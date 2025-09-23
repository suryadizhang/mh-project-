#!/usr/bin/env python3
"""
System Health Monitor for My Hibachi Production VPS
Monitors system resources, services, and application health
"""

import os
import sys
import time
import json
import psutil
import requests
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse

# Configuration
MONITOR_CONFIG = {
    "check_interval": 60,  # seconds
    "log_retention_days": 7,
    "alert_thresholds": {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "load_average": 2.0,
        "response_time_ms": 5000
    },
    "services": [
        "nginx",
        "postgresql",
        "redis-server",
        "myhibachi-backend",
        "myhibachi-frontend"
    ],
    "endpoints": [
        {"url": "http://localhost/health", "name": "frontend", "timeout": 10},
        {"url": "http://localhost:8000/health", "name": "backend", "timeout": 10},
        {"url": "http://localhost:8001/health", "name": "ai-backend", "timeout": 10}
    ]
}

LOG_DIR = Path("/var/log/myhibachi")
DATA_DIR = Path("/var/lib/myhibachi/monitoring")

@dataclass
class SystemMetrics:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    load_average: Tuple[float, float, float]
    network_io: Dict[str, int]
    process_count: int
    uptime_seconds: int

@dataclass
class ServiceStatus:
    name: str
    status: str
    pid: Optional[int]
    memory_mb: Optional[float]
    cpu_percent: Optional[float]
    restart_count: int

@dataclass
class EndpointHealth:
    name: str
    url: str
    status_code: Optional[int]
    response_time_ms: Optional[float]
    is_healthy: bool
    error: Optional[str]

@dataclass
class HealthReport:
    timestamp: str
    system_metrics: SystemMetrics
    service_statuses: List[ServiceStatus]
    endpoint_health: List[EndpointHealth]
    alerts: List[str]
    overall_status: str

