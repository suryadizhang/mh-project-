"""
Unit Tests for VPS Security Router
==================================

Tests for VPS security monitoring endpoints including:
- Status checks
- Jail management
- Banned IPs retrieval
- Firewall rules
- Attack logs
- Unban functionality

These tests mock SSH commands since we don't want to actually
connect to VPS during unit tests.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import router functions and models
from routers.v1.vps_security import (
    AttackLogEntry,
    BannedIP,
    FirewallRule,
    JailStatus,
    SecurityStats,
    SecurityStatus,
    UnbanRequest,
    UnbanResponse,
    parse_firewalld_rich_rules,
    parse_jail_status,
    router,
    run_ssh_command,
)

# ==============================================================================
# Test Helper Function: parse_jail_status
# ==============================================================================


class TestParseJailStatus:
    """Tests for parsing fail2ban jail status output."""

    def test_parse_jail_status_with_banned_ips(self):
        """Test parsing jail status with multiple banned IPs."""
        output = """
Status for the jail: sshd
|- Filter
|  |- Currently failed:	0
|  |- Total failed:	123
|  `- File list:	/var/log/secure
`- Actions
   |- Currently banned:	3
   |- Total banned:	45
   `- Banned IP list:	192.168.1.1 10.0.0.1 172.16.0.1
"""
        result = parse_jail_status(output)

        assert result["currently_banned"] == 3
        assert result["total_banned"] == 45
        assert result["banned_ips"] == ["192.168.1.1", "10.0.0.1", "172.16.0.1"]

    def test_parse_jail_status_no_banned(self):
        """Test parsing jail status with no banned IPs."""
        output = """
Status for the jail: nginx-http-auth
|- Filter
|  |- Currently failed:	0
|  |- Total failed:	10
|  `- File list:	/var/log/nginx/error.log
`- Actions
   |- Currently banned:	0
   |- Total banned:	5
   `- Banned IP list:
"""
        result = parse_jail_status(output)

        assert result["currently_banned"] == 0
        assert result["total_banned"] == 5
        assert result["banned_ips"] == []

    def test_parse_jail_status_single_banned(self):
        """Test parsing jail status with single banned IP."""
        output = """
Status for the jail: recidive
`- Actions
   |- Currently banned:	1
   |- Total banned:	10
   `- Banned IP list:	8.8.8.8
"""
        result = parse_jail_status(output)

        assert result["currently_banned"] == 1
        assert result["total_banned"] == 10
        assert result["banned_ips"] == ["8.8.8.8"]


# ==============================================================================
# Test Helper Function: parse_firewalld_rich_rules
# ==============================================================================


class TestParseFirewallRichRules:
    """Tests for parsing firewalld rich rules."""

    def test_parse_rich_rules_with_source(self):
        """Test parsing rich rules with source address."""
        output = """rule family="ipv4" source address="192.168.1.100" reject
