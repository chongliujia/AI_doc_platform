import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional

from ..core.config import settings

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None):
        """
        初始化OpenAI客户端
        
        Args:
            api_key: API密钥，默认从配置中获取
            api_endpoint: API端点，默认从配置中获取
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.api_endpoint = api_endpoint or settings.OPENAI_API_ENDPOINT
        
        if not self.api_key:
            logger.warning("OpenAI API密钥未配置")
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             temperature: float = 0.7, 
                             max_tokens: int = 2000,
                             model: str = "gpt-4") -> Optional[Dict[str, Any]]:
        """
        调用OpenAI聊天完成API
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制随机性
            max_tokens: 生成的最大token数
            model: 使用的模型，默认为"gpt-4"
            
        Returns:
            API响应，如果请求失败则返回None
        """
        if not self.api_key:
            logger.error("无法调用OpenAI API: 未配置API密钥")
            return None
            
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoint, 
                                       json=payload, 
                                       headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API请求失败: {response.status}, {error_text}")
                        return None
                        
                    result = await response.json()
                    return result
        except Exception as e:
            logger.error(f"OpenAI API请求异常: {str(e)}")
            return None 