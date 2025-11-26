#!/usr/bin/env python3
"""
Production Log Monitor - Race Condition & Encryption Tracking

Monitors production logs for:
- IntegrityError (race conditions - expected behavior)
- Encryption errors
- Database lock contention
- Performance degradation

Usage:
    python monitor_production_logs.py /var/log/myhibachi-backend.log
    python monitor_production_logs.py /var/log/myhibachi-backend.log --interval 30
    python monitor_production_logs.py /var/log/myhibachi-backend.log --alert-email admin@myhibachi.com
"""

import re
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Tuple


class LogMonitor:
    """Monitor production logs for critical patterns"""

    def __init__(self, log_file: Path, interval: int = 60):
        self.log_file = log_file
        self.interval = interval
        self.stats = defaultdict(int)
        self.alerts = []

        # Patterns to monitor
        self.patterns = {
            "race_condition": [
                r"IntegrityError.*idx_booking_date_slot_active",
                r"unique constraint.*violated.*booking",
                r"duplicate key value violates unique constraint.*idx_booking_date_slot_active",
            ],
            "encryption_error": [
                r"Fernet.*Invalid",
                r"cryptography.*error",
                r"decrypt.*failed",
                r"encryption.*failed",
            ],
            "database_lock": [
                r"lock.*timeout",
                r"deadlock detected",
                r"could not obtain lock",
            ],
            "performance": [
                r"slow query.*duration.*[5-9]\d{3}",  # >5s queries
                r"timeout.*exceeded",
            ],
        }

    def parse_log_entry(self, line: str) -> Tuple[str, str, str]:
        """Extract timestamp, level, and message from log line"""
        # Example: 2025-11-26 10:30:45 INFO: Customer created
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+): (.+)", line)
        if match:
            return match.groups()
        return "", "", line

    def check_patterns(self, line: str):
        """Check line against all monitoring patterns"""
        timestamp, level, message = self.parse_log_entry(line)

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    self.stats[category] += 1

                    # Create alert
                    alert = {
                        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
                        "category": category,
                        "level": level or "UNKNOWN",
                        "message": message.strip(),
                        "pattern": pattern,
                    }
                    self.alerts.append(alert)

                    # Print immediate alert
                    self.print_alert(alert)

    def print_alert(self, alert: Dict):
        """Print alert to console"""
        severity = {
            "race_condition": "⚠️ WARNING",
            "encryption_error": "🔴 ERROR",
            "database_lock": "🟠 ERROR",
            "performance": "🟡 WARNING",
        }.get(alert["category"], "ℹ️ INFO")

        print(f"\n{severity} [{alert['timestamp']}] {alert['category'].upper()}")
        print(f"  Message: {alert['message'][:200]}...")
        print(f"  Pattern: {alert['pattern']}")

    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "="*80)
        print(f"📊 MONITORING SUMMARY ({datetime.now(timezone.utc).isoformat()})")
        print("="*80)

        if not self.stats:
            print("\n✅ No issues detected")
            return

        print("\n📈 Detection Counts:")
        for category, count in sorted(self.stats.items()):
            icon = {
                "race_condition": "⚠️",
                "encryption_error": "🔴",
                "database_lock": "🟠",
                "performance": "🟡",
            }.get(category, "ℹ️")
            print(f"  {icon} {category}: {count}")

        # Analysis
        print("\n📝 Analysis:")

        if self.stats["race_condition"] > 0:
            print(f"  ⚠️ Race conditions detected: {self.stats['race_condition']}")
            print(f"     This is EXPECTED behavior (graceful failure)")
            print(f"     Action: Verify bookings created correctly")
            if self.stats["race_condition"] > 10:
                print(f"     ⚠️ High frequency! Consider adding application-level locking")

        if self.stats["encryption_error"] > 0:
            print(f"  🔴 Encryption errors: {self.stats['encryption_error']}")
            print(f"     Action: Check FIELD_ENCRYPTION_KEY configuration")
            print(f"     Verify key hasn't changed/rotated incorrectly")

        if self.stats["database_lock"] > 0:
            print(f"  🟠 Database locks: {self.stats['database_lock']}")
            print(f"     Action: Review concurrent booking patterns")
            print(f"     Consider optimizing SELECT FOR UPDATE usage")

        if self.stats["performance"] > 0:
            print(f"  🟡 Performance issues: {self.stats['performance']}")
            print(f"     Action: Review slow queries, add indexes if needed")

    def run(self):
        """Start monitoring log file"""
        print("="*80)
        print(f"🔍 Monitoring: {self.log_file}")
        print(f"⏱️ Interval: {self.interval}s")
        print(f"🕒 Started: {datetime.now(timezone.utc).isoformat()}")
        print("="*80)

        if not self.log_file.exists():
            print(f"❌ Log file not found: {self.log_file}")
            return

        # Get initial file size to start from end
        last_position = self.log_file.stat().st_size

        try:
            while True:
                # Check if file has grown
                current_size = self.log_file.stat().st_size

                if current_size > last_position:
                    # Read new lines
                    with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_position)
                        for line in f:
                            self.check_patterns(line)

                    last_position = current_size

                elif current_size < last_position:
                    # File was rotated or truncated
                    print(f"\n🔄 Log file rotated/truncated at {datetime.now(timezone.utc).isoformat()}")
                    last_position = 0

                # Wait for next check
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n\n⏹️ Monitoring stopped by user")
            self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Monitor My Hibachi production logs for critical patterns"
    )
    parser.add_argument(
        "log_file",
        type=Path,
        help="Path to log file (e.g., /var/log/myhibachi-backend.log)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--alert-email",
        type=str,
        help="Email address for critical alerts (not implemented)"
    )

    args = parser.parse_args()

    monitor = LogMonitor(args.log_file, args.interval)
    monitor.run()


if __name__ == "__main__":
    main()
