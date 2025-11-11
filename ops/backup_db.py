#!/usr/bin/env python3
"""
Database Backup Script for My Hibachi Production
Handles PostgreSQL backups with rotation, compression, and cloud storage
"""

import os
import sys
import datetime
import subprocess
import logging
import argparse
import gzip
import shutil
from pathlib import Path
from typing import Optional

# Configuration
BACKUP_DIR = Path("/var/backups/myhibachi")
LOG_DIR = Path("/var/log/myhibachi")
RETENTION_DAYS = 30
MAX_BACKUPS = 10

# Database configuration (from environment)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "myhibachi")
DB_USER = os.getenv("DB_USER", "myhibachi")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Cloud storage configuration (optional)
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

class DatabaseBackup:
    def __init__(self):
        self.setup_logging()
        self.ensure_directories()
        
    def setup_logging(self):
        """Configure logging"""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / "backup.log"
        
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
        """Ensure backup directories exist"""
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Backup directory: {BACKUP_DIR}")
        
    def create_backup(self) -> Optional[Path]:
        """Create PostgreSQL database backup"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"myhibachi_backup_{timestamp}.sql"
        backup_path = BACKUP_DIR / backup_filename
        
        # Set PGPASSWORD for pg_dump
        env = os.environ.copy()
        if DB_PASSWORD:
            env["PGPASSWORD"] = DB_PASSWORD
            
        # Create pg_dump command
        cmd = [
            "pg_dump",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", DB_NAME,
            "--no-password",
            "--verbose",
            "--format=custom",
            "--file", str(backup_path)
        ]
        
        try:
            self.logger.info(f"Starting backup: {backup_filename}")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Backup created successfully: {backup_path}")
                
                # Compress the backup
                compressed_path = self.compress_backup(backup_path)
                return compressed_path
            else:
                self.logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("Backup timed out after 1 hour")
            return None
        except Exception as e:
            self.logger.error(f"Backup error: {e}")
            return None
            
    def compress_backup(self, backup_path: Path) -> Path:
        """Compress backup file with gzip"""
        compressed_path = backup_path.with_suffix(backup_path.suffix + ".gz")
        
        try:
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    
            # Remove uncompressed file
            backup_path.unlink()
            
            # Log compression ratio
            original_size = backup_path.stat().st_size if backup_path.exists() else 0
            compressed_size = compressed_path.stat().st_size
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            self.logger.info(f"Backup compressed: {compressed_path} (saved {ratio:.1f}%)")
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
            return backup_path
            
    def upload_to_s3(self, backup_path: Path) -> bool:
        """Upload backup to AWS S3"""
        if not AWS_S3_BUCKET:
            self.logger.info("S3 bucket not configured, skipping upload")
            return True
            
        try:
            cmd = [
                "aws", "s3", "cp",
                str(backup_path),
                f"s3://{AWS_S3_BUCKET}/backups/{backup_path.name}",
                "--region", AWS_REGION
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Backup uploaded to S3: {backup_path.name}")
                return True
            else:
                self.logger.error(f"S3 upload failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"S3 upload error: {e}")
            return False
            
    def cleanup_old_backups(self):
        """Remove old backup files"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=RETENTION_DAYS)
        
        backups = list(BACKUP_DIR.glob("myhibachi_backup_*.sql.gz"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep maximum number of backups
        if len(backups) > MAX_BACKUPS:
            for backup in backups[MAX_BACKUPS:]:
                try:
                    backup.unlink()
                    self.logger.info(f"Removed old backup: {backup.name}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {backup.name}: {e}")
                    
        # Remove backups older than retention period
        for backup in backups:
            backup_time = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
            if backup_time < cutoff_date:
                try:
                    backup.unlink()
                    self.logger.info(f"Removed expired backup: {backup.name}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {backup.name}: {e}")
                    
    def verify_backup(self, backup_path: Path) -> bool:
        """Verify backup file integrity"""
        try:
            # Check if file exists and is not empty
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                self.logger.error(f"Backup file is empty or missing: {backup_path}")
                return False
                
            # Test gzip integrity if compressed
            if backup_path.suffix == ".gz":
                result = subprocess.run(
                    ["gzip", "-t", str(backup_path)],
                    capture_output=True
                )
                if result.returncode != 0:
                    self.logger.error(f"Backup file is corrupted: {backup_path}")
                    return False
                    
            self.logger.info(f"Backup verification passed: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False
            
    def run_backup(self, upload_s3: bool = True) -> bool:
        """Run complete backup process"""
        self.logger.info("Starting database backup process")
        
        # Create backup
        backup_path = self.create_backup()
        if not backup_path:
            return False
            
        # Verify backup
        if not self.verify_backup(backup_path):
            return False
            
        # Upload to S3 if requested
        if upload_s3:
            self.upload_to_s3(backup_path)
            
        # Cleanup old backups
        self.cleanup_old_backups()
        
        self.logger.info("Backup process completed successfully")
        return True

def main():
    parser = argparse.ArgumentParser(description="My Hibachi Database Backup")
    parser.add_argument("--no-s3", action="store_true", help="Skip S3 upload")
    parser.add_argument("--verify-only", type=str, help="Only verify specified backup file")
    parser.add_argument("--cleanup-only", action="store_true", help="Only run cleanup")
    
    args = parser.parse_args()
    
    backup = DatabaseBackup()
    
    if args.verify_only:
        backup_path = Path(args.verify_only)
        success = backup.verify_backup(backup_path)
        sys.exit(0 if success else 1)
        
    if args.cleanup_only:
        backup.cleanup_old_backups()
        sys.exit(0)
        
    # Run full backup
    success = backup.run_backup(upload_s3=not args.no_s3)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()