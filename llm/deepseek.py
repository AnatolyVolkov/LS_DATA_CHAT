# llm/deepseek.py (исправленная версия)
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
import json

from config import Config

logger = logging.getLogger(__name__)

class DeepSeekLLM:
    """Wrapper for DeepSeek API using direct HTTP requests"""
    
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.base_url = Config.DEEPSEEK_API_BASE
        self.model = Config.DEEPSEEK_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def invoke(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Invoke DeepSeek model with prompt using HTTP request"""
        try:
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append({
                    "role": "system", 
                    "content": "Ты - аналитик данных сервера лицензий. Отвечай на поставленный вопрос точно и без лишней информации"
                })
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                raise Exception(f"API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    async def ainvoke(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Async invoke - for simplicity, call sync version"""
        return self.invoke(prompt, system_message)