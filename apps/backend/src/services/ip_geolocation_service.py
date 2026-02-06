"""
IP Geolocation Service

Provides IP address geolocation and reputation checking.
Uses ip-api.com (free tier: 45 requests/minute) for geolocation.

For production, consider:
- MaxMind GeoIP2 (local database, fastest)
- ipinfo.io (reliable, good free tier)
- ipdata.co (includes threat data)
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class GeoLocation:
    """Geolocation data for an IP address"""

    ip_address: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    is_vpn: bool = False
    is_proxy: bool = False
    is_tor: bool = False
    is_datacenter: bool = False
    reputation_score: int = 50  # 0-100, higher is better


@dataclass
class DeviceFingerprint:
    """Device fingerprint from user agent and other signals"""

    fingerprint: str
    browser: Optional[str] = None
    os: Optional[str] = None
    device_type: Optional[str] = None  # desktop, mobile, tablet
    is_bot: bool = False


class IPGeolocationService:
    """
    Service for IP geolocation and reputation checking.

    Uses free ip-api.com for geolocation.
    Caches results in database to reduce API calls.
    """

    # Known VPN/Datacenter ASNs (partial list)
    KNOWN_VPN_ASNS = {
        "AS14618",  # Amazon AWS
        "AS15169",  # Google Cloud
        "AS8075",  # Microsoft Azure
        "AS16509",  # Amazon
        "AS14061",  # DigitalOcean
        "AS63949",  # Linode
        "AS20473",  # Vultr
        "AS13335",  # Cloudflare
        "AS32934",  # Facebook
    }

    # Known TOR exit node IPs (should be updated periodically)
    # In production, use https://check.torproject.org/exit-addresses

    def __init__(self, db: AsyncSession, cache_ttl_days: int = 7):
        self.db = db
        self.cache_ttl_days = cache_ttl_days
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def get_geolocation(self, ip_address: str) -> GeoLocation:
        """
        Get geolocation for an IP address.
        Checks cache first, then calls external API.
        """
        # Skip localhost/private IPs
        if self._is_private_ip(ip_address):
            return GeoLocation(
                ip_address=ip_address,
                country="Local",
                city="Private Network",
                reputation_score=100,
            )

        # Check cache first
        cached = await self._get_cached_location(ip_address)
        if cached:
            return cached

        # Fetch from API
        location = await self._fetch_geolocation(ip_address)

        # Cache the result
        await self._cache_location(location)

        return location

    def _is_private_ip(self, ip_address: str) -> bool:
        """Check if IP is private/local"""
        if not ip_address:
            return True

        private_prefixes = [
            "127.",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
            "192.168.",
            "::1",
            "fe80:",
            "fc00:",
            "fd00:",
        ]
        return any(ip_address.startswith(prefix) for prefix in private_prefixes)

    async def _get_cached_location(self, ip_address: str) -> Optional[GeoLocation]:
        """Get cached geolocation from database"""
        try:
            query = text(
                """
                SELECT
                    ip_address, reputation_score, is_vpn, is_proxy, is_tor,
                    is_datacenter, country_code, threat_types
                FROM security.ip_reputation_cache
                WHERE ip_address = :ip_address
                  AND expires_at > NOW()
            """
            )
            result = await self.db.execute(query, {"ip_address": ip_address})
            row = result.fetchone()

            if row:
                return GeoLocation(
                    ip_address=row.ip_address,
                    country_code=row.country_code,
                    is_vpn=row.is_vpn,
                    is_proxy=row.is_proxy,
                    is_tor=row.is_tor,
                    is_datacenter=row.is_datacenter,
                    reputation_score=row.reputation_score,
                )
            return None
        except Exception as e:
            logger.warning(f"Cache lookup failed for {ip_address}: {e}")
            return None

    async def _cache_location(self, location: GeoLocation) -> None:
        """Cache geolocation in database"""
        try:
            query = text(
                """
                INSERT INTO security.ip_reputation_cache
                (ip_address, reputation_score, is_vpn, is_proxy, is_tor, is_datacenter, country_code)
                VALUES (:ip_address, :reputation_score, :is_vpn, :is_proxy, :is_tor, :is_datacenter, :country_code)
                ON CONFLICT (ip_address) DO UPDATE SET
                    reputation_score = EXCLUDED.reputation_score,
                    is_vpn = EXCLUDED.is_vpn,
                    is_proxy = EXCLUDED.is_proxy,
                    is_tor = EXCLUDED.is_tor,
                    is_datacenter = EXCLUDED.is_datacenter,
                    country_code = EXCLUDED.country_code,
                    last_checked = NOW(),
                    expires_at = NOW() + INTERVAL '7 days'
            """
            )
            await self.db.execute(
                query,
                {
                    "ip_address": location.ip_address,
                    "reputation_score": location.reputation_score,
                    "is_vpn": location.is_vpn,
                    "is_proxy": location.is_proxy,
                    "is_tor": location.is_tor,
                    "is_datacenter": location.is_datacenter,
                    "country_code": location.country_code,
                },
            )
            await self.db.commit()
        except Exception as e:
            logger.warning(f"Cache save failed for {location.ip_address}: {e}")
            await self.db.rollback()

    async def _fetch_geolocation(self, ip_address: str) -> GeoLocation:
        """Fetch geolocation from ip-api.com (free tier)"""
        try:
            client = await self._get_http_client()
            # ip-api.com fields: status,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,proxy,hosting
            url = f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,proxy,hosting"

            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()

                if data.get("status") == "success":
                    # Check if it's a datacenter/hosting IP
                    is_datacenter = data.get("hosting", False)
                    is_proxy = data.get("proxy", False)

                    # Check ASN for known VPN providers
                    asn = data.get("as", "").split()[0] if data.get("as") else ""
                    is_vpn = asn in self.KNOWN_VPN_ASNS or is_datacenter

                    # Calculate reputation score
                    reputation = 100
                    if is_proxy:
                        reputation -= 30
                    if is_vpn:
                        reputation -= 20
                    if is_datacenter:
                        reputation -= 15

                    return GeoLocation(
                        ip_address=ip_address,
                        country=data.get("country"),
                        country_code=data.get("countryCode"),
                        region=data.get("regionName"),
                        city=data.get("city"),
                        latitude=data.get("lat"),
                        longitude=data.get("lon"),
                        timezone=data.get("timezone"),
                        isp=data.get("isp"),
                        is_vpn=is_vpn,
                        is_proxy=is_proxy,
                        is_datacenter=is_datacenter,
                        reputation_score=max(0, reputation),
                    )

            logger.warning(f"Geolocation lookup failed for {ip_address}: {response.status_code}")

        except asyncio.TimeoutError:
            logger.warning(f"Geolocation timeout for {ip_address}")
        except Exception as e:
            logger.error(f"Geolocation error for {ip_address}: {e}")

        # Return basic location on failure
        return GeoLocation(ip_address=ip_address, reputation_score=50)

    def generate_device_fingerprint(
        self, user_agent: str, ip_address: str = ""
    ) -> DeviceFingerprint:
        """
        Generate a device fingerprint from user agent.
        In production, use more signals (screen resolution, fonts, etc.)
        """
        if not user_agent:
            return DeviceFingerprint(fingerprint="unknown", is_bot=False)

        # Simple fingerprint from user agent hash
        fingerprint = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

        # Parse user agent for device info
        ua_lower = user_agent.lower()

        # Detect browser
        browser = "Unknown"
        if "chrome" in ua_lower and "edg" not in ua_lower:
            browser = "Chrome"
        elif "firefox" in ua_lower:
            browser = "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            browser = "Safari"
        elif "edg" in ua_lower:
            browser = "Edge"
        elif "opera" in ua_lower or "opr" in ua_lower:
            browser = "Opera"

        # Detect OS
        os_name = "Unknown"
        if "windows" in ua_lower:
            os_name = "Windows"
        elif "mac os" in ua_lower or "macos" in ua_lower:
            os_name = "macOS"
        elif "linux" in ua_lower and "android" not in ua_lower:
            os_name = "Linux"
        elif "android" in ua_lower:
            os_name = "Android"
        elif "iphone" in ua_lower or "ipad" in ua_lower:
            os_name = "iOS"

        # Detect device type
        device_type = "desktop"
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            device_type = "mobile"
        elif "ipad" in ua_lower or "tablet" in ua_lower:
            device_type = "tablet"

        # Detect bots
        bot_indicators = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "curl",
            "wget",
            "python-requests",
        ]
        is_bot = any(indicator in ua_lower for indicator in bot_indicators)

        return DeviceFingerprint(
            fingerprint=fingerprint,
            browser=browser,
            os=os_name,
            device_type=device_type,
            is_bot=is_bot,
        )

    async def is_ip_known_for_user(self, user_id: str, ip_address: str) -> bool:
        """Check if this IP has been used by this user before"""
        try:
            query = text(
                """
                SELECT 1 FROM security.known_user_ips
                WHERE user_id = CAST(:user_id AS uuid)
                  AND ip_address = :ip_address
            """
            )
            result = await self.db.execute(query, {"user_id": user_id, "ip_address": ip_address})
            return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking known IP: {e}")
            return False

    async def register_user_ip(
        self,
        user_id: str,
        ip_address: str,
        country: Optional[str] = None,
        city: Optional[str] = None,
    ) -> bool:
        """Register an IP as known for a user (or update last_seen)"""
        try:
            query = text(
                """
                INSERT INTO security.known_user_ips
                (user_id, ip_address, country, city, first_seen, last_seen, login_count)
                VALUES (CAST(:user_id AS uuid), :ip_address, :country, :city, NOW(), NOW(), 1)
                ON CONFLICT (user_id, ip_address) DO UPDATE SET
                    last_seen = NOW(),
                    login_count = security.known_user_ips.login_count + 1
            """
            )
            await self.db.execute(
                query,
                {
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "country": country,
                    "city": city,
                },
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error registering user IP: {e}")
            await self.db.rollback()
            return False

    async def count_new_ips_24h(self, user_id: str) -> int:
        """Count how many new IPs the user logged in from in last 24 hours"""
        try:
            query = text(
                """
                SELECT COUNT(DISTINCT ip_address)
                FROM security.login_history
                WHERE user_id = CAST(:user_id AS uuid)
                  AND is_new_ip = TRUE
                  AND login_at > NOW() - INTERVAL '24 hours'
            """
            )
            result = await self.db.execute(query, {"user_id": user_id})
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting new IPs: {e}")
            return 0

    async def count_accounts_from_ip_1h(self, ip_address: str) -> int:
        """Count how many different accounts logged in from this IP in last hour"""
        try:
            query = text(
                """
                SELECT COUNT(DISTINCT user_id)
                FROM security.login_history
                WHERE ip_address = :ip_address
                  AND login_at > NOW() - INTERVAL '1 hour'
            """
            )
            result = await self.db.execute(query, {"ip_address": ip_address})
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting accounts from IP: {e}")
            return 0

    async def get_last_login(self, user_id: str) -> Optional[dict]:
        """Get user's last login info for geo-impossible detection"""
        try:
            query = text(
                """
                SELECT ip_address, city, country, latitude, longitude, login_at
                FROM security.login_history
                WHERE user_id = CAST(:user_id AS uuid)
                ORDER BY login_at DESC
                LIMIT 1
            """
            )
            result = await self.db.execute(query, {"user_id": user_id})
            row = result.fetchone()

            if row:
                return {
                    "ip_address": row.ip_address,
                    "city": row.city,
                    "country": row.country,
                    "latitude": float(row.latitude) if row.latitude else None,
                    "longitude": (float(row.longitude) if row.longitude else None),
                    "login_at": row.login_at,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting last login: {e}")
            return None

    def calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math

        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def is_geo_impossible(
        self,
        distance_km: float,
        minutes_between: float,
        max_speed_kmh: float = 900,  # Max commercial flight speed
    ) -> bool:
        """
        Check if travel between two locations is physically impossible.
        Default max speed is 900 km/h (commercial jet).
        """
        if minutes_between <= 0:
            return False

        hours_between = minutes_between / 60
        required_speed = distance_km / hours_between

        # Add buffer for airport transit time (2 hours minimum for flights)
        if distance_km > 500:  # Likely requires flying
            hours_between -= 2  # Account for airport time
            if hours_between <= 0:
                return True
            required_speed = distance_km / hours_between

        return required_speed > max_speed_kmh
