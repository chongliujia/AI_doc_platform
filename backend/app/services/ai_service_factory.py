import logging
from typing import Dict, Any, Optional

from .ai_service_interface import AIServiceInterface
from .deepseek_service import DeepSeekService
from .image_service import ImageService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIServiceFactory:
    """
    AI服务工厂，用于创建不同的AI服务实例
    """
    
    # 支持的AI服务类型
    SUPPORTED_SERVICES = {
        "deepseek": DeepSeekService,
        # 未来可以添加更多服务，如：
        # "openai": OpenAIService,
        # "anthropic": AnthropicService,
    }
    
    @classmethod
    def create_service(cls, service_type: str = "deepseek", **kwargs) -> AIServiceInterface:
        """
        创建AI服务实例
        
        Args:
            service_type: 服务类型，如"deepseek"、"openai"等
            **kwargs: 传递给服务构造函数的参数
            
        Returns:
            AI服务实例
            
        Raises:
            ValueError: 如果服务类型不支持
        """
        if service_type not in cls.SUPPORTED_SERVICES:
            supported = ", ".join(cls.SUPPORTED_SERVICES.keys())
            logger.error(f"不支持的AI服务类型: {service_type}，支持的类型: {supported}")
            raise ValueError(f"不支持的AI服务类型: {service_type}，支持的类型: {supported}")
        
        service_class = cls.SUPPORTED_SERVICES[service_type]
        logger.info(f"创建AI服务: {service_type}")
        return service_class(**kwargs)
    
    @classmethod
    def get_default_service(cls) -> AIServiceInterface:
        """
        获取默认的AI服务实例
        
        Returns:
            默认的AI服务实例
        """
        return cls.create_service("deepseek")
        
    @classmethod
    def get_image_service(cls) -> ImageService:
        """
        获取图片服务实例
        
        Returns:
            图片服务实例
        """
        logger.info("创建图片服务")
        return ImageService() 