import psycopg2
from psycopg2.extras import RealDictCursor
from config import DatabaseConfig
import logging
import re

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.connection = None
    
    def _parse_connection_string(self, connection_string):
        """Parse connection string to extract components"""
        # Remove the driver prefix
        if connection_string.startswith("postgresql+asyncpg://"):
            connection_string = connection_string.replace("postgresql+asyncpg://", "")
        elif connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "")
        
        # Parse the connection string
        pattern = r"([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
        match = re.match(pattern, connection_string)
        
        if match:
            user, password, host, port, database = match.groups()
            return {
                'host': host,
                'port': int(port),
                'database': database,
                'user': user,
                'password': password
            }
        else:
            raise ValueError("Invalid connection string format")
    
    def get_connection(self):
        """Get a database connection"""
        try:
            if self.connection is None or self.connection.closed:
                logger.info("Creating new database connection")
                # Parse connection string to get individual components
                connection_params = self._parse_connection_string(DatabaseConfig.get_sync_connection_string())
                
                self.connection = psycopg2.connect(
                    host=connection_params['host'],
                    port=connection_params['port'],
                    database=connection_params['database'],
                    user=connection_params['user'],
                    password=connection_params['password'],
                    cursor_factory=RealDictCursor
                )
                logger.info("Database connection created successfully")
            else:
                # Test if connection is still valid
                try:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    logger.debug("Database connection is valid")
                except Exception:
                    logger.info("Database connection is invalid, creating new connection")
                    self.connection.close()
                    connection_params = self._parse_connection_string(DatabaseConfig.get_sync_connection_string())
                    self.connection = psycopg2.connect(
                        host=connection_params['host'],
                        port=connection_params['port'],
                        database=connection_params['database'],
                        user=connection_params['user'],
                        password=connection_params['password'],
                        cursor_factory=RealDictCursor
                    )
                    logger.info("New database connection created successfully")
            
            return self.connection
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def close_connection(self):
        """Close the database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            logger.info(f"Executing query: {query[:100]}... with params: {params}")
            cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                logger.info(f"SELECT query returned {len(result)} rows")
                return result
            else:
                connection.commit()
                rowcount = cursor.rowcount
                logger.info(f"Non-SELECT query affected {rowcount} rows")
                return rowcount
        except Exception as e:
            connection.rollback()
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query was: {query}")
            logger.error(f"Params were: {params}")
            raise
        finally:
            cursor.close()

# Global database connection instance
db = DatabaseConnection() 