"""
Quick Production Readiness Assessment for MyHibachi
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

def check_api_structure():
    """Check API structure and files"""
    results = {}
    
    # Operational API
    operational_api_path = Path("apps/api")
    if operational_api_path.exists():
        results["operational_api"] = {
            "main_file": (operational_api_path / "app" / "main.py").exists(),
            "requirements": (operational_api_path / "requirements.txt").exists(),
            "dockerfile": (operational_api_path / "Dockerfile").exists(),
            "alembic": (operational_api_path / "alembic.ini").exists(),
            "models": (operational_api_path / "app" / "models").exists(),
            "routers": (operational_api_path / "app" / "routers").exists(),
            "crm": (operational_api_path / "app" / "crm").exists()
        }
    
    # AI API
    ai_api_path = Path("apps/ai-api")
    if ai_api_path.exists():
        results["ai_api"] = {
            "main_file": (ai_api_path / "app" / "main.py").exists(),
            "requirements": (ai_api_path / "requirements.txt").exists(),
            "dockerfile": (ai_api_path / "Dockerfile").exists(),
            "models": (ai_api_path / "app" / "models.py").exists(),
            "services": (ai_api_path / "app" / "services").exists(),
            "routers": (ai_api_path / "app" / "routers").exists()
        }
    
    return results

def check_frontend_structure():
    """Check frontend structure"""
    results = {}
    
    admin_path = Path("apps/admin")
    if admin_path.exists():
        results["admin_panel"] = {
            "package_json": (admin_path / "package.json").exists(),
            "next_config": (admin_path / "next.config.js").exists(),
            "env_local": (admin_path / ".env.local").exists(),
            "src_directory": (admin_path / "src").exists(),
            "pages": (admin_path / "src" / "app").exists(),
            "components": (admin_path / "src" / "components").exists(),
            "api_client": (admin_path / "src" / "services" / "api.ts").exists()
        }
    
    return results

def check_fastapi_documentation():
    """Check FastAPI documentation configuration"""
    results = {}
    
    # Check operational API main.py for docs configuration
    operational_main = Path("apps/api/app/main.py")
    if operational_main.exists():
        with open(operational_main, 'r') as f:
            content = f.read()
            results["operational_api_docs"] = {
                "fastapi_app": "FastAPI(" in content,
                "docs_url": "docs_url" in content,
                "redoc_url": "redoc_url" in content,
                "title": "title=" in content,
                "description": "description=" in content,
                "version": "version=" in content
            }
    
    # Check AI API main.py for docs configuration
    ai_main = Path("apps/ai-api/app/main.py")
    if ai_main.exists():
        with open(ai_main, 'r') as f:
            content = f.read()
            results["ai_api_docs"] = {
                "fastapi_app": "FastAPI(" in content,
                "docs_url": "docs_url" in content,
                "redoc_url": "redoc_url" in content,
                "title": "title=" in content,
                "description": "description=" in content,
                "version": "version=" in content
            }
    
    return results

def check_environment_setup():
    """Check environment configuration"""
    results = {}
    
    # Check for environment files
    env_files = [
        "apps/api/.env",
        "apps/api/.env.example", 
        "apps/ai-api/.env",
        "apps/ai-api/.env.example",
        "apps/admin/.env.local",
        "apps/admin/.env.example"
    ]
    
    for env_file in env_files:
        env_path = Path(env_file)
        results[env_file] = env_path.exists()
        
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    content = f.read()
                    results[f"{env_file}_content"] = {
                        "has_database_url": "DATABASE_URL" in content,
                        "has_openai_key": "OPENAI_API_KEY" in content,
                        "has_stripe_key": "STRIPE" in content,
                        "has_jwt_secret": "JWT_SECRET" in content,
                        "has_placeholder_values": "your_" in content.lower() or "sk_test_" in content
                    }
            except:
                results[f"{env_file}_content"] = "ERROR_READING"
    
    return results

def check_docker_setup():
    """Check Docker configuration"""
    results = {}
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml",
        ".dockerignore",
        "apps/api/Dockerfile",
        "apps/ai-api/Dockerfile", 
        "apps/admin/Dockerfile"
    ]
    
    for docker_file in docker_files:
        docker_path = Path(docker_file)
        results[docker_file] = docker_path.exists()
    
    return results

def check_database_setup():
    """Check database configuration"""
    results = {}
    
    # Operational API database
    api_alembic = Path("apps/api/alembic")
    if api_alembic.exists():
        migrations = list((api_alembic / "versions").glob("*.py")) if (api_alembic / "versions").exists() else []
        results["operational_db"] = {
            "alembic_directory": True,
            "alembic_ini": Path("apps/api/alembic.ini").exists(),
            "migrations_count": len(migrations),
            "models_directory": Path("apps/api/app/models").exists()
        }
    
    # AI API database
    ai_db = Path("apps/ai-api/ai_chat.db")
    results["ai_db"] = {
        "sqlite_file": ai_db.exists(),
        "sqlite_size": ai_db.stat().st_size if ai_db.exists() else 0,
        "models_file": Path("apps/ai-api/app/models.py").exists()
    }
    
    return results

def generate_recommendations(results):
    """Generate recommendations based on checks"""
    recommendations = []
    
    # API Structure recommendations
    for api_name, api_data in results.get("api_structure", {}).items():
        missing_files = [k for k, v in api_data.items() if not v]
        if missing_files:
            recommendations.append(f"Missing files in {api_name}: {', '.join(missing_files)}")
    
    # Documentation recommendations
    for api_name, docs_data in results.get("documentation", {}).items():
        missing_docs = [k for k, v in docs_data.items() if not v]
        if missing_docs:
            recommendations.append(f"Missing documentation config in {api_name}: {', '.join(missing_docs)}")
    
    # Environment recommendations
    env_issues = []
    for env_file, exists in results.get("environment", {}).items():
        if not exists and not env_file.endswith("_content"):
            env_issues.append(env_file)
    if env_issues:
        recommendations.append(f"Missing environment files: {', '.join(env_issues)}")
    
    # Docker recommendations
    docker_issues = [k for k, v in results.get("docker", {}).items() if not v]
    if docker_issues:
        recommendations.append(f"Missing Docker files: {', '.join(docker_issues)}")
    
    # General production recommendations
    recommendations.extend([
        "Start both APIs (operational on 8003, AI on 8002) and test Swagger docs at /docs",
        "Test all frontend functionality against backend APIs",
        "Set up proper environment variables with real values (not placeholders)",
        "Configure SSL certificates for production",
        "Set up monitoring and logging",
        "Implement automated testing pipeline",
        "Configure database backups",
        "Set up CI/CD pipeline"
    ])
    
    return recommendations

def main():
    """Run production readiness check"""
    print("🔍 Running Production Readiness Check for MyHibachi...")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "api_structure": check_api_structure(),
        "frontend_structure": check_frontend_structure(),
        "documentation": check_fastapi_documentation(),
        "environment": check_environment_setup(),
        "docker": check_docker_setup(),
        "database": check_database_setup()
    }
    
    # Generate recommendations
    recommendations = generate_recommendations(results)
    results["recommendations"] = recommendations
    
    # Calculate overall status
    api_ready = all(
        all(api_data.values()) 
        for api_data in results["api_structure"].values()
    )
    
    docs_ready = all(
        all(docs_data.values()) 
        for docs_data in results["documentation"].values()
    )
    
    if api_ready and docs_ready:
        results["overall_status"] = "READY_FOR_TESTING"
    else:
        results["overall_status"] = "NEEDS_SETUP"
    
    # Print summary
    print(f"📊 Overall Status: {results['overall_status']}")
    print()
    
    print("🔌 API Structure:")
    for api_name, api_data in results["api_structure"].items():
        status = "✅" if all(api_data.values()) else "❌"
        print(f"  {status} {api_name}")
        for file_name, exists in api_data.items():
            icon = "✅" if exists else "❌"
            print(f"    {icon} {file_name}")
    print()
    
    print("📚 API Documentation:")
    for api_name, docs_data in results["documentation"].items():
        status = "✅" if all(docs_data.values()) else "❌"
        print(f"  {status} {api_name}")
        for config_name, exists in docs_data.items():
            icon = "✅" if exists else "❌"
            print(f"    {icon} {config_name}")
    print()
    
    print("🌍 Environment Setup:")
    for env_file, exists in results["environment"].items():
        if not env_file.endswith("_content"):
            icon = "✅" if exists else "❌"
            print(f"  {icon} {env_file}")
    print()
    
    print("🐳 Docker Setup:")
    for docker_file, exists in results["docker"].items():
        icon = "✅" if exists else "❌"
        print(f"  {icon} {docker_file}")
    print()
    
    print("💡 Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    print()
    
    # Save detailed results
    with open("production_check_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Detailed results saved to: production_check_results.json")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    results = main()