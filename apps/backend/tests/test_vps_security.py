"""
Unit Tests for VPS Security Router
===================================

Tests the /api/admin/vps-security/* endpoints that monitor
VPS security via fail2ban and firewalld.

These tests mock the SSH command execution since we can't
actually connect to the VPS during unit tests.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.deps import AdminUser, get_current_admin_user
from core.auth import get_current_active_user
from core.auth.middleware import AuthenticatedUser
from main import app

# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture(autouse=True)
def set_test_environment():
    """Set required environment variables for tests."""
    # Set encryption key for unban endpoint
    os.environ["FIELD_ENCRYPTION_KEY"] = "test-encryption-key-32-bytes!!"
    yield
    # Cleanup
    if "FIELD_ENCRYPTION_KEY" in os.environ:
        del os.environ["FIELD_ENCRYPTION_KEY"]


def get_mock_admin_user():
    """Return a mock AdminUser for dependency override."""
    return AdminUser(
        id=123,
        email="admin@myhibachi.com",
        role="ADMIN",
        full_name="Test Admin",
    )


def get_mock_super_admin_user():
    """Return a mock SuperAdmin user for dependency override."""
    return AdminUser(
        id=456,
        email="superadmin@myhibachi.com",
        role="SUPER_ADMIN",
        full_name="Super Admin",
    )


def get_mock_authenticated_super_admin():
    """Return a mock AuthenticatedUser for require_roles tests.

    The unban endpoint uses require_roles([UserRole.SUPER_ADMIN]) which
    internally depends on get_current_active_user (returns AuthenticatedUser),
    NOT get_current_admin_user (returns AdminUser).
    """
    # Create a mock StationUser-like object
    mock_user = MagicMock()
    mock_user.id = 456
    mock_user.role = "SUPER_ADMIN"
    mock_user.status = MagicMock()
    mock_user.status.value = "active"  # For status check

    # Create a mock UserSession
    mock_session = MagicMock()

    # Create AuthenticatedUser mock
    mock_auth_user = MagicMock(spec=AuthenticatedUser)
    mock_auth_user.user = mock_user
    mock_auth_user.session = mock_session
    mock_auth_user.permissions = set()
    mock_auth_user.id = 456
    mock_auth_user.role = MagicMock()
    mock_auth_user.role.value = "SUPER_ADMIN"
    mock_auth_user.email = "testadmin@example.com"  # Required for unban logging

    return mock_auth_user


@pytest.fixture
def admin_client():
    """
    Provides an AsyncClient with admin authentication mocked.
    Uses dependency override to bypass real token validation.
    """
    app.dependency_overrides[get_current_admin_user] = get_mock_admin_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def super_admin_client():
    """
    Provides an AsyncClient with super_admin authentication mocked.
    Uses dependency override to bypass real token validation.

    NOTE: Overrides BOTH get_current_admin_user (for most endpoints)
    AND get_current_active_user (for require_roles-protected endpoints like unban).
    """
    app.dependency_overrides[get_current_admin_user] = get_mock_super_admin_user
    app.dependency_overrides[
        get_current_active_user
    ] = get_mock_authenticated_super_admin
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_ssh_success():
    """Mock successful SSH command execution."""

    async def mock_run_ssh(*args, **kwargs):
        command = args[0] if args else kwargs.get("command", "")

        # Mock responses for different commands
        if "systemctl is-active fail2ban" in command:
            return (True, "active", "")
        elif "systemctl is-active firewalld" in command:
            return (True, "active", "")
        elif "fail2ban-client status" in command and "status " not in command:
            return (
                True,
                "Status\n|- Number of jail:\t3\n`- Jail list:\tsshd, api-abuse, recidive",
                "",
            )
        elif "fail2ban-client status sshd" in command:
            return (
                True,
                """Status for the jail: sshd
|- Filter
|  |- Currently failed:\t5
|  |- Total failed:\t1234
|  `- File list:\t/var/log/secure
`- Actions
   |- Currently banned:\t3
   |- Total banned:\t150
   `- Banned IP list:\t192.168.1.100 10.0.0.50 172.16.0.25""",
                "",
            )
        elif "fail2ban-client status api-abuse" in command:
            return (
                True,
                """Status for the jail: api-abuse
|- Filter
|  |- Currently failed:\t2
|  |- Total failed:\t50
|  `- File list:\t/var/log/nginx/error.log
`- Actions
   |- Currently banned:\t1
   |- Total banned:\t10
   `- Banned IP list:\t203.0.113.5""",
                "",
            )
        elif "fail2ban-client status recidive" in command:
            return (
                True,
                """Status for the jail: recidive
