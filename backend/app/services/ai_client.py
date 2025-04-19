import os
import json
import requests
import logging
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from abc import ABC, abstractmethod
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIClient(ABC):
    """
    AI客户端基类，处理与AI API的通信
    """
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None):
        """
        初始化AI客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            api_endpoint: API端点，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.api_endpoint = api_endpoint or os.getenv("AI_API_ENDPOINT", "")
        
        if not self.api_key:
            logger.error("API密钥未设置")
            raise ValueError("API密钥未设置")
        
        logger.info(f"AI客户端初始化完成，API端点: {self.api_endpoint}")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def call_api(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> Optional[Dict[str, Any]]:
        """
        调用AI API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            API响应，如果请求失败则返回None
        """
        try:
            payload = self._prepare_payload(messages, temperature, max_tokens)
            
            # 记录请求信息
            logger.info(f"发送API请求: endpoint={self.api_endpoint}, model={payload.get('model', 'unknown')}")
            logger.info(f"请求参数: temperature={temperature}, max_tokens={max_tokens}")
            logger.info(f"请求消息: {messages[-1]['content'][:100]}..." if messages else "无消息")
            
            # 增加超时时间到180秒
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                timeout=180
            )
            
            logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return None
            
            response_json = response.json()
            
            # 记录响应内容摘要
            if response_json and "choices" in response_json and response_json["choices"]:
                content = response_json["choices"][0].get("message", {}).get("content", "")
                logger.info(f"API响应内容摘要: {content[:150]}..." if content else "无内容")
            
            return response_json
            
        except requests.exceptions.Timeout:
            logger.error("API请求超时，可能需要更长的处理时间")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"API调用出错: {str(e)}")
            return None
    
    @abstractmethod
    def _prepare_payload(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> Dict[str, Any]:
        """
        准备API请求的payload
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            准备好的payload
        """
        pass
    
    def extract_response_content(self, response: Dict[str, Any]) -> Optional[str]:
        """
        从API响应中提取内容
        
        Args:
            response: API响应
            
        Returns:
            提取的内容，如果提取失败则返回None
        """
        try:
            if "choices" in response and response["choices"] and len(response["choices"]) > 0:
                content = response["choices"][0].get("message", {}).get("content", "")
                
                # 记录原始内容
                content_preview = content.replace('\n', ' ')[:100] + "..." if len(content) > 100 else content
                logger.info(f"提取的原始内容: {content_preview}")
                
                # 检查内容是否包含Markdown代码块
                code_blocks = re.findall(r"```(?:json)?[\s\S]*?```", content)
                if code_blocks:
                    logger.info(f"内容包含 {len(code_blocks)} 个代码块")
                    
                return content
            
            logger.warning("响应中未找到有效内容")
            return None
        except Exception as e:
            logger.error(f"提取内容时出错: {str(e)}")
            return None 