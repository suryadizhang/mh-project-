import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json

def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    format_type: str = "detailed"
) -> None:
    """
    Configure comprehensive logging for production deployment
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_type: Format type ('simple', 'detailed', 'json')
    """
    
    formats = {
        'simple': '%(levelname)s - %(message)s',
        'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]',
        'json': '%(message)s'
    }
    
    config: Dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': formats.get(format_type, formats['detailed'])
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'json' if format_type == 'json' else 'standard',
                'stream': sys.stdout
            }
        },
        'root': {
            'level': level,
            'handlers': ['console']
        },
        'loggers': {
            'uvicorn': {
                'level': level,
                'handlers': ['console'],
                'propagate': False
            },
            'fastapi': {
                'level': level,
                'handlers': ['console'],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            }
        }
    }
    
    # Add file handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': level,
            'formatter': 'json' if format_type == 'json' else 'standard',
            'filename': str(log_path),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
        
        # Add file handler to all loggers
        for logger_config in [config['root']] + list(config['loggers'].values()):
            logger_config['handlers'].append('file')
    
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

# Production-ready logging setup
def setup_production_logging():
    """Setup logging specifically for production environment"""
    setup_logging(
        level="INFO",
        log_file="/var/log/myhibachi/api.log",
        format_type="json"
    )
    
    # Additional production loggers
    error_logger = logging.getLogger('error')
    access_logger = logging.getLogger('access')
    security_logger = logging.getLogger('security')
    
    return {
        'error': error_logger,
        'access': access_logger,
        'security': security_logger
    }