# database/connection.py
import pymysql
import sshtunnel
import paramiko
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging
from typing import Optional, Generator
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/main.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DatabaseConnection:
    """Manage SSH tunnel and database connection"""
    
    def __init__(self):
        #self.tunnel = None
        self.local_port = None
        self.engine = None
        
    def connect(self):
        """Establish database connection"""
        try:
            # # Setup SSH tunnel
            # self.tunnel = sshtunnel.SSHTunnelForwarder(
            #     (Config.SSH_HOST, Config.SSH_PORT),
            #     ssh_username=Config.SSH_USERNAME,
            #     ssh_password=Config.SSH_PASSWORD,
            #     ssh_pkey=Config.SSH_PRIVATE_KEY_PATH,
            #     remote_bind_address=(Config.DB_HOST, Config.DB_PORT),
            #     local_bind_address=('localhost', 0)
            # )
            # self.tunnel.start()
            # self.local_port = self.tunnel.local_bind_port
            
            # Create SQLAlchemy engine
            connection_string = f"mysql+pymysql://{Config.DB_USER}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"            
            self.engine = create_engine(
                connection_string,
                poolclass=NullPool,
                connect_args={
                    'connect_timeout': Config.CONNECTION_TIMEOUT,
                    'password':Config.DB_PASSWORD,
                    'charset': 'utf8mb4'
                }
            )
            
            logging.info(f"Database connection established via local port {self.local_port}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to establish connection: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Close connections"""
        if self.engine:
            self.engine.dispose()
        # if self.tunnel:
        #     self.tunnel.stop()
        logging.info("Connections closed")
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        if not self.engine:
            raise Exception("Not connected to database")
        
        
        connection = self.engine.connect()        
        try:
            yield connection
        finally:
            connection.close()
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def execute_query(self, query: str, params: dict = None):
        """Execute SELECT query with retry logic"""
        if not query.strip().upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        with self.get_connection() as conn:            
            result = conn.execute(text(query), params or {})
            return result.fetchall()

# Singleton instance
db_connection = DatabaseConnection()