|- Filter
|  |- Currently failed:\t0
|  |- Total failed:\t5
|  `- File list:\t/var/log/fail2ban.log
`- Actions
   |- Currently banned:\t0
   |- Total banned:\t2
   `- Banned IP list:""",
                "",
            )
        elif "firewall-cmd --list-rich-rules" in command:
            return (
                True,
                """rule family="ipv4" source address="192.168.1.100" drop
rule family="ipv4" source address="10.0.0.50" reject""",
                "",
            )
        elif "grep 'Ban\\|Unban' /var/log/fail2ban.log" in command:
            return (
                True,
                """2025-01-26 02:34:26,123 fail2ban.actions [1234]: NOTICE [sshd] Ban 192.168.1.100
2025-01-26 02:35:00,456 fail2ban.actions [1234]: NOTICE [sshd] Ban 10.0.0.50
2025-01-26 02:40:15,789 fail2ban.actions [1234]: NOTICE [api-abuse] Ban 203.0.113.5""",
                "",
            )
        elif "grep 'Ban' /var/log/fail2ban.log | grep" in command and "date" in command:
            return (True, "42", "")
        elif "grep 'Ban' /var/log/fail2ban.log | wc -l" in command:
            return (True, "156", "")
        elif (
            "grep 'Ban' /var/log/fail2ban.log | grep -oP" in command
            and "sort | uniq -c" in command
        ):
            return (True, "   75 sshd", "")
        elif "head -5" in command:
            return (True, "   30 192.168.1.100\n   25 10.0.0.50\n   15 203.0.113.5", "")
        elif "unbanip" in command:
            return (True, "", "")
        else:
            return (True, "", "")

    return mock_run_ssh


@pytest.fixture
def mock_ssh_failure():
    """Mock failed SSH command execution."""

    async def mock_run_ssh(*args, **kwargs):
        return (False, "", "Connection refused")

    return mock_run_ssh


# ==============================================================================
# GET /status Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_security_status_success(admin_client, mock_ssh_success):
    """Test successful security status retrieval."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/status")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "fail2ban_running" in data
            assert "firewalld_running" in data
            assert "active_jails" in data
            assert "total_banned_ips" in data
            assert "last_checked" in data


@pytest.mark.asyncio
async def test_get_security_status_unauthorized():
    """Test security status without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/status")

        # Should return 401 or 403
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_security_status_ssh_failure(admin_client, mock_ssh_failure):
    """Test security status when SSH commands fail."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_failure):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/status")

            # Should still return 200 with default/error values
            assert response.status_code == 200
            data = response.json()

            # Services should show as inactive when SSH fails
            assert data["fail2ban_running"] is False
            assert data["firewalld_running"] is False


# ==============================================================================
# GET /jails Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_jail_status_success(admin_client, mock_ssh_success):
    """Test successful jail status retrieval."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/jails")

            assert response.status_code == 200
            data = response.json()

            # Should return list of jails
            assert isinstance(data, list)
            if len(data) > 0:
                jail = data[0]
                assert "name" in jail
                assert "enabled" in jail
                assert "currently_banned" in jail
                assert "total_banned" in jail


@pytest.mark.asyncio
async def test_get_jail_status_unauthorized():
    """Test jail status without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/jails")

        assert response.status_code in [401, 403]


# ==============================================================================
# GET /banned-ips Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_banned_ips_success(admin_client, mock_ssh_success):
    """Test successful banned IPs retrieval."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/banned-ips")

            assert response.status_code == 200
            data = response.json()

            # Should return list of banned IPs
            assert isinstance(data, list)
            if len(data) > 0:
                banned_ip = data[0]
                assert "ip" in banned_ip
                assert "jail" in banned_ip


@pytest.mark.asyncio
async def test_get_banned_ips_unauthorized():
    """Test banned IPs without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/banned-ips")

        assert response.status_code in [401, 403]


# ==============================================================================
# GET /firewall-rules Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_firewall_rules_success(admin_client, mock_ssh_success):
    """Test successful firewall rules retrieval."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/firewall-rules")

            assert response.status_code == 200
            data = response.json()

            # Should return list of firewall rules
            assert isinstance(data, list)
            if len(data) > 0:
                rule = data[0]
                assert "rule" in rule


@pytest.mark.asyncio
async def test_get_firewall_rules_unauthorized():
    """Test firewall rules without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/firewall-rules")

        assert response.status_code in [401, 403]


# ==============================================================================
# GET /attack-log Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_attack_log_success(admin_client, mock_ssh_success):
    """Test successful attack log retrieval."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/attack-log")

            assert response.status_code == 200
            data = response.json()

            # Should return list of attack log entries
            assert isinstance(data, list)
            if len(data) > 0:
                entry = data[0]
                assert "timestamp" in entry
                assert "jail" in entry
                assert "action" in entry
                assert "ip" in entry


@pytest.mark.asyncio
async def test_get_attack_log_with_limit(admin_client, mock_ssh_success):
    """Test attack log with custom limit."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/attack-log?limit=10")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_attack_log_unauthorized():
    """Test attack log without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/attack-log")

        assert response.status_code in [401, 403]


# ==============================================================================
# GET /stats Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_security_stats_success(admin_client, mock_ssh_success):
    """Test successful security stats retrieval."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/stats")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "total_bans_24h" in data
            assert "total_bans_7d" in data
            assert "most_attacked_jail" in data
            assert "top_attacker_ips" in data


@pytest.mark.asyncio
async def test_get_security_stats_unauthorized():
    """Test security stats without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/stats")

        assert response.status_code in [401, 403]


# ==============================================================================
# POST /unban Tests (Requires SUPER_ADMIN)
# ==============================================================================


@pytest.mark.asyncio
async def test_unban_ip_success(super_admin_client, mock_ssh_success):
    """Test successful IP unban (super admin only)."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/admin/vps-security/unban",
                json={"ip": "192.168.1.100", "jail": "sshd"},
            )

            assert response.status_code == 200
            data = response.json()

            assert "success" in data
            assert "ip" in data
            assert "unbanned_from" in data
            assert "message" in data


@pytest.mark.asyncio
async def test_unban_ip_all_jails(super_admin_client, mock_ssh_success):
    """Test unban IP from all jails."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/admin/vps-security/unban",
                json={"ip": "192.168.1.100"},  # No jail specified = all jails
            )

            assert response.status_code == 200
            data = response.json()
            assert "unbanned_from" in data


@pytest.mark.asyncio
async def test_unban_ip_admin_forbidden(admin_client, mock_ssh_success):
    """Test that regular admin cannot unban IPs."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/admin/vps-security/unban",
                json={"ip": "192.168.1.100", "jail": "sshd"},
            )

            # Regular admin should be forbidden from unban
            assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_unban_ip_unauthorized():
    """Test unban without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/admin/vps-security/unban",
            json={"ip": "192.168.1.100", "jail": "sshd"},
        )

        assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_unban_ip_invalid_request(super_admin_client, mock_ssh_success):
    """Test unban with invalid IP format."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/admin/vps-security/unban", json={}  # Missing required 'ip' field
            )

            assert response.status_code == 422  # Validation error


# ==============================================================================
# GET /report Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_security_report_success(admin_client, mock_ssh_success):
    """Test successful security report retrieval."""
    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/report")

            assert response.status_code == 200
            data = response.json()

            # Verify comprehensive report structure
            assert "status" in data
            assert "jails" in data
            assert "banned_ips" in data
            assert "recent_attacks" in data
            assert "stats" in data
            assert "generated_at" in data


@pytest.mark.asyncio
async def test_get_security_report_unauthorized():
    """Test security report without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/report")

        assert response.status_code in [401, 403]


# ==============================================================================
# GET /known-attackers Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_known_attackers_success(admin_client):
    """Test successful known attackers retrieval."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/known-attackers")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "last_audit" in data
        assert "attackers" in data
        assert "note" in data

        # Verify attackers list structure
        assert isinstance(data["attackers"], list)
        if len(data["attackers"]) > 0:
            attacker = data["attackers"][0]
            assert "ip" in attacker
            assert "organization" in attacker
            assert "country" in attacker
            assert "attack_type" in attacker
            assert "status" in attacker


@pytest.mark.asyncio
async def test_get_known_attackers_unauthorized():
    """Test known attackers without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/admin/vps-security/known-attackers")

        assert response.status_code in [401, 403]


# ==============================================================================
# Edge Cases and Error Handling
# ==============================================================================


@pytest.mark.asyncio
async def test_ssh_timeout_handling(admin_client):
    """Test handling of SSH command timeout."""

    async def mock_timeout(*args, **kwargs):
        import asyncio

        await asyncio.sleep(0.01)  # Small delay
        return (False, "", "Connection timed out")

    with patch("routers.v1.vps_security.run_ssh_command", mock_timeout):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/status")

            # Should handle timeout gracefully
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_malformed_ssh_output(admin_client):
    """Test handling of malformed SSH command output."""

    async def mock_malformed(*args, **kwargs):
        return (True, "malformed output that doesn't match expected format", "")

    with patch("routers.v1.vps_security.run_ssh_command", mock_malformed):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/jails")

            # Should handle gracefully without crashing
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_empty_jail_list(admin_client):
    """Test handling of empty jail list."""

    async def mock_empty_jails(*args, **kwargs):
        command = args[0] if args else ""
        if "fail2ban-client status" in command:
            return (True, "Status\n|- Number of jail:\t0\n`- Jail list:", "")
        return (True, "", "")

    with patch("routers.v1.vps_security.run_ssh_command", mock_empty_jails):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/admin/vps-security/jails")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# ==============================================================================
# Performance Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_status_response_time(admin_client, mock_ssh_success):
    """Test that status endpoint responds within acceptable time."""
    import time

    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            start = time.perf_counter()
            response = await client.get("/api/admin/vps-security/status")
            duration_ms = (time.perf_counter() - start) * 1000

            assert response.status_code == 200
            # Should respond within 500ms (excluding real SSH calls)
            assert duration_ms < 500, f"Response took {duration_ms:.2f}ms"


@pytest.mark.asyncio
async def test_report_response_time(admin_client, mock_ssh_success):
    """Test that full report endpoint responds within acceptable time."""
    import time

    with patch("routers.v1.vps_security.run_ssh_command", mock_ssh_success):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            start = time.perf_counter()
            response = await client.get("/api/admin/vps-security/report")
            duration_ms = (time.perf_counter() - start) * 1000

            assert response.status_code == 200
            # Full report may take longer, allow 1000ms
            assert duration_ms < 1000, f"Response took {duration_ms:.2f}ms"
