# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SSH Configuration
    # SSH_HOST = os.getenv('SSH_HOST', 'your-ssh-server.com')
    # SSH_PORT = int(os.getenv('SSH_PORT', '22'))
    # SSH_USERNAME = os.getenv('SSH_USERNAME', 'your-username')
    # SSH_PASSWORD = os.getenv('SSH_PASSWORD', 'your-password')
    # SSH_PRIVATE_KEY_PATH = os.getenv('SSH_PRIVATE_KEY_PATH', None)
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'licencecenter')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your-db-password')
    DB_NAME = os.getenv('DB_NAME', 'licencecenter')
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'your-deepseek-api-key')
    DEEPSEEK_API_BASE = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    
    # App Configuration
    MAX_RETRIES = 3
    CONNECTION_TIMEOUT = 300