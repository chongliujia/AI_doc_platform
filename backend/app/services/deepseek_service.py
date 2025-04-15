import logging
from typing import List, Dict, Any, Optional

from .ai_service_interface import AIServiceInterface
from .deepseek_client import DeepSeekClient
from .outline_generator import OutlineGenerator
from .content_generator import ContentGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekService(AIServiceInterface):
    """
    DeepSeek服务，实现AI服务接口
    这是一个门面类，整合了各个组件的功能
    """
    
    def __init__(self):
        """
        初始化DeepSeek服务
        """
        # 初始化AI客户端
        self.client = DeepSeekClient()
        
        # 初始化大纲生成器
        self.outline_generator = OutlineGenerator(self.client)
        
        # 初始化内容生成器
        self.content_generator = ContentGenerator(self.client)
        
        logger.info("DeepSeek服务初始化完成")
    
    def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """
        生成文本完成
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制随机性
            max_tokens: 生成的最大token数
            
        Returns:
            生成的文本，如果请求失败则返回None
        """
        try:
            # 调用AI客户端
            response = self.client.call_api(messages, temperature, max_tokens)
            if not response:
                return None
            
            # 提取内容
            return self.client.extract_response_content(response)
            
        except Exception as e:
            logger.error(f"生成文本完成时出错: {str(e)}")
            return None
    
    def call_api(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> Optional[Dict[str, Any]]:
        """
        调用AI API
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制随机性
            max_tokens: 生成的最大token数
            
        Returns:
            API响应，如果请求失败则返回None
        """
        try:
            return self.client.call_api(messages, temperature, max_tokens)
        except Exception as e:
            logger.error(f"调用API时出错: {str(e)}")
            return None
    
    def generate_document_outline(self, topic: str, doc_type: str) -> Optional[List[Dict[str, Any]]]:
        """
        生成文档大纲
        
        Args:
            topic: 文档主题
            doc_type: 文档类型 (ppt, word, pdf)
            
        Returns:
            文档大纲，如果生成失败则返回None
        """
        return self.outline_generator.generate_document_outline(topic, doc_type)
    
    def generate_section_content(self, topic: str, section_title: str, doc_type: str) -> str:
        """
        生成文档章节内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            doc_type: 文档类型 (ppt, word, pdf)
            
        Returns:
            章节内容
        """
        return self.content_generator.generate_section_content(topic, section_title, doc_type)
    
    def generate_slide_content(self, topic: str, section_title: str, slide_title: str, slide_type: str) -> Dict[str, Any]:
        """
        生成幻灯片内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            slide_title: 幻灯片标题
            slide_type: 幻灯片类型 (content, two_column, image_content)
            
        Returns:
            幻灯片内容
        """
        return self.content_generator.generate_slide_content(topic, section_title, slide_title, slide_type)