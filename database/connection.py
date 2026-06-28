"""
Database connection module for Flask application.

Provides functions to establish MySQL connections and perform health checks.
"""

import mysql.connector
from mysql.connector import Error as MySQLError
import os


def get_database_config():
    """
    Get database configuration from environment variables.

    Returns:
        dict: Database connection parameters
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "student_mental_health_dss"),
        "port": int(os.getenv("DB_PORT", 3306)),
    }


def get_connection():
    """
    Establish a connection to the MySQL database.

    Returns:
        mysql.connector.MySQLConnection: Active database connection

    Raises:
        MySQLError: If connection fails due to MySQL errors
        Exception: If connection fails for other reasons
    """
    try:
        config = get_database_config()
        connection = mysql.connector.connect(**config)

        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"Successfully connected to MySQL Server version {db_info}")
            return connection
    except MySQLError as err:
        if err.errno == 2003:
            raise MySQLError(
                f"Cannot connect to MySQL on {config.get('host')}:{config.get('port')}. "
                "Is MySQL running? Make sure XAMPP MySQL service is started."
            )
        elif err.errno == 1045:
            raise MySQLError(
                f"Access denied for user '{config.get('user')}@{config.get('host')}'. "
                "Check your database credentials in .env file."
            )
        elif err.errno == 1049:
            raise MySQLError(
                f"Database '{config.get('database')}' does not exist. "
                "Create the database first using the instructions in README.md"
            )
        else:
            raise MySQLError(f"Error connecting to MySQL: {err}")
    except Exception as err:
        raise Exception(f"Unexpected error while connecting to database: {err}")


def check_database_health():
    """
    Perform a health check on the database connection.

    Returns:
        dict: Health check result with status and message

    Example:
        {
            'status': 'connected',
            'message': 'Database connection is healthy',
            'database': 'student_mental_health_dss',
            'version': '8.0.27'
        }
    """
    try:
        connection = get_connection()

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            connection.close()

            config = get_database_config()
            return {
                "status": "connected",
                "message": "Database connection is healthy",
                "database": config.get("database"),
                "version": version,
            }
    except MySQLError as err:
        return {
            "status": "error",
            "message": str(err),
        }
    except Exception as err:
        return {
            "status": "error",
            "message": f"Unexpected error during health check: {str(err)}",
        }


def close_connection(connection):
    """
    Close a database connection.

    Args:
        connection: MySQL connection object to close

    Returns:
        bool: True if closed successfully, False otherwise
    """
    if connection and connection.is_connected():
        connection.close()
        return True
    return False
