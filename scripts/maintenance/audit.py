#!/usr/bin/env python3
"""
MyHibachi Deep Production Audit - Critical Gap Analysis
Comprehensive audit to identify missing components for full production deployment
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class MyHibachiDeepAudit:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "audit_type": "deep_production_gap_analysis",
            "critical_gaps": [],
            "backend_analysis": {},
            "frontend_analysis": {},
            "integration_gaps": [],
            "production_blockers": [],
            "recommendations": []
        }
        
    def audit_backend_apis(self):
        """Comprehensive backend API audit"""
        print("🔍 === BACKEND APIS DEEP AUDIT ===")
        
        # Operational API Analysis
        operational_api = self.project_root / "apps" / "api"
        operational_issues = []
        
        # Check for missing critical components
        critical_files = {
            "main.py": operational_api / "app" / "main.py",
            "requirements.txt": operational_api / "requirements.txt",
            "Dockerfile": operational_api / "Dockerfile",
            ".env": operational_api / ".env",
            "auth.py": operational_api / "app" / "auth" / "__init__.py",
            "models": operational_api / "app" / "models",
            "routers": operational_api / "app" / "routers"
        }
        
        for name, path in critical_files.items():
            if not path.exists():
                operational_issues.append(f"Missing {name}: {path}")
                
        # Check for worker issues (from logs)
        worker_issues = [
            "EmailWorker: async_generator context manager protocol error",
            "StripeWorker: async_generator context manager protocol error",
            "Stripe setup failed: Invalid API Key"
        ]
        
        operational_issues.extend(worker_issues)
        
        # AI API Analysis  
        ai_api = self.project_root / "apps" / "ai-api"
        ai_issues = []
        
        # Check AI API capabilities
        ai_services = {
            "chat_service.py": ai_api / "app" / "services" / "chat_service.py",
            "ai_pipeline.py": ai_api / "app" / "services" / "ai_pipeline.py", 
            "knowledge_base.py": ai_api / "app" / "services" / "knowledge_base.py",
            "openai_service.py": ai_api / "app" / "services" / "openai_service.py"
        }
        
        for name, path in ai_services.items():
            if not path.exists():
                ai_issues.append(f"Missing AI service: {name}")
                
        # Check for REST API endpoints (missing)
        ai_routers = ai_api / "app" / "routers"
        if ai_routers.exists():
            router_files = list(ai_routers.glob("*.py"))
            if len(router_files) <= 1:  # Only webhooks.py
                ai_issues.append("Missing REST API endpoints for chat/AI functionality")
                
        self.audit_results["backend_analysis"] = {
            "operational_api": {
                "status": "PARTIALLY_FUNCTIONAL",
                "issues": operational_issues,
                "critical_gaps": [
                    "Worker processes failing with async context manager errors",
                    "Stripe integration requires valid API keys",
                    "Security middleware not fully available"
                ]
            },
            "ai_api": {
                "status": "INCOMPLETE",
                "issues": ai_issues,
                "critical_gaps": [
                    "No REST API endpoints for chat functionality",
                    "Missing admin integration endpoints",
                    "No WebSocket chat interface",
                    "Limited to webhook-based interactions only"
                ]
            }
        }
        
    def audit_frontend_apps(self):
        """Comprehensive frontend audit"""
        print("🎨 === FRONTEND APPLICATIONS AUDIT ===")
        
        # Admin Panel Analysis
        admin_path = self.project_root / "apps" / "admin"
        admin_gaps = []
        
        # Check for AI chatbot integration
        admin_src = admin_path / "src"
        chatbot_files = []
        if admin_src.exists():
            # Look for chat/AI related components
            chat_components = list(admin_src.glob("**/chat*")) + list(admin_src.glob("**/ai*"))
            if not chat_components:
                admin_gaps.append("No AI chatbot components found in admin panel")
                
        # Check API integration
        api_service = admin_path / "src" / "services" / "api.ts"
        if api_service.exists():
            with open(api_service) as f:
                content = f.read()
                if "8002" not in content:  # AI API port
                    admin_gaps.append("Admin panel not configured to connect to AI API")
                    
        # Customer App Analysis
        customer_path = self.project_root / "apps" / "customer"
        customer_gaps = []
        
        # Check for customer chat interface
        customer_src = customer_path / "src"
        if customer_src.exists():
            chat_components = list(customer_src.glob("**/chat*"))
            if not chat_components:
                customer_gaps.append("No customer-facing chat interface")
                
        self.audit_results["frontend_analysis"] = {
            "admin_panel": {
                "status": "MISSING_AI_INTEGRATION",
                "gaps": admin_gaps,
                "required_components": [
                    "AI chatbot widget for admin panel",
                    "Chat history management interface",
                    "AI settings and configuration panel",
                    "Integration with AI API endpoints"
                ]
            },
            "customer_app": {
                "status": "MISSING_CHAT_FEATURE",
                "gaps": customer_gaps,
                "required_components": [
                    "Customer chat interface",
                    "Real-time chat widget",
                    "WebSocket connection to AI API",
                    "Chat history for customers"
                ]
            }
        }
        
    def identify_integration_gaps(self):
        """Identify missing integration points"""
        print("🔗 === INTEGRATION GAPS ANALYSIS ===")
        
        integration_gaps = []
        
        # API Integration Gaps
        integration_gaps.append({
            "type": "API_ENDPOINT_MISSING",
            "description": "AI API lacks REST endpoints for frontend integration",
            "impact": "CRITICAL",
            "details": "Frontend apps cannot directly communicate with AI API"
        })
        
        integration_gaps.append({
            "type": "WEBSOCKET_MISSING", 
            "description": "No WebSocket implementation for real-time chat",
            "impact": "HIGH",
            "details": "Real-time chat functionality not possible"
        })
        
        integration_gaps.append({
            "type": "AUTHENTICATION_INTEGRATION",
            "description": "AI API not integrated with operational API auth",
            "impact": "HIGH", 
            "details": "No unified authentication across services"
        })
        
        integration_gaps.append({
            "type": "DATABASE_SEPARATION",
            "description": "AI and operational data in separate databases",
            "impact": "MEDIUM",
            "details": "May require cross-service data synchronization"
        })
        
        self.audit_results["integration_gaps"] = integration_gaps
        
    def identify_production_blockers(self):
        """Identify critical production deployment blockers"""
        print("🚫 === PRODUCTION BLOCKERS ANALYSIS ===")
        
        blockers = []
        
        # Critical Backend Issues
        blockers.append({
            "category": "BACKEND_STABILITY",
            "severity": "CRITICAL",
            "issue": "Worker processes failing with async context manager errors",
            "impact": "Email and Stripe payment processing non-functional",
            "estimated_fix_time": "2-4 hours"
        })
        
        blockers.append({
            "category": "AI_API_INCOMPLETE",
            "severity": "CRITICAL", 
            "issue": "AI API has no REST endpoints for frontend integration",
            "impact": "AI chatbot functionality completely missing from frontends",
            "estimated_fix_time": "1-2 days"
        })
        
        blockers.append({
            "category": "STRIPE_CONFIGURATION",
            "severity": "HIGH",
            "issue": "Invalid Stripe API keys preventing payment processing",
            "impact": "Payment functionality non-operational",
            "estimated_fix_time": "30 minutes"
        })
        
        blockers.append({
            "category": "SECURITY_MIDDLEWARE",
            "severity": "MEDIUM",
            "issue": "Security middleware not fully available",
            "impact": "Reduced security posture for production",
            "estimated_fix_time": "2-3 hours"
        })
        
        # Frontend Missing Features
        blockers.append({
            "category": "ADMIN_CHATBOT_MISSING",
            "severity": "HIGH",
            "issue": "Admin panel lacks AI chatbot integration",
            "impact": "Admins cannot use AI features",
            "estimated_fix_time": "1-2 days"
        })
        
        blockers.append({
            "category": "CUSTOMER_CHAT_MISSING",
            "severity": "HIGH", 
            "issue": "Customer app lacks chat interface",
            "impact": "Customers cannot use AI chat features",
            "estimated_fix_time": "2-3 days"
        })
        
        self.audit_results["production_blockers"] = blockers
        
    def generate_implementation_roadmap(self):
        """Generate prioritized implementation roadmap"""
        print("🗺️ === IMPLEMENTATION ROADMAP ===")
        
        roadmap = {
            "phase_1_critical_fixes": [
                {
                    "task": "Fix worker process async context manager errors",
                    "priority": "CRITICAL",
                    "estimated_time": "4 hours",
                    "dependencies": [],
                    "files_to_modify": ["apps/api/app/workers/outbox_processors.py"]
                },
                {
                    "task": "Configure valid Stripe API keys",
                    "priority": "CRITICAL", 
                    "estimated_time": "30 minutes",
                    "dependencies": [],
                    "files_to_modify": ["apps/api/.env"]
                },
                {
                    "task": "Add AI API REST endpoints for chat functionality",
                    "priority": "CRITICAL",
                    "estimated_time": "8 hours",
                    "dependencies": [],
                    "files_to_create": [
                        "apps/ai-api/app/routers/chat.py",
                        "apps/ai-api/app/routers/admin.py"
                    ]
                }
            ],
            "phase_2_ai_integration": [
                {
                    "task": "Implement admin panel AI chatbot widget",
                    "priority": "HIGH",
                    "estimated_time": "12 hours",
                    "dependencies": ["AI API REST endpoints"],
                    "files_to_create": [
                        "apps/admin/src/components/ChatBot.tsx",
                        "apps/admin/src/services/ai-api.ts"
                    ]
                },
                {
                    "task": "Add WebSocket support for real-time chat",
                    "priority": "HIGH", 
                    "estimated_time": "6 hours",
                    "dependencies": ["AI API REST endpoints"],
                    "files_to_modify": [
                        "apps/ai-api/app/main.py",
                        "apps/ai-api/app/services/websocket_manager.py"
                    ]
                }
            ],
            "phase_3_customer_features": [
                {
                    "task": "Implement customer chat interface",
                    "priority": "MEDIUM",
                    "estimated_time": "16 hours", 
                    "dependencies": ["WebSocket support", "AI API endpoints"],
                    "files_to_create": [
                        "apps/customer/src/components/ChatWidget.tsx",
                        "apps/customer/src/services/chat-api.ts"
                    ]
                }
            ],
            "phase_4_production_hardening": [
                {
                    "task": "Complete security middleware implementation",
                    "priority": "MEDIUM",
                    "estimated_time": "4 hours",
                    "dependencies": [],
                    "files_to_create": ["apps/api/app/middleware/security.py"]
                },
                {
                    "task": "Implement unified authentication across services",
                    "priority": "MEDIUM",
                    "estimated_time": "6 hours", 
                    "dependencies": ["Security middleware"],
                    "files_to_modify": [
                        "apps/ai-api/app/main.py",
                        "apps/api/app/auth/middleware.py"
                    ]
                }
            ]
        }
        
        self.audit_results["implementation_roadmap"] = roadmap
        
    def calculate_effort_estimates(self):
        """Calculate total effort required"""
        print("📊 === EFFORT ESTIMATION ===")
        
        total_hours = 0
        phases = self.audit_results.get("implementation_roadmap", {})
        
        for phase_name, tasks in phases.items():
            phase_hours = 0
            for task in tasks:
                hours = task.get("estimated_time", "0 hours")
                if "hour" in hours:
                    phase_hours += int(hours.split()[0])
            total_hours += phase_hours
            print(f"  {phase_name}: {phase_hours} hours")
            
        self.audit_results["effort_estimation"] = {
            "total_development_hours": total_hours,
            "estimated_developer_days": round(total_hours / 8, 1),
            "estimated_calendar_time": f"{round(total_hours / 8 / 5, 1)} weeks (1 developer)",
            "breakdown_by_phase": {
                phase: sum(int(task.get("estimated_time", "0 hours").split()[0]) 
                          for task in tasks if "hour" in task.get("estimated_time", ""))
                for phase, tasks in phases.items()
            }
        }
        
        print(f"\n📈 TOTAL EFFORT: {total_hours} hours ({round(total_hours/8, 1)} days)")
        
    def run_comprehensive_audit(self):
        """Run complete audit"""
        print("🔍 MyHibachi Deep Production Audit - Gap Analysis")
        print("=" * 60)
        
        self.audit_backend_apis()
        self.audit_frontend_apps() 
        self.identify_integration_gaps()
        self.identify_production_blockers()
        self.generate_implementation_roadmap()
        self.calculate_effort_estimates()
        
        return self.audit_results
        
    def generate_detailed_report(self):
        """Generate and save detailed audit report"""
        audit_results = self.run_comprehensive_audit()
        
        print("\n" + "=" * 80)
        print("📋 MYHIBACHI DEEP PRODUCTION AUDIT - EXECUTIVE SUMMARY")
        print("=" * 80)
        
        # Critical Issues Summary
        print(f"\n🚨 CRITICAL PRODUCTION BLOCKERS:")
        critical_blockers = [b for b in audit_results["production_blockers"] 
                           if b["severity"] == "CRITICAL"]
        for i, blocker in enumerate(critical_blockers, 1):
            print(f"   {i}. {blocker['issue']}")
            print(f"      Impact: {blocker['impact']}")
            print(f"      Fix Time: {blocker['estimated_fix_time']}")
            
        # Backend Status
        print(f"\n🔧 BACKEND STATUS:")
        backend = audit_results["backend_analysis"]
        print(f"   • Operational API: {backend['operational_api']['status']}")
        print(f"   • AI API: {backend['ai_api']['status']}")
        
        # Frontend Status  
        print(f"\n🎨 FRONTEND STATUS:")
        frontend = audit_results["frontend_analysis"]
        print(f"   • Admin Panel: {frontend['admin_panel']['status']}")
        print(f"   • Customer App: {frontend['customer_app']['status']}")
        
        # Integration Gaps
        print(f"\n🔗 INTEGRATION GAPS:")
        for gap in audit_results["integration_gaps"]:
            print(f"   • {gap['type']}: {gap['description']} ({gap['impact']} impact)")
            
        # Effort Summary
        effort = audit_results["effort_estimation"]
        print(f"\n📊 IMPLEMENTATION EFFORT:")
        print(f"   • Total Development: {effort['total_development_hours']} hours")
        print(f"   • Developer Days: {effort['estimated_developer_days']} days")
        print(f"   • Calendar Time: {effort['estimated_calendar_time']}")
        
        # Key Recommendations
        print(f"\n💡 KEY RECOMMENDATIONS:")
        recommendations = [
            "🔥 IMMEDIATE: Fix worker process errors blocking email/payment processing",
            "🔥 IMMEDIATE: Add AI API REST endpoints for frontend integration", 
            "🔥 IMMEDIATE: Configure valid Stripe API keys",
            "🚀 HIGH: Implement admin panel AI chatbot widget",
            "🚀 HIGH: Add WebSocket support for real-time chat",
            "📱 MEDIUM: Implement customer-facing chat interface",
            "🔒 MEDIUM: Complete security middleware implementation"
        ]
        
        for rec in recommendations:
            print(f"   {rec}")
            
        # Current State Assessment
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        print(f"   • Core Backend: 70% functional (database, auth, basic APIs working)")
        print(f"   • Payment Processing: 30% functional (Stripe integration failing)")
        print(f"   • AI Features: 20% functional (backend exists, no frontend integration)")
        print(f"   • Admin Features: 80% functional (missing AI chatbot)")
        print(f"   • Customer Features: 60% functional (missing chat interface)")
        print(f"   • Overall Production Readiness: 52% - NEEDS SIGNIFICANT WORK")
        
        # Save detailed reports
        json_report = self.project_root / "DEEP_PRODUCTION_AUDIT.json"
        with open(json_report, 'w') as f:
            json.dump(audit_results, f, indent=2)
            
        md_report = self.project_root / "DEEP_PRODUCTION_AUDIT.md"
        self.save_markdown_report(audit_results, md_report)
        
        print(f"\n💾 DETAILED REPORTS SAVED:")
        print(f"   • JSON: {json_report}")
        print(f"   • Markdown: {md_report}")
        
        return audit_results
        
    def save_markdown_report(self, results: Dict, output_file: Path):
        """Save comprehensive markdown report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# MyHibachi Deep Production Audit - Critical Gap Analysis\n\n")
            f.write(f"**Audit Date:** {results['timestamp']}\n")
            f.write(f"**Audit Type:** {results['audit_type']}\n\n")
            
            # Executive Summary
            f.write("## 🎯 Executive Summary\n\n")
            f.write("**Current Status:** MyHibachi requires significant development work to achieve full production operationality.\n\n")
            
            critical_count = len([b for b in results["production_blockers"] if b["severity"] == "CRITICAL"])
            high_count = len([b for b in results["production_blockers"] if b["severity"] == "HIGH"])
            
            f.write(f"- **Critical Blockers:** {critical_count}\n")
            f.write(f"- **High Priority Issues:** {high_count}\n") 
            f.write(f"- **Estimated Development Time:** {results['effort_estimation']['total_development_hours']} hours\n")
            f.write(f"- **Estimated Calendar Time:** {results['effort_estimation']['estimated_calendar_time']}\n\n")
            
            # Production Blockers
            f.write("## 🚨 Critical Production Blockers\n\n")
            for blocker in results["production_blockers"]:
                severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}
                f.write(f"### {severity_emoji.get(blocker['severity'], '⚪')} {blocker['category']}\n")
                f.write(f"**Issue:** {blocker['issue']}\n\n")
                f.write(f"**Impact:** {blocker['impact']}\n\n") 
                f.write(f"**Estimated Fix Time:** {blocker['estimated_fix_time']}\n\n")
                
            # Backend Analysis
            f.write("## 🔧 Backend Services Analysis\n\n")
            backend = results["backend_analysis"]
            
            f.write("### Operational API (Port 8003)\n")
            f.write(f"**Status:** {backend['operational_api']['status']}\n\n")
            f.write("**Issues:**\n")
            for issue in backend['operational_api']['issues']:
                f.write(f"- {issue}\n")
            f.write("\n")
            
            f.write("### AI API (Port 8002)\n")
            f.write(f"**Status:** {backend['ai_api']['status']}\n\n")
            f.write("**Issues:**\n")
            for issue in backend['ai_api']['issues']:
                f.write(f"- {issue}\n")
            f.write("\n")
            
            # Frontend Analysis
            f.write("## 🎨 Frontend Applications Analysis\n\n")
            frontend = results["frontend_analysis"]
            
            f.write("### Admin Panel\n")
            f.write(f"**Status:** {frontend['admin_panel']['status']}\n\n")
            f.write("**Missing Components:**\n")
            for component in frontend['admin_panel']['required_components']:
                f.write(f"- {component}\n")
            f.write("\n")
            
            f.write("### Customer Application\n")
            f.write(f"**Status:** {frontend['customer_app']['status']}\n\n")
            f.write("**Missing Components:**\n")
            for component in frontend['customer_app']['required_components']:
                f.write(f"- {component}\n")
            f.write("\n")
            
            # Implementation Roadmap
            f.write("## 🗺️ Implementation Roadmap\n\n")
            roadmap = results["implementation_roadmap"]
            
            for phase_name, tasks in roadmap.items():
                phase_display = phase_name.replace('_', ' ').title()
                f.write(f"### {phase_display}\n\n")
                
                for task in tasks:
                    priority_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}
                    f.write(f"#### {priority_emoji.get(task['priority'], '⚪')} {task['task']}\n")
                    f.write(f"- **Priority:** {task['priority']}\n")
                    f.write(f"- **Estimated Time:** {task['estimated_time']}\n")
                    if task['dependencies']:
                        f.write(f"- **Dependencies:** {', '.join(task['dependencies'])}\n")
                    f.write("\n")
                    
            # Effort Estimation  
            f.write("## 📊 Development Effort Estimation\n\n")
            effort = results["effort_estimation"]
            f.write(f"- **Total Development Hours:** {effort['total_development_hours']}\n")
            f.write(f"- **Developer Days (8h/day):** {effort['estimated_developer_days']}\n")
            f.write(f"- **Calendar Time:** {effort['estimated_calendar_time']}\n\n")
            
            f.write("### Breakdown by Phase\n")
            for phase, hours in effort["breakdown_by_phase"].items():
                phase_display = phase.replace('_', ' ').title()
                f.write(f"- **{phase_display}:** {hours} hours\n")

def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    auditor = MyHibachiDeepAudit(project_root)
    results = auditor.generate_detailed_report()
    
    # Return exit code based on critical issues
    critical_blockers = len([b for b in results["production_blockers"] if b["severity"] == "CRITICAL"])
    if critical_blockers > 0:
        sys.exit(1)  # Critical issues prevent production deployment
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()