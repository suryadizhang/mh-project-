"""
Service Registration and Configuration
Configures all services and repositories in the dependency injection container
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    # Try relative imports first
    from .container import DependencyInjectionContainer
    from ..repositories.booking_repository import BookingRepository
    from ..repositories.customer_repository import CustomerRepository
except ImportError:
    # Fall back to absolute imports for validation script
    from core.container import DependencyInjectionContainer
    from repositories.booking_repository import BookingRepository
    from repositories.customer_repository import CustomerRepository

class ServiceRegistry:
    """
    Centralized service registration for the dependency injection container
    
    Features:
    - Database session management
    - Repository registration
    - Service configuration
    - Environment-specific settings
    """
    
    def __init__(self, container: DependencyInjectionContainer):
        self.container = container
        self._database_url: Optional[str] = None
        self._session_factory: Optional[sessionmaker] = None
    
    def configure_database(self, database_url: str, **engine_kwargs) -> 'ServiceRegistry':
        """Configure database connection"""
        self._database_url = database_url
        
        # Create engine with default settings
        engine_config = {
            "echo": False,
            "pool_pre_ping": True,
            "pool_recycle": 300,
            **engine_kwargs
        }
        
        engine = create_engine(database_url, **engine_config)
        self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Register session factory
        self.container.register_factory("database_session_factory", lambda: self._session_factory)
        self.container.register_factory("database_session", self._create_database_session)
        
        return self
    
    def _create_database_session(self) -> Session:
        """Create a new database session"""
        if not self._session_factory:
            raise RuntimeError("Database not configured. Call configure_database() first.")
        
        return self._session_factory()
    
    def register_repositories(self) -> 'ServiceRegistry':
        """Register all repository implementations"""
        # Register repositories with session dependency
        self.container.register_transient(
            "booking_repository",
            BookingRepository,
            dependencies={"session": "database_session"}
        )
        
        self.container.register_transient(
            "customer_repository", 
            CustomerRepository,
            dependencies={"session": "database_session"}
        )
        
        return self
    
    def register_services(self) -> 'ServiceRegistry':
        """Register business services"""
        # Register core services (these would be implemented later)
        
        # Example service registrations:
        # self.container.register_singleton(
        #     "booking_service",
        #     BookingService,
        #     dependencies={
        #         "booking_repo": "booking_repository",
        #         "customer_repo": "customer_repository"
        #     }
        # )
        
        # self.container.register_singleton(
        #     "notification_service",
        #     NotificationService,
        #     dependencies={"config": "notification_config"}
        # )
        
        return self
    
    def register_external_services(self) -> 'ServiceRegistry':
        """Register external service integrations"""
        # Register external service configurations
        
        # Example configurations:
        # self.container.register_singleton(
        #     "stripe_config", 
        #     lambda: StripeConfig(api_key=os.getenv("STRIPE_SECRET_KEY"))
        # )
        
        # self.container.register_singleton(
        #     "ringcentral_config",
        #     lambda: RingCentralConfig(
        #         client_id=os.getenv("RINGCENTRAL_CLIENT_ID"),
        #         client_secret=os.getenv("RINGCENTRAL_CLIENT_SECRET")
        #     )
        # )
        
        return self
    
    def register_middleware(self) -> 'ServiceRegistry':
        """Register middleware components"""
        # Register authentication and authorization services
        
        # Example middleware registrations:
        # self.container.register_singleton(
        #     "auth_service",
        #     AuthenticationService,
        #     dependencies={"jwt_config": "jwt_config"}
        # )
        
        # self.container.register_singleton(
        #     "rate_limit_service",
        #     RateLimitService,
        #     dependencies={"redis_client": "redis_client"}
        # )
        
        return self
    
    def register_configuration(self, config: Dict[str, Any]) -> 'ServiceRegistry':
        """Register application configuration"""
        # Register individual config sections
        for key, value in config.items():
            self.container.register_value(f"config_{key}", value)
        
        # Register full config
        self.container.register_value("app_config", config)
        
        return self
    
    def validate_registrations(self) -> bool:
        """Validate that all required services are registered"""
        required_services = [
            "database_session",
            "booking_repository",
            "customer_repository"
        ]
        
        missing_services = []
        for service_name in required_services:
            try:
                self.container.resolve(service_name)
            except Exception:
                missing_services.append(service_name)
        
        if missing_services:
            raise RuntimeError(
                f"Missing required service registrations: {', '.join(missing_services)}"
            )
        
        return True

def create_service_container(
    database_url: str,
    app_config: Optional[Dict[str, Any]] = None
) -> DependencyInjectionContainer:
    """
    Factory function to create and configure the service container
    
    Args:
        database_url: Database connection string
        app_config: Application configuration dictionary
        
    Returns:
        Configured dependency injection container
    """
    # Create container
    container = DependencyInjectionContainer()
    
    # Create registry
    registry = ServiceRegistry(container)
    
    # Configure services
    registry.configure_database(database_url)
    registry.register_repositories()
    registry.register_services()
    registry.register_external_services()
    registry.register_middleware()
    
    # Register configuration if provided
    if app_config:
        registry.register_configuration(app_config)
    
    # Validate setup
    registry.validate_registrations()
    
    return container

# FastAPI Integration

class ContainerMiddleware:
    """
    Middleware to inject the DI container into FastAPI request context
    """
    
    def __init__(self, container: DependencyInjectionContainer):
        self.container = container
    
    async def __call__(self, request, call_next):
        """Add container to request state"""
        request.state.container = self.container
        response = await call_next(request)
        return response

def get_container():
    """
    FastAPI dependency to get the DI container from request state
    This should be used in FastAPI endpoints to access services
    """
    from fastapi import Request
    
    def _get_container(request: Request) -> DependencyInjectionContainer:
        if not hasattr(request.state, 'container'):
            raise RuntimeError("DI container not found in request state")
        return request.state.container
    
    return _get_container

# Convenience functions for common dependencies

def get_booking_repository():
    """FastAPI dependency to get booking repository"""
    def _get_repo(container: DependencyInjectionContainer = get_container()):
        return container.resolve("booking_repository")
    return _get_repo

def get_customer_repository():
    """FastAPI dependency to get customer repository"""
    def _get_repo(container: DependencyInjectionContainer = get_container()):
        return container.resolve("customer_repository")
    return _get_repo

def get_database_session():
    """FastAPI dependency to get database session"""
    def _get_session(container: DependencyInjectionContainer = get_container()):
        return container.resolve("database_session")
    return _get_session

# Service locator pattern (for backwards compatibility)

_global_container: Optional[DependencyInjectionContainer] = None

def set_global_container(container: DependencyInjectionContainer):
    """Set the global container instance"""
    global _global_container
    _global_container = container

def get_global_container() -> DependencyInjectionContainer:
    """Get the global container instance"""
    if _global_container is None:
        raise RuntimeError("Global container not set. Call set_global_container() first.")
    return _global_container

def resolve_service(service_name: str):
    """Resolve a service from the global container"""
    return get_global_container().resolve(service_name)