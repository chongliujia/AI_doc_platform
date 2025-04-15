from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class AIProvider(ABC):
    """
    AI服务提供者接口，定义了所有AI服务必须实现的方法
    """
    
    @abstractmethod
    async def generate_completion(self, messages: List[Dict[str, str]], 
                                 temperature: float = 0.7, 
                                 max_tokens: int = 2000) -> Optional[str]:
        """
        生成文本完成
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制随机性
            max_tokens: 生成的最大token数
            
        Returns:
            生成的文本，如果请求失败则返回None
        """
        pass
    
    @abstractmethod
    async def generate_document_outline(self, topic: str, doc_type: str, 
                                      additional_info: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        生成文档大纲
        
        Args:
            topic: 文档主题
            doc_type: 文档类型 (ppt, word, pdf)
            additional_info: 额外的信息或要求
            
        Returns:
            文档大纲，如果生成失败则返回None
        """
        pass
    
    @abstractmethod
    async def generate_section_content(self, topic: str, section_title: str, 
                                     doc_type: str, 
                                     additional_info: Optional[str] = None) -> Optional[str]:
        """
        生成文档章节内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            doc_type: 文档类型 (ppt, word, pdf)
            additional_info: 额外的信息或要求
            
        Returns:
            章节内容，如果生成失败则返回None
        """
        pass 