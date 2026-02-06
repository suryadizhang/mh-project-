"""
VPS Security Monitoring API Router
==================================

Provides endpoints for monitoring VPS security status including:
- Fail2ban banned IPs and jail status
- Firewalld rules
- Attack logs and statistics
- Manual unban functionality

Requires SUPER_ADMIN role for all operations.

VPS Connection:
- Uses SSH key authentication to VPS at 108.175.12.154
- Parses fail2ban-client and firewall-cmd output
- Returns structured JSON responses

Related Files:
- /etc/fail2ban/jail.local - Jail configurations
- /etc/fail2ban/filter.d/ - Filter definitions
- configs/fail2ban/ - Local copies of filter files

Author: My Hibachi Dev Team
Created: January 2025
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.deps import get_current_admin_user
from core.auth import require_roles
from db.models.identity import User
from utils.auth import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vps-security", tags=["VPS Security"])


# ==============================================================================
# Configuration
# ==============================================================================

VPS_HOST = os.getenv("VPS_HOST", "108.175.12.154")
VPS_USER = os.getenv("VPS_USER", "root")
SSH_TIMEOUT = 30  # seconds


# ==============================================================================
# Pydantic Schemas
# ==============================================================================


class BannedIP(BaseModel):
    """Details of a banned IP address."""

    ip: str
    jail: str
    ban_time: Optional[str] = None
    country: Optional[str] = None
    organization: Optional[str] = None


class JailStatus(BaseModel):
    """Status of a fail2ban jail."""

    name: str
    enabled: bool
    currently_banned: int
    total_banned: int
    filter_path: Optional[str] = None


class FirewallRule(BaseModel):
    """A firewall rule entry."""

    family: str = "ipv4"
    rule: str
    source_ip: Optional[str] = None


class SecurityStatus(BaseModel):
    """Overall VPS security status."""

    fail2ban_running: bool
    firewalld_running: bool
    active_jails: int
    total_banned_ips: int
    last_checked: str


class AttackLogEntry(BaseModel):
    """An entry from the attack/ban log."""

    timestamp: str
    jail: str
    action: str  # "Ban" or "Unban"
    ip: str
    message: Optional[str] = None


class SecurityStats(BaseModel):
    """Security statistics summary."""

    total_bans_24h: int = 0
    total_bans_7d: int = 0
    most_attacked_jail: Optional[str] = None
    top_attacker_ips: list[str] = Field(default_factory=list)
    banned_countries: list[str] = Field(default_factory=list)


class SecurityReportResponse(BaseModel):
    """Full security report."""

    status: SecurityStatus
    jails: list[JailStatus]
    banned_ips: list[BannedIP]
    recent_attacks: list[AttackLogEntry]
    stats: SecurityStats
    generated_at: str


class UnbanRequest(BaseModel):
    """Request to unban an IP."""

    ip: str
    jail: Optional[str] = None  # If None, unban from all jails


class UnbanResponse(BaseModel):
    """Response after unbanning an IP."""

    success: bool
    ip: str
    unbanned_from: list[str]
    message: str


# ==============================================================================
# SSH Helper Functions
# ==============================================================================


async def run_ssh_command(command: str) -> tuple[bool, str, str]:
    """
    Run a command on VPS via SSH.

    Returns:
        Tuple of (success, stdout, stderr)
    """
    ssh_cmd = (
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {VPS_USER}@{VPS_HOST} '{command}'"
    )

    try:
        process = await asyncio.create_subprocess_shell(
            ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=SSH_TIMEOUT)

        return (
            process.returncode == 0,
            stdout.decode("utf-8", errors="replace").strip(),
            stderr.decode("utf-8", errors="replace").strip(),
        )
    except asyncio.TimeoutError:
        logger.error(f"SSH command timed out: {command[:50]}...")
        return False, "", "SSH command timed out"
    except Exception as e:
        logger.error(f"SSH command failed: {e}")
        return False, "", str(e)


def parse_jail_status(output: str) -> dict:
    """Parse fail2ban-client jail status output."""
    result = {
        "currently_banned": 0,
        "total_banned": 0,
        "banned_ips": [],
    }

    for line in output.split("\n"):
        line = line.strip()
        if "Currently banned:" in line:
            result["currently_banned"] = int(line.split(":")[-1].strip())
        elif "Total banned:" in line:
            result["total_banned"] = int(line.split(":")[-1].strip())
        elif "Banned IP list:" in line:
            ips_str = line.split(":")[-1].strip()
            if ips_str:
                result["banned_ips"] = ips_str.split()

    return result


def parse_firewalld_rich_rules(output: str) -> list[FirewallRule]:
    """Parse firewall-cmd --list-rich-rules output."""
    rules = []

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Extract source IP if present
        source_match = re.search(r'source address="([^"]+)"', line)
        source_ip = source_match.group(1) if source_match else None

        rules.append(
            FirewallRule(
                family="ipv4",
                rule=line,
                source_ip=source_ip,
            )
        )

    return rules


# ==============================================================================
# API Endpoints
# ==============================================================================


@router.get("/status", response_model=SecurityStatus)
async def get_security_status(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get overall VPS security status.

    Checks fail2ban and firewalld service status.
    """
    # Check fail2ban status
    success_f2b, stdout_f2b, _ = await run_ssh_command("systemctl is-active fail2ban")
    fail2ban_running = success_f2b and "active" in stdout_f2b

    # Check firewalld status
    success_fw, stdout_fw, _ = await run_ssh_command("systemctl is-active firewalld")
    firewalld_running = success_fw and "active" in stdout_fw

    # Get jail count
    success_jails, stdout_jails, _ = await run_ssh_command("fail2ban-client status")
    active_jails = 0
    if success_jails:
        match = re.search(r"Number of jail:\s*(\d+)", stdout_jails)
        if match:
            active_jails = int(match.group(1))

    # Count total banned IPs across all jails
    total_banned = 0
    if success_jails:
        # Extract jail names
        jail_match = re.search(r"Jail list:\s*(.+)", stdout_jails)
        if jail_match:
            jail_names = [j.strip() for j in jail_match.group(1).split(",")]
            for jail in jail_names:
                success, stdout, _ = await run_ssh_command(f"fail2ban-client status {jail}")
                if success:
                    parsed = parse_jail_status(stdout)
                    total_banned += parsed["currently_banned"]

    return SecurityStatus(
        fail2ban_running=fail2ban_running,
        firewalld_running=firewalld_running,
        active_jails=active_jails,
        total_banned_ips=total_banned,
        last_checked=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


@router.get("/jails", response_model=list[JailStatus])
async def get_jail_status(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get status of all fail2ban jails.
    """
    jails = []

    # Get jail list
    success, stdout, _ = await run_ssh_command("fail2ban-client status")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to fail2ban",
        )

    # Extract jail names
    jail_match = re.search(r"Jail list:\s*(.+)", stdout)
    if not jail_match:
        return jails

    jail_names = [j.strip() for j in jail_match.group(1).split(",")]

    for jail_name in jail_names:
        success, stdout, _ = await run_ssh_command(f"fail2ban-client status {jail_name}")
        if success:
            parsed = parse_jail_status(stdout)
            jails.append(
                JailStatus(
                    name=jail_name,
                    enabled=True,
                    currently_banned=parsed["currently_banned"],
                    total_banned=parsed["total_banned"],
                    filter_path=f"/etc/fail2ban/filter.d/{jail_name}.conf",
                )
            )

    return jails


@router.get("/banned-ips", response_model=list[BannedIP])
async def get_banned_ips(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get all currently banned IPs across all jails.
    """
    banned_ips = []

    # Get jail list
    success, stdout, _ = await run_ssh_command("fail2ban-client status")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to fail2ban",
        )

    # Extract jail names
    jail_match = re.search(r"Jail list:\s*(.+)", stdout)
    if not jail_match:
        return banned_ips

    jail_names = [j.strip() for j in jail_match.group(1).split(",")]

    for jail_name in jail_names:
        success, stdout, _ = await run_ssh_command(f"fail2ban-client status {jail_name}")
        if success:
            parsed = parse_jail_status(stdout)
            for ip in parsed["banned_ips"]:
                banned_ips.append(
                    BannedIP(
                        ip=ip,
                        jail=jail_name,
                    )
                )

    return banned_ips


@router.get("/firewall-rules", response_model=list[FirewallRule])
async def get_firewall_rules(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get current firewalld rich rules (blocking rules).
    """
    success, stdout, _ = await run_ssh_command("firewall-cmd --list-rich-rules")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to query firewall",
        )

    return parse_firewalld_rich_rules(stdout)


@router.get("/attack-log", response_model=list[AttackLogEntry])
async def get_attack_log(
    limit: int = 50,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get recent attack/ban log entries.
    """
    entries = []

    # Get recent bans from fail2ban log
    success, stdout, _ = await run_ssh_command(
        f"grep -E 'Ban|Unban' /var/log/fail2ban.log | tail -n {limit}"
    )

    if success and stdout:
        for line in stdout.split("\n"):
            if not line.strip():
                continue

            # Parse log line format: 2025-01-26 02:34:26,123 fail2ban.actions [1234]: NOTICE [sshd] Ban 1.2.3.4
            match = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .+\[(\w+)\] (Ban|Unban) (\d+\.\d+\.\d+\.\d+)",
                line,
            )
            if match:
                entries.append(
                    AttackLogEntry(
                        timestamp=match.group(1),
                        jail=match.group(2),
                        action=match.group(3),
                        ip=match.group(4),
                        message=line,
                    )
                )

    return entries


@router.get("/stats", response_model=SecurityStats)
async def get_security_stats(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get security statistics summary.
    """
    stats = SecurityStats()

    # Count bans in last 24 hours
    success_24h, stdout_24h, _ = await run_ssh_command(
        "grep 'Ban' /var/log/fail2ban.log | grep \"$(date +'%Y-%m-%d')\" | wc -l"
    )
    if success_24h:
        try:
            stats.total_bans_24h = int(stdout_24h.strip())
        except ValueError:
            pass

    # Count bans in last 7 days (approximate)
    success_7d, stdout_7d, _ = await run_ssh_command("grep 'Ban' /var/log/fail2ban.log | wc -l")
    if success_7d:
        try:
            stats.total_bans_7d = int(stdout_7d.strip())
        except ValueError:
            pass

    # Find most attacked jail
    success_jails, stdout_jails, _ = await run_ssh_command(
        "grep 'Ban' /var/log/fail2ban.log | grep -oP '\\[\\K[^\\]]+' | sort | uniq -c | sort -rn | head -1"
    )
    if success_jails and stdout_jails:
        parts = stdout_jails.strip().split()
        if len(parts) >= 2:
            stats.most_attacked_jail = parts[1]

    # Get top attacker IPs
    success_ips, stdout_ips, _ = await run_ssh_command(
        "grep 'Ban' /var/log/fail2ban.log | grep -oP '\\d+\\.\\d+\\.\\d+\\.\\d+' | sort | uniq -c | sort -rn | head -5"
    )
    if success_ips and stdout_ips:
        for line in stdout_ips.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                stats.top_attacker_ips.append(parts[1])

    return stats


@router.post("/unban", response_model=UnbanResponse)
async def unban_ip(
    request: UnbanRequest,
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Manually unban an IP address.

    Requires SUPER_ADMIN role.
    """
    unbanned_from = []

    if request.jail:
        # Unban from specific jail
        success, _, stderr = await run_ssh_command(
            f"fail2ban-client set {request.jail} unbanip {request.ip}"
        )
        if success:
            unbanned_from.append(request.jail)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to unban IP: {stderr}",
            )
    else:
        # Get all jails and unban from each
        success, stdout, _ = await run_ssh_command("fail2ban-client status")
        if success:
            jail_match = re.search(r"Jail list:\s*(.+)", stdout)
            if jail_match:
                jail_names = [j.strip() for j in jail_match.group(1).split(",")]
                for jail_name in jail_names:
                    success, _, _ = await run_ssh_command(
                        f"fail2ban-client set {jail_name} unbanip {request.ip}"
                    )
                    if success:
                        unbanned_from.append(jail_name)

    logger.info(f"User {current_user.email} unbanned IP {request.ip} from jails: {unbanned_from}")

    return UnbanResponse(
        success=len(unbanned_from) > 0,
        ip=request.ip,
        unbanned_from=unbanned_from,
        message=f"IP {request.ip} unbanned from {len(unbanned_from)} jail(s)",
    )


@router.get("/report", response_model=SecurityReportResponse)
async def get_security_report(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Generate a full security report.

    Combines status, jails, banned IPs, attack log, and statistics.
    """
    # Gather all data
    security_status = await get_security_status(current_user)
    jails = await get_jail_status(current_user)
    banned_ips = await get_banned_ips(current_user)
    recent_attacks = await get_attack_log(limit=20, current_user=current_user)
    stats = await get_security_stats(current_user)

    return SecurityReportResponse(
        status=security_status,
        jails=jails,
        banned_ips=banned_ips,
        recent_attacks=recent_attacks,
        stats=stats,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


# ==============================================================================
# Known Attackers Information (from security audit)
# ==============================================================================


@router.get("/known-attackers")
async def get_known_attackers(
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get information about known attackers identified during security audits.
    """
    return {
        "last_audit": "2025-01-26",
        "attackers": [
            {
                "ip": "159.223.4.35",
                "organization": "DigitalOcean, LLC",
                "country": "USA",
                "attack_type": "SSH brute force",
                "first_seen": "2025-01-26",
                "status": "banned",
            },
            {
                "ip": "159.223.43.21",
                "organization": "DigitalOcean, LLC",
                "country": "USA",
                "attack_type": "SSH brute force",
                "first_seen": "2025-01-26",
                "status": "banned",
            },
            {
                "ip": "2.57.122.208",
                "organization": "TECHOFF SRV LIMITED",
                "country": "United Kingdom",
                "attack_type": "SSH brute force",
                "first_seen": "2025-01-26",
                "status": "banned",
            },
            {
                "ip": "213.209.159.159",
                "organization": "Feo Prest SRL",
                "country": "Romania",
                "attack_type": "SSH brute force",
                "first_seen": "2025-01-26",
                "status": "banned",
            },
        ],
        "note": "These IPs are blocked via fail2ban with 7-day bans. Recidive jail will escalate to 30-day bans for repeat offenders.",
    }