class SystemHealthMonitor:
    def __init__(self):
        self.setup_logging()
        self.ensure_directories()
        self.restart_counts = {}
        
    def setup_logging(self):
        """Configure logging"""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / "health_monitor.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def ensure_directories(self):
        """Ensure monitoring directories exist"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    def get_system_metrics(self) -> SystemMetrics:
        """Collect system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage for important mount points
        disk_usage = {}
        for mount_point in ["/", "/var", "/tmp"]:
            try:
                disk = psutil.disk_usage(mount_point)
                disk_usage[mount_point] = (disk.used / disk.total) * 100
            except:
                disk_usage[mount_point] = 0
                
        # Load average
        load_avg = os.getloadavg()
        
        # Network I/O
        net_io = psutil.net_io_counters()
        network_io = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv
        }
        
        # Process count
        process_count = len(psutil.pids())
        
        # System uptime
        uptime_seconds = int(time.time() - psutil.boot_time())
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage=disk_usage,
            load_average=load_avg,
            network_io=network_io,
            process_count=process_count,
            uptime_seconds=uptime_seconds
        )
        
    def check_service_status(self, service_name: str) -> ServiceStatus:
        """Check systemd service status"""
        try:
            # Get service status
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True, text=True
            )
            status = result.stdout.strip()
            
            # Get service PID if running
            pid = None
            memory_mb = None
            cpu_percent = None
            
            if status == "active":
                try:
                    pid_result = subprocess.run(
                        ["systemctl", "show", service_name, "--property=MainPID"],
                        capture_output=True, text=True
                    )
                    pid_line = pid_result.stdout.strip()
                    if "MainPID=" in pid_line:
                        pid = int(pid_line.split("=")[1])
                        
                        # Get process metrics
                        if pid > 0:
                            try:
                                process = psutil.Process(pid)
                                memory_mb = process.memory_info().rss / 1024 / 1024
                                cpu_percent = process.cpu_percent()
                            except psutil.NoSuchProcess:
                                pass
                except:
                    pass
                    
            # Track restart count
            restart_count = self.restart_counts.get(service_name, 0)
            if status != "active" and service_name not in self.restart_counts:
                self.restart_counts[service_name] = 0
            elif status == "active" and service_name in self.restart_counts:
                if self.restart_counts[service_name] > 0:
                    self.restart_counts[service_name] += 1
                    
            return ServiceStatus(
                name=service_name,
                status=status,
                pid=pid,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                restart_count=restart_count
            )
            
        except Exception as e:
            self.logger.error(f"Error checking service {service_name}: {e}")
            return ServiceStatus(
                name=service_name,
                status="error",
                pid=None,
                memory_mb=None,
                cpu_percent=None,
                restart_count=0
            )
            
    def check_endpoint_health(self, endpoint: Dict) -> EndpointHealth:
        """Check HTTP endpoint health"""
        try:
            start_time = time.time()
            response = requests.get(
                endpoint["url"],
                timeout=endpoint.get("timeout", 10),
                headers={"User-Agent": "MyHibachi-HealthMonitor/1.0"}
            )
            response_time_ms = (time.time() - start_time) * 1000
            
            is_healthy = response.status_code == 200
            
            return EndpointHealth(
                name=endpoint["name"],
                url=endpoint["url"],
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                is_healthy=is_healthy,
                error=None
            )
            
        except requests.exceptions.Timeout:
            return EndpointHealth(
                name=endpoint["name"],
                url=endpoint["url"],
                status_code=None,
                response_time_ms=None,
                is_healthy=False,
                error="Timeout"
            )
        except Exception as e:
            return EndpointHealth(
                name=endpoint["name"],
                url=endpoint["url"],
                status_code=None,
                response_time_ms=None,
                is_healthy=False,
                error=str(e)
            )
            
    def generate_alerts(self, metrics: SystemMetrics, services: List[ServiceStatus], 
                       endpoints: List[EndpointHealth]) -> List[str]:
        """Generate alerts based on thresholds"""
        alerts = []
        thresholds = MONITOR_CONFIG["alert_thresholds"]
        
        # System resource alerts
        if metrics.cpu_percent > thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
        if metrics.memory_percent > thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
            
        for mount, usage in metrics.disk_usage.items():
            if usage > thresholds["disk_percent"]:
                alerts.append(f"High disk usage on {mount}: {usage:.1f}%")
                
        if metrics.load_average[0] > thresholds["load_average"]:
            alerts.append(f"High load average: {metrics.load_average[0]:.2f}")
            
        # Service alerts
        for service in services:
            if service.status != "active":
                alerts.append(f"Service {service.name} is {service.status}")
                
        # Endpoint alerts
        for endpoint in endpoints:
            if not endpoint.is_healthy:
                error_msg = f"Endpoint {endpoint.name} is unhealthy"
                if endpoint.error:
                    error_msg += f": {endpoint.error}"
                alerts.append(error_msg)
            elif (endpoint.response_time_ms and 
                  endpoint.response_time_ms > thresholds["response_time_ms"]):
                alerts.append(f"Slow response from {endpoint.name}: "
                            f"{endpoint.response_time_ms:.0f}ms")
                
        return alerts
        
    def save_health_report(self, report: HealthReport):
        """Save health report to file"""
        report_file = DATA_DIR / f"health_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        try:
            with open(report_file, "a") as f:
                f.write(json.dumps(asdict(report)) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to save health report: {e}")
            
    def cleanup_old_reports(self):
        """Remove old health report files"""
        cutoff_date = datetime.now() - timedelta(days=MONITOR_CONFIG["log_retention_days"])
        
        for report_file in DATA_DIR.glob("health_*.jsonl"):
            try:
                file_date = datetime.strptime(report_file.stem.split("_")[1], "%Y%m%d")
                if file_date < cutoff_date:
                    report_file.unlink()
                    self.logger.info(f"Removed old report: {report_file.name}")
            except Exception as e:
                self.logger.error(f"Error processing {report_file}: {e}")
                
    def run_health_check(self) -> HealthReport:
        """Run complete health check"""
        # Collect system metrics
        system_metrics = self.get_system_metrics()
        
        # Check service statuses
        service_statuses = []
        for service_name in MONITOR_CONFIG["services"]:
            status = self.check_service_status(service_name)
            service_statuses.append(status)
            
        # Check endpoint health
        endpoint_health = []
        for endpoint in MONITOR_CONFIG["endpoints"]:
            health = self.check_endpoint_health(endpoint)
            endpoint_health.append(health)
            
        # Generate alerts
        alerts = self.generate_alerts(system_metrics, service_statuses, endpoint_health)
        
        # Determine overall status
        overall_status = "healthy"
        if alerts:
            critical_keywords = ["high cpu", "high memory", "high disk", "service", "unhealthy"]
            if any(any(keyword in alert.lower() for keyword in critical_keywords) 
                   for alert in alerts):
                overall_status = "critical"
            else:
                overall_status = "warning"
                
        report = HealthReport(
            timestamp=datetime.now().isoformat(),
            system_metrics=system_metrics,
            service_statuses=service_statuses,
            endpoint_health=endpoint_health,
            alerts=alerts,
            overall_status=overall_status
        )
        
        return report
        
    def run_continuous_monitoring(self):
        """Run continuous health monitoring"""
        self.logger.info("Starting continuous health monitoring")
        
        while True:
            try:
                # Run health check
                report = self.run_health_check()
                
                # Log status
                if report.alerts:
                    self.logger.warning(f"Health check alerts: {', '.join(report.alerts)}")
                else:
                    self.logger.info("Health check: All systems healthy")
                    
                # Save report
                self.save_health_report(report)
                
                # Cleanup old reports periodically
                if datetime.now().hour == 3 and datetime.now().minute < 5:  # 3 AM
                    self.cleanup_old_reports()
                    
                # Wait for next check
                time.sleep(MONITOR_CONFIG["check_interval"])
                
            except KeyboardInterrupt:
                self.logger.info("Health monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(60)  # Wait a minute before retrying

def main():
    parser = argparse.ArgumentParser(description="My Hibachi System Health Monitor")
    parser.add_argument("--once", action="store_true", help="Run health check once and exit")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup old reports only")
    
    args = parser.parse_args()
    
    monitor = SystemHealthMonitor()
    
    if args.cleanup:
        monitor.cleanup_old_reports()
        sys.exit(0)
        
    if args.once:
        report = monitor.run_health_check()
        
        if args.json:
            print(json.dumps(asdict(report), indent=2))
        else:
            print(f"Overall Status: {report.overall_status}")
            print(f"Timestamp: {report.timestamp}")
            
            if report.alerts:
                print("\nAlerts:")
                for alert in report.alerts:
                    print(f"  - {alert}")
            else:
                print("\nNo alerts - all systems healthy")
                
            print(f"\nSystem Metrics:")
            print(f"  CPU: {report.system_metrics.cpu_percent:.1f}%")
            print(f"  Memory: {report.system_metrics.memory_percent:.1f}%")
            print(f"  Load: {report.system_metrics.load_average[0]:.2f}")
            
        sys.exit(0 if report.overall_status == "healthy" else 1)
        
    # Run continuous monitoring
    monitor.run_continuous_monitoring()

if __name__ == "__main__":
    main()