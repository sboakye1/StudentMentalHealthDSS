"""
Database package for the Student Mental Health DSS application.

Provides database connection management and utilities.
"""

from database.connection import (
    get_connection,
    get_database_config,
    check_database_health,
    close_connection,
)

__all__ = [
    "get_connection",
    "get_database_config",
    "check_database_health",
    "close_connection",
]