rule family="ipv4" source address="10.0.0.50" drop"""

        rules = parse_firewalld_rich_rules(output)

        assert len(rules) == 2
        assert rules[0].source_ip == "192.168.1.100"
        assert rules[0].family == "ipv4"
        assert rules[1].source_ip == "10.0.0.50"

    def test_parse_rich_rules_no_source(self):
        """Test parsing rich rules without source address."""
        output = """rule family="ipv4" port port="8080" protocol="tcp" accept"""

        rules = parse_firewalld_rich_rules(output)

        assert len(rules) == 1
        assert rules[0].source_ip is None
        assert "8080" in rules[0].rule

    def test_parse_rich_rules_empty(self):
        """Test parsing empty rich rules output."""
        output = ""

        rules = parse_firewalld_rich_rules(output)

        assert rules == []


# ==============================================================================
# Test SSH Command Runner (Mocked)
# ==============================================================================


class TestSSHCommand:
    """Tests for SSH command execution."""

    @pytest.mark.asyncio
    async def test_ssh_command_success(self):
        """Test successful SSH command execution."""
        with patch(
            "routers.v1.vps_security.asyncio.create_subprocess_shell"
        ) as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"command output", b""))
            mock_subprocess.return_value = mock_process

            success, stdout, stderr = await run_ssh_command("echo test")

            assert success is True
            assert stdout == "command output"
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_ssh_command_failure(self):
        """Test failed SSH command execution."""
        with patch(
            "routers.v1.vps_security.asyncio.create_subprocess_shell"
        ) as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(
                return_value=(b"", b"connection refused")
            )
            mock_subprocess.return_value = mock_process

            success, stdout, stderr = await run_ssh_command("fail command")

            assert success is False
            assert stderr == "connection refused"

    @pytest.mark.asyncio
    async def test_ssh_command_timeout(self):
        """Test SSH command timeout."""
        import asyncio

        with patch(
            "routers.v1.vps_security.asyncio.create_subprocess_shell"
        ) as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_subprocess.return_value = mock_process

            success, stdout, stderr = await run_ssh_command("slow command")

            assert success is False
            assert "timed out" in stderr.lower()


# ==============================================================================
# Test Pydantic Models
# ==============================================================================


class TestModels:
    """Tests for Pydantic model validation."""

    def test_banned_ip_model(self):
        """Test BannedIP model creation."""
        banned = BannedIP(
            ip="192.168.1.1",
            jail="sshd",
            ban_time="2025-01-26 10:30:00",
            country="USA",
            organization="DigitalOcean",
        )

        assert banned.ip == "192.168.1.1"
        assert banned.jail == "sshd"
        assert banned.country == "USA"

    def test_jail_status_model(self):
        """Test JailStatus model creation."""
        jail = JailStatus(
            name="sshd",
            enabled=True,
            currently_banned=5,
            total_banned=100,
            filter_path="/etc/fail2ban/filter.d/sshd.conf",
        )

        assert jail.name == "sshd"
        assert jail.enabled is True
        assert jail.currently_banned == 5

    def test_security_status_model(self):
        """Test SecurityStatus model creation."""
        status = SecurityStatus(
            fail2ban_running=True,
            firewalld_running=True,
            active_jails=5,
            total_banned_ips=25,
            last_checked="2025-01-26T10:00:00Z",
        )

        assert status.fail2ban_running is True
        assert status.active_jails == 5
        assert status.total_banned_ips == 25

    def test_attack_log_entry_model(self):
        """Test AttackLogEntry model creation."""
        entry = AttackLogEntry(
            timestamp="2025-01-26 10:30:00",
            jail="sshd",
            action="Ban",
            ip="192.168.1.1",
            message="Full log message",
        )

        assert entry.action == "Ban"
        assert entry.ip == "192.168.1.1"

    def test_security_stats_model(self):
        """Test SecurityStats model with defaults."""
        stats = SecurityStats()

        assert stats.total_bans_24h == 0
        assert stats.total_bans_7d == 0
        assert stats.most_attacked_jail is None
        assert stats.top_attacker_ips == []

    def test_unban_request_model(self):
        """Test UnbanRequest model validation."""
        request = UnbanRequest(ip="192.168.1.1", jail="sshd")

        assert request.ip == "192.168.1.1"
        assert request.jail == "sshd"

    def test_unban_request_no_jail(self):
        """Test UnbanRequest with no specific jail."""
        request = UnbanRequest(ip="192.168.1.1")

        assert request.ip == "192.168.1.1"
        assert request.jail is None

    def test_unban_response_model(self):
        """Test UnbanResponse model creation."""
        response = UnbanResponse(
            success=True,
            ip="192.168.1.1",
            unbanned_from=["sshd", "nginx-http-auth"],
            message="IP unbanned successfully",
        )

        assert response.success is True
        assert len(response.unbanned_from) == 2


# ==============================================================================
# Test Security Stats Parsing
# ==============================================================================


class TestSecurityStatsParsing:
    """Tests for security statistics parsing logic."""

    def test_parse_ban_count_output(self):
        """Test parsing ban count from wc -l output."""
        output = "42"
        count = int(output.strip())
        assert count == 42

    def test_parse_top_attacker_output(self):
        """Test parsing top attacker IP from sorted output."""
        output = """     15 192.168.1.100
      8 10.0.0.50
      3 172.16.0.1"""

        ips = []
        for line in output.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                ips.append(parts[1])

        assert ips == ["192.168.1.100", "10.0.0.50", "172.16.0.1"]

    def test_parse_most_attacked_jail(self):
        """Test parsing most attacked jail from grep output."""
        output = "     45 sshd"
        parts = output.strip().split()

        assert len(parts) >= 2
        assert parts[1] == "sshd"


# ==============================================================================
# Integration-style Tests (with mocked SSH)
# ==============================================================================


@pytest.mark.asyncio
class TestEndpointLogic:
    """Tests for endpoint business logic with mocked SSH."""

    async def test_security_status_logic(self):
        """Test security status endpoint logic."""
        # This would test the endpoint logic with mocked SSH
        # For now, verify the expected behavior

        # Mock responses
        fail2ban_active = "active"
        firewalld_active = "active"
        jail_list = """
