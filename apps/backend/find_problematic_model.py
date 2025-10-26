"""Find the specific model causing CallableSchema error"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

import logging
logging.basicConfig(level=logging.ERROR)

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema
import importlib
import pkgutil

def test_model_schema(model_class):
    """Test if a model can generate a JSON schema"""
    try:
        models_json_schema([(model_class, 'validation')], title='Test')
        return True, None
    except Exception as e:
        return False, str(e)

def find_pydantic_models(package_name):
    """Find all Pydantic BaseModel subclasses in a package"""
    models = []
    try:
        package = importlib.import_module(package_name)
        
        # Get all classes in the module
        for name in dir(package):
            obj = getattr(package, name)
            if isinstance(obj, type) and issubclass(obj, BaseModel) and obj != BaseModel:
                models.append((f"{package_name}.{name}", obj))
                
    except Exception as e:
        pass
        
    return models

print("Searching for problematic Pydantic models...")
print("=" * 80)

# List of modules to check
modules_to_check = [
    'core.dtos',
    'api.v1.endpoints.health',
    'api.v1.inbox.schemas',
    'api.ai.endpoints.schemas',
    'api.app.cqrs.base',
    'api.app.cqrs.crm_operations',
    'api.app.cqrs.social_commands',
    'api.app.cqrs.social_queries',
    'api.ai.endpoints.routers.v1.unified_chat',
]

problematic_models = []

for module_name in modules_to_check:
    print(f"\nChecking module: {module_name}")
    models = find_pydantic_models(module_name)
    
    for model_path, model_class in models:
        success, error = test_model_schema(model_class)
        if not success:
            print(f"  [FAIL] {model_class.__name__}: {error}")
            problematic_models.append((model_class.__name__, model_path, error))
        else:
            print(f"  [OK] {model_class.__name__}")

print("\n" + "=" * 80)
if problematic_models:
    print(f"\nFound {len(problematic_models)} problematic models:")
    for name, path, error in problematic_models:
        print(f"  - {name} ({path})")
        print(f"    Error: {error[:100]}...")
else:
    print("\n[SUCCESS] All tested models can generate JSON schemas!")
    print("\nThe issue might be:")
    print("  1. A model in a different module")
    print("  2. A response_model reference that doesn't exist")
    print("  3. An endpoint definition issue")
