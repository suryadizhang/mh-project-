"""
Authentication module for MyHibachi API
"""

from .middleware import setup_auth_middleware

__all__ = ["setup_auth_middleware"]