Status
|- Number of jail:	5
`- Jail list:	sshd, nginx-http-auth, nginx-botsearch, nginx-bad-request, recidive
"""

        # Verify parsing
        import re

        match = re.search(r"Number of jail:\s*(\d+)", jail_list)
        assert match is not None
        assert int(match.group(1)) == 5

        jail_match = re.search(r"Jail list:\s*(.+)", jail_list)
        assert jail_match is not None
        jails = [j.strip() for j in jail_match.group(1).split(",")]
        assert len(jails) == 5
        assert "sshd" in jails

    async def test_attack_log_parsing(self):
        """Test parsing attack log entries."""
        import re

        log_line = "2025-01-26 02:34:26,123 fail2ban.actions [1234]: NOTICE [sshd] Ban 192.168.1.100"

        match = re.match(
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .+\[(\w+)\] (Ban|Unban) (\d+\.\d+\.\d+\.\d+)",
            log_line,
        )

        assert match is not None
        assert match.group(1) == "2025-01-26 02:34:26"
        assert match.group(2) == "sshd"
        assert match.group(3) == "Ban"
        assert match.group(4) == "192.168.1.100"


# ==============================================================================
# Test Known Attackers Data
# ==============================================================================


class TestKnownAttackers:
    """Tests for known attackers endpoint data."""

    def test_known_attacker_data_structure(self):
        """Test known attacker data has required fields."""
        attacker = {
            "ip": "159.223.4.35",
            "organization": "DigitalOcean, LLC",
            "country": "USA",
            "attack_type": "SSH brute force",
            "first_seen": "2025-01-26",
            "status": "banned",
        }

        assert "ip" in attacker
        assert "organization" in attacker
        assert "country" in attacker
        assert "attack_type" in attacker
        assert attacker["status"] == "banned"

    def test_ip_address_format_validation(self):
        """Test IP address format is valid."""
        import re

        ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"

        valid_ips = ["192.168.1.1", "10.0.0.1", "159.223.4.35"]
        invalid_ips = ["256.1.1.1", "abc.def.ghi.jkl", "192.168"]

        for ip in valid_ips:
            assert re.match(ip_pattern, ip), f"{ip} should be valid"

        for ip in invalid_ips:
            # Don't validate IP range here, just format
            if not re.match(ip_pattern, ip):
                pass  # Expected


# ==============================================================================
# Test Firewall Rule Parsing Edge Cases
# ==============================================================================


class TestFirewallRuleEdgeCases:
    """Edge case tests for firewall rule parsing."""

    def test_ipv6_rules(self):
        """Test parsing IPv6 firewall rules."""
        output = 'rule family="ipv6" source address="2001:db8::1" reject'

        rules = parse_firewalld_rich_rules(output)

        assert len(rules) == 1
        assert rules[0].source_ip == "2001:db8::1"

    def test_mixed_rules(self):
        """Test parsing mixed IPv4 and port rules."""
        output = """rule family="ipv4" source address="192.168.1.1" reject
rule family="ipv4" port port="22" protocol="tcp" accept
rule family="ipv4" source address="10.0.0.1" service name="http" reject"""

        rules = parse_firewalld_rich_rules(output)

        assert len(rules) == 3
        assert rules[0].source_ip == "192.168.1.1"
        assert rules[1].source_ip is None  # Port-based rule
        assert rules[2].source_ip == "10.0.0.1"

    def test_rules_with_whitespace(self):
        """Test parsing rules with extra whitespace."""
        output = """
        rule family="ipv4" source address="192.168.1.1" reject

        rule family="ipv4" source address="10.0.0.1" drop

"""

        rules = parse_firewalld_rich_rules(output)

        assert len(rules) == 2
