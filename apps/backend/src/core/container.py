"""
Dependency Injection Container
Centralized service registration and dependency management
"""
from typing import Type, TypeVar, Dict, Any, Optional
from functools import lru_cache
from dataclasses import dataclass
import inspect
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class ServiceConfig:
    """Configuration for a registered service"""
    service_class: Type
    singleton: bool = True
    factory_method: Optional[str] = None
    dependencies: Dict[str, str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}

class DependencyInjectionContainer:
    """
    Lightweight dependency injection container
    
    Features:
    - Singleton and transient service lifetimes
    - Automatic dependency resolution
    - Type-safe service retrieval
    - Circular dependency detection
    - Factory method support
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceConfig] = {}
        self._instances: Dict[str, Any] = {}
        self._resolving: set = set()  # Circular dependency detection
        
    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T],
        dependencies: Dict[str, str] = None
    ) -> 'DependencyInjectionContainer':
        """Register a singleton service"""
        service_name = self._get_service_name(interface)
        self._services[service_name] = ServiceConfig(
            service_class=implementation,
            singleton=True,
            dependencies=dependencies or {}
        )
        logger.debug(f"Registered singleton: {service_name} -> {implementation.__name__}")
        return self
    
    def register_transient(
        self,
        interface: Type[T],
        implementation: Type[T],
        dependencies: Dict[str, str] = None
    ) -> 'DependencyInjectionContainer':
        """Register a transient service (new instance each time)"""
        service_name = self._get_service_name(interface)
        self._services[service_name] = ServiceConfig(
            service_class=implementation,
            singleton=False,
            dependencies=dependencies or {}
        )
        logger.debug(f"Registered transient: {service_name} -> {implementation.__name__}")
        return self
    
    def register_factory(
        self,
        interface: Type[T],
        factory_class: Type,
        factory_method: str,
        singleton: bool = True,
        dependencies: Dict[str, str] = None
    ) -> 'DependencyInjectionContainer':
        """Register a service created by a factory method"""
        service_name = self._get_service_name(interface)
        self._services[service_name] = ServiceConfig(
            service_class=factory_class,
            singleton=singleton,
            factory_method=factory_method,
            dependencies=dependencies or {}
        )
        logger.debug(f"Registered factory: {service_name} -> {factory_class.__name__}.{factory_method}")
        return self
    
    def register_instance(
        self,
        interface: Type[T],
        instance: T
    ) -> 'DependencyInjectionContainer':
        """Register a pre-created instance"""
        service_name = self._get_service_name(interface)
        self._instances[service_name] = instance
        logger.debug(f"Registered instance: {service_name}")
        return self
    
    def register_value(self, name: str, value: Any) -> 'DependencyInjectionContainer':
        """Register a pre-created value (configuration, constants, etc.)"""
        self._instances[name] = value
        logger.debug(f"Registered value: {name}")
        return self
    
    def resolve(self, interface_or_name) -> Any:
        """Resolve a service instance by interface type or name"""
        if isinstance(interface_or_name, str):
            # Resolve by name
            service_name = interface_or_name
        else:
            # Resolve by type
            service_name = self._get_service_name(interface_or_name)
        
        # Check for circular dependencies
        if service_name in self._resolving:
            raise ValueError(f"Circular dependency detected for {service_name}")
        
        # Return existing instance if it exists
        if service_name in self._instances:
            return self._instances[service_name]
        
        # Check if service is registered
        if service_name not in self._services:
            raise ValueError(f"Service not registered: {service_name}")
        
        self._resolving.add(service_name)
        try:
            instance = self._create_instance(service_name)
            
            # Cache if singleton
            config = self._services[service_name]
            if config.singleton:
                self._instances[service_name] = instance
            
            return instance
        finally:
            self._resolving.discard(service_name)
    
    def is_registered(self, interface_or_name) -> bool:
        """Check if a service is registered"""
        if isinstance(interface_or_name, str):
            service_name = interface_or_name
        else:
            service_name = self._get_service_name(interface_or_name)
        
        return service_name in self._services or service_name in self._instances
    
    def get_dependency_provider(self, interface: Type[T]):
        """Get a FastAPI dependency provider for the service"""
        def dependency_provider() -> T:
            return self.resolve(interface)
        return dependency_provider
    
    def _create_instance(self, service_name: str) -> Any:
        """Create a new service instance"""
        config = self._services[service_name]
        
        # Resolve dependencies
        resolved_deps = {}
        for dep_name, dep_service in config.dependencies.items():
            if dep_service in self._services:
                # Resolve by service name
                resolved_deps[dep_name] = self.resolve_by_name(dep_service)
            else:
                # Try to resolve as class
                try:
                    dep_class = globals().get(dep_service) or locals().get(dep_service)
                    if dep_class:
                        resolved_deps[dep_name] = self.resolve(dep_class)
                except:
                    raise ValueError(f"Cannot resolve dependency: {dep_service}")
        
        # Create instance
        if config.factory_method:
            # Use factory method
            factory_instance = config.service_class()
            factory_method = getattr(factory_instance, config.factory_method)
            return factory_method(**resolved_deps)
        else:
            # Use constructor
            # Auto-inject constructor parameters
            constructor_params = self._get_constructor_dependencies(
                config.service_class, resolved_deps
            )
            return config.service_class(**constructor_params)
    
    def _get_constructor_dependencies(
        self,
        service_class: Type,
        explicit_deps: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Auto-resolve constructor dependencies"""
        constructor_params = {}
        
        # Get constructor signature
        sig = inspect.signature(service_class.__init__)
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            # Use explicitly provided dependency
            if param_name in explicit_deps:
                constructor_params[param_name] = explicit_deps[param_name]
                continue
            
            # Try to auto-resolve by type annotation
            if param.annotation and param.annotation != inspect.Parameter.empty:
                try:
                    # Try to resolve the parameter type
                    resolved_service = self.resolve(param.annotation)
                    constructor_params[param_name] = resolved_service
                except ValueError:
                    # Can't resolve - check if parameter has default value
                    if param.default == inspect.Parameter.empty:
                        logger.warning(
                            f"Cannot resolve required parameter '{param_name}' "
                            f"of type {param.annotation} for {service_class.__name__}"
                        )
                        # This will likely cause an error when creating the instance
                    
        return constructor_params
    
    def resolve_by_name(self, service_name: str) -> Any:
        """Resolve service by name"""
        if service_name in self._instances:
            return self._instances[service_name]
        
        if service_name not in self._services:
            raise ValueError(f"Service not registered: {service_name}")
        
        return self._create_instance(service_name)
    
    def _get_service_name(self, interface_or_name) -> str:
        """Get service name from interface type or return name if string"""
        if isinstance(interface_or_name, str):
            return interface_or_name
        elif hasattr(interface_or_name, '__module__') and hasattr(interface_or_name, '__name__'):
            return f"{interface_or_name.__module__}.{interface_or_name.__name__}"
        else:
            return str(interface_or_name)
    
    def clear(self):
        """Clear all services and instances"""
        self._services.clear()
        self._instances.clear()
        self._resolving.clear()
    
    def get_registered_services(self) -> Dict[str, ServiceConfig]:
        """Get all registered services (for debugging)"""
        return self._services.copy()
    
    def get_active_instances(self) -> Dict[str, Any]:
        """Get all active instances (for debugging)"""
        return self._instances.copy()

# Global container instance
container = DependencyInjectionContainer()

@lru_cache()
def get_container() -> DependencyInjectionContainer:
    """Get the global container instance"""
    return container

# Convenience decorators for service registration
def singleton(dependencies: Dict[str, str] = None):
    """Decorator to register a class as a singleton service"""
    def decorator(cls):
        container.register_singleton(cls, cls, dependencies)
        return cls
    return decorator

def transient(dependencies: Dict[str, str] = None):
    """Decorator to register a class as a transient service"""
    def decorator(cls):
        container.register_transient(cls, cls, dependencies)
        return cls
    return decorator

def service_factory(factory_method: str, singleton: bool = True, dependencies: Dict[str, str] = None):
    """Decorator to register a factory method"""
    def decorator(cls):
        # This needs the interface to be specified separately
        # Usage: @service_factory("create_service")
        # Then: container.register_factory(IService, MyFactory, "create_service")
        cls._factory_method = factory_method
        cls._factory_singleton = singleton
        cls._factory_dependencies = dependencies or {}
        return cls
    return decorator