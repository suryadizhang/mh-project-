"""
OpenAPI configuration and documentation setup for MyHibachi API.
"""

from fastapi.openapi.utils import get_openapi
from typing import Dict, Any, Callable


def get_openapi_schema(app) -> Callable[[], Dict[str, Any]]:
    """
    Generate a function that returns comprehensive OpenAPI schema for MyHibachi API.
    """
    def custom_openapi() -> Dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        try:
            openapi_schema = get_openapi(
                title="MyHibachi AI Sales CRM API",
                version="2.0.0",
                description="""
# MyHibachi AI Sales CRM API

A comprehensive hibachi catering booking and management system with AI-powered features.

## Features

- 🎯 **CQRS Architecture**: Command Query Responsibility Segregation for scalability
- 🔐 **OAuth 2.1 + MFA**: Secure authentication with multi-factor authentication
- 🤖 **AI Integration**: AI-powered booking assistance and customer support
- 💳 **Payment Processing**: Stripe integration with multiple payment methods
- 📱 **Multi-channel**: SMS, Email, and WhatsApp notifications
- 📊 **Analytics**: Comprehensive booking and revenue analytics
- 🛡️ **Security**: Field-level encryption, audit logging, and RBAC
- 🚀 **High Performance**: Redis caching, rate limiting, and async processing

## Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Get your token by calling the `/api/auth/login` endpoint with valid credentials.

## Rate Limits

- **Authentication**: 5 requests/minute
- **Booking Operations**: 10 requests/minute  
- **General API**: 100 requests/minute
- **SMS Notifications**: 30 requests/minute

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

## Support

- **Email**: support@myhibachichef.com
- **Phone**: +1 (916) 740-8768
- **Documentation**: https://api.myhibachichef.com/docs
        """.strip(),
                routes=app.routes,
                servers=[
                    {
                        "url": "https://api.myhibachichef.com",
                        "description": "Production server"
                    },
                    {
                        "url": "https://staging-api.myhibachichef.com", 
                        "description": "Staging server"
                    },
                    {
                        "url": "http://localhost:8000",
                        "description": "Development server"
                    }
                ],
                tags=[
                    {
                        "name": "Authentication",
                        "description": "User authentication and authorization endpoints"
                    },
                    {
                        "name": "Bookings",
                        "description": "Hibachi booking management operations"
                    },
                    {
                        "name": "Customers", 
                        "description": "Customer management and CRM operations"
                    },
                    {
                        "name": "Payments",
                        "description": "Payment processing and refund operations"
                    },
                    {
                        "name": "AI Services",
                        "description": "AI-powered booking assistance and automation"
                    },
                    {
                        "name": "Analytics",
                        "description": "Business intelligence and reporting"
                    },
                    {
                        "name": "Notifications",
                        "description": "SMS, email, and push notification services"
                    },
                    {
                        "name": "Health",
                        "description": "System health and monitoring endpoints"
                    },
                    {
                        "name": "Admin",
                        "description": "Administrative operations and system management"
                    }
                ]
            )

            # Add security schemes
            openapi_schema["components"]["securitySchemes"] = {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token obtained from login endpoint"
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for service-to-service authentication"
                }
            }

            # Add global security requirement
            openapi_schema["security"] = [
                {"BearerAuth": []},
                {"ApiKeyAuth": []}
            ]

            # Add contact information
            openapi_schema["info"]["contact"] = {
                "name": "MyHibachi API Support",
                "email": "support@myhibachichef.com",
                "url": "https://myhibachichef.com/contact"
            }

            # Add license information
            openapi_schema["info"]["license"] = {
                "name": "Proprietary",
                "url": "https://myhibachichef.com/terms"
            }

            # Add external documentation
            openapi_schema["externalDocs"] = {
                "description": "MyHibachi Developer Portal",
                "url": "https://developers.myhibachichef.com"
            }

            app.openapi_schema = openapi_schema
            return app.openapi_schema
            
        except Exception as e:
            # Fallback with detailed error logging
            import logging
            import traceback
            import sys
            
            logging.error(f"Failed to generate full OpenAPI schema: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            
            # Try to extract more info about which model failed
            tb = sys.exc_info()[2]
            if tb:
                frame = tb.tb_frame
                while frame:
                    local_vars = frame.f_locals
                    if 'schema' in local_vars or 'model' in local_vars:
                        logging.error(f"Frame locals: {list(local_vars.keys())}")
                    frame = frame.f_back if hasattr(frame, 'f_back') else None
            
            # Return a minimal working schema
            app.openapi_schema = {
                "openapi": "3.1.0",
                "info": {
                    "title": "MyHibachi AI Sales CRM API",
                    "version": "2.0.0",
                    "description": f"API schema generation failed: {str(e)}\n\nCheck server logs for details."
                },
                "paths": {},
                "components": {}
            }
            return app.openapi_schema
    
    return custom_openapi


# Standard response schemas for reuse
STANDARD_RESPONSES = {
    "400": {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "VALIDATION_ERROR"},
                                "message": {"type": "string", "example": "Invalid input data"},
                                "details": {"type": "object"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    "401": {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "AUTHENTICATION_REQUIRED"},
                                "message": {"type": "string", "example": "Authentication required"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    "403": {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "INSUFFICIENT_PERMISSIONS"},
                                "message": {"type": "string", "example": "Insufficient permissions"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    "404": {
        "description": "Not Found",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "RESOURCE_NOT_FOUND"},
                                "message": {"type": "string", "example": "Resource not found"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    "422": {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "VALIDATION_ERROR"},
                                "message": {"type": "string", "example": "Input data validation failed"},
                                "details": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "field": {"type": "string"},
                                            "message": {"type": "string"},
                                            "code": {"type": "string"}
                                        }
                                    }
                                },
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    "429": {
        "description": "Rate Limit Exceeded",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "RATE_LIMIT_EXCEEDED"},
                                "message": {"type": "string", "example": "Too many requests"},
                                "retry_after": {"type": "integer", "example": 60},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    "500": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "INTERNAL_SERVER_ERROR"},
                                "message": {"type": "string", "example": "An internal error occurred"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
}