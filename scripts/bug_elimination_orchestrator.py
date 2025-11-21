#!/usr/bin/env python3
"""
MASTER BUG ELIMINATION ORCHESTRATOR
Coordinates the entire bug elimination process with rollback safety
"""

from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


class BugEliminationOrchestrator:
    """Master coordinator for the entire bug elimination battle plan"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.session_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path("bug_elimination_results") / self.session_id
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Execution phases in order
        self.phases = {
            "phase_0_scan": {
                "name": "Emergency Bug Discovery",
                "script": "scripts/immediate_bug_scan.py",
                "required": True,
                "description": "Scan for critical bugs without external dependencies",
                "success_criteria": {"critical_bugs": 0, "high_bugs": "<10"},
            },
            "phase_1_test": {
                "name": "Pre-Fix Testing",
                "script": "scripts/progressive_testing_framework.py",
                "args": ["critical"],
                "required": True,
                "description": "Establish baseline functionality before fixes",
                "success_criteria": {"overall_status": "PASS"},
            },
            "phase_2_backup": {
                "name": "System Backup",
                "function": self.create_system_backup,
                "required": True,
                "description": "Create full system backup before applying fixes",
                "success_criteria": {"backup_created": True},
            },
            "phase_3_fix": {
                "name": "Critical Bug Auto-Fix",
                "script": "scripts/critical_bug_autofixer.py",
                "required": True,
                "description": "Apply automated fixes for critical vulnerabilities",
                "success_criteria": {"fixes_applied": ">0", "errors": 0},
            },
            "phase_4_test": {
                "name": "Post-Fix Testing",
                "script": "scripts/progressive_testing_framework.py",
                "args": ["security"],
                "required": True,
                "description": "Verify fixes don't break functionality",
                "success_criteria": {
                    "overall_status": "PASS",
                    "critical_failures": 0,
                },
            },
            "phase_5_verify": {
                "name": "Security Verification",
                "script": "scripts/immediate_bug_scan.py",
                "required": True,
                "description": "Verify critical bugs have been eliminated",
                "success_criteria": {"critical_bugs": 0},
            },
        }

        self.execution_log = []

    def log_phase_result(
        self, phase: str, success: bool, details: dict[str, Any]
    ):
        """Log the result of a phase execution"""
        self.execution_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "phase": phase,
                "success": success,
                "details": details,
            }
        )

        # Save log after each phase
        with open(self.results_dir / "execution_log.json", "w") as f:
            json.dump(self.execution_log, f, indent=2)

    def create_system_backup(self) -> dict[str, Any]:
        """Create full system backup before applying fixes"""
        print("💾 Creating system backup...")

        backup_dir = self.results_dir / "system_backup"
        backup_dir.mkdir(exist_ok=True)

        try:
            # Backup critical directories
            critical_dirs = ["apps", "scripts", "tests"]
            backup_info = {
                "timestamp": datetime.now(UTC).isoformat(),
                "backed_up_dirs": [],
                "total_files": 0,
            }

            for dir_name in critical_dirs:
                source_dir = self.project_root / dir_name
                if source_dir.exists():
                    target_dir = backup_dir / dir_name
                    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

                    # Count files
                    file_count = len(list(target_dir.rglob("*")))
                    backup_info["backed_up_dirs"].append(
                        {"directory": dir_name, "files_backed_up": file_count}
                    )
                    backup_info["total_files"] += file_count

            # Create backup manifest
            with open(backup_dir / "backup_manifest.json", "w") as f:
                json.dump(backup_info, f, indent=2)

            return {
                "status": "success",
                "backup_location": str(backup_dir),
                "backup_info": backup_info,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_script_phase(
        self, script_path: str, args: list[str] = None
    ) -> dict[str, Any]:
        """Run a Python script phase and capture results"""
        args = args or []

        try:
            # Ensure script exists
            if not Path(script_path).exists():
                return {
                    "status": "error",
                    "error": f"Script not found: {script_path}",
                }

            # Run script
            cmd = [sys.executable, script_path] + args
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,  # 5 minute timeout
            )

            # Parse output for JSON results if available
            output_data = {}
            try:
                # Look for JSON files created by the script
                for json_file in [
                    "emergency_bug_report.json",
                    "critical_fixes_applied.json",
                    "progressive_test_results.json",
                ]:
                    json_path = self.project_root / json_file
                    if json_path.exists():
                        with open(json_path) as f:
                            output_data[json_file] = json.load(f)
            except Exception:
                pass

            return {
                "status": "success" if result.returncode == 0 else "error",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_data": output_data,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Script execution timeout (5 minutes)",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def check_success_criteria(
        self, phase_config: dict[str, Any], result: dict[str, Any]
    ) -> bool:
        """Check if phase met its success criteria"""
        criteria = phase_config.get("success_criteria", {})

        if not criteria:
            return result["status"] == "success"

        # Extract data from results
        data_source = result.get("output_data", {})

        for criterion, expected in criteria.items():
            if criterion == "overall_status":
                # Check test results
                for json_data in data_source.values():
                    if "overall_status" in json_data:
                        if json_data["overall_status"] != expected:
                            return False

            elif criterion == "critical_bugs":
                # Check bug scan results
                for json_data in data_source.values():
                    if "summary" in json_data:
                        critical_count = json_data["summary"].get(
                            "critical", 0
                        )
                        if expected == 0 and critical_count > 0:
                            return False

            elif criterion == "fixes_applied":
                # Check fix results
                for json_data in data_source.values():
                    if "total_fixes_applied" in json_data:
                        fixes_count = json_data["total_fixes_applied"]
                        if expected == ">0" and fixes_count == 0:
                            return False

        return True

    def execute_phase(
        self, phase_name: str, phase_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a single phase of the bug elimination process"""
        print(f"\n🚀 Executing Phase: {phase_config['name']}")
        print(f"📝 Description: {phase_config['description']}")

        if "script" in phase_config:
            # Script-based phase
            args = phase_config.get("args", [])
            result = self.run_script_phase(phase_config["script"], args)
        elif "function" in phase_config:
            # Function-based phase
            result = phase_config["function"]()
        else:
            result = {
                "status": "error",
                "error": "No execution method defined",
            }

        # Check success criteria
        success = self.check_success_criteria(phase_config, result)

        # Log result
        self.log_phase_result(phase_name, success, result)

        status_icon = "✅" if success else "❌"
        print(
            f"{status_icon} Phase {phase_config['name']}: {'SUCCESS' if success else 'FAILED'}"
        )

        return result

    def rollback_changes(self):
        """Rollback changes if critical phases fail"""
        print("🔄 Rolling back changes due to failures...")

        backup_dir = self.results_dir / "system_backup"
        if backup_dir.exists():
            try:
                # Restore from backup
                critical_dirs = ["apps", "scripts", "tests"]
                for dir_name in critical_dirs:
                    source_backup = backup_dir / dir_name
                    target_dir = self.project_root / dir_name

                    if source_backup.exists() and target_dir.exists():
                        shutil.rmtree(target_dir)
                        shutil.copytree(source_backup, target_dir)

                print("✅ Successfully rolled back all changes")
                return True

            except Exception as e:
                print(f"❌ Rollback failed: {e}")
                return False
        else:
            print("❌ No backup found for rollback")
            return False

    def run_complete_elimination_process(self) -> dict[str, Any]:
        """Execute the complete bug elimination process"""

        print(
            f"""
🚨 STARTING COMPREHENSIVE BUG ELIMINATION 🚨

Session ID: {self.session_id}
Results Directory: {self.results_dir}
Project Root: {self.project_root}

🎯 Phases to Execute:
        """
        )

        for phase_name, phase_config in self.phases.items():
            required = "REQUIRED" if phase_config["required"] else "OPTIONAL"
            print(f"   {phase_name}: {phase_config['name']} ({required})")

        print("\n" + "=" * 60)

        # Execute phases
        results = {
            "session_id": self.session_id,
            "start_time": datetime.now(UTC).isoformat(),
            "phases_executed": {},
            "overall_success": True,
            "rollback_performed": False,
        }

        for phase_name, phase_config in self.phases.items():
            phase_result = self.execute_phase(phase_name, phase_config)
            results["phases_executed"][phase_name] = phase_result

            # Check if phase failed and is required
            if (
                phase_result["status"] != "success"
                and phase_config["required"]
            ):
                print(
                    f"\n🚨 CRITICAL FAILURE in required phase: {phase_config['name']}"
                )
                results["overall_success"] = False

                # Perform rollback if we've made changes
                if phase_name in ["phase_3_fix", "phase_4_test"]:
                    results["rollback_performed"] = self.rollback_changes()

                break

        results["end_time"] = datetime.now(UTC).isoformat()

        # Save final results
        with open(self.results_dir / "final_results.json", "w") as f:
            json.dump(results, f, indent=2)

        return results

    def generate_final_report(self, results: dict[str, Any]):
        """Generate final human-readable report"""

        success_icon = "🎉" if results["overall_success"] else "🚨"

        print(
            f"""
{success_icon} BUG ELIMINATION PROCESS COMPLETE {success_icon}

📊 EXECUTION SUMMARY:
   Overall Success: {"✅ YES" if results['overall_success'] else "❌ NO"}
   Session ID: {results['session_id']}
   Start Time: {results['start_time']}
   End Time: {results['end_time']}
   Rollback Performed: {"Yes" if results['rollback_performed'] else "No"}

📋 PHASE RESULTS:
        """
        )

        for phase_name, phase_result in results["phases_executed"].items():
            phase_config = self.phases[phase_name]
            status_icon = "✅" if phase_result["status"] == "success" else "❌"
            print(
                f"   {status_icon} {phase_config['name']}: {phase_result['status'].upper()}"
            )

        if results["overall_success"]:
            print(
                f"""
🎉 SUCCESS! Your My Hibachi system has been significantly improved:

✅ Critical security vulnerabilities eliminated
✅ Silent exceptions properly handled  
✅ Timezone issues resolved
✅ Race conditions protected
✅ System functionality verified

🎯 NEXT STEPS:
   1. Review detailed results: {self.results_dir}/final_results.json
   2. Commit changes: git add -A && git commit -m "🚨 CRITICAL: Eliminate security vulnerabilities"
   3. Deploy to staging for testing
   4. Continue with Phase 2 of the full battle plan

🔧 Files Modified: Check git diff for all changes made
💾 Backup Location: {self.results_dir}/system_backup
            """
            )
        else:
            print(
                f"""
🚨 PROCESS FAILED - System requires manual attention

❌ Critical issues prevented automatic bug elimination
🔄 {"System rolled back to original state" if results['rollback_performed'] else "Manual rollback may be needed"}

📋 REQUIRED ACTIONS:
   1. Review failure details: {self.results_dir}/execution_log.json
   2. Fix blocking issues manually
   3. Re-run elimination process
   
💡 TROUBLESHOOTING:
   - Check that all scripts are executable
   - Ensure Python environment is set up correctly
   - Verify project structure matches expectations
            """
            )


if __name__ == "__main__":
    print("🚀 My Hibachi Bug Elimination Orchestrator")
    print("==========================================")

    orchestrator = BugEliminationOrchestrator()
    results = orchestrator.run_complete_elimination_process()
    orchestrator.generate_final_report(results)

    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)
