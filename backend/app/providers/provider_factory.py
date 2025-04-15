import logging
from typing import Dict, Any, Optional, Type

from .ai.ai_provider import AIProvider
from .storage.storage_provider import StorageProvider
from .cache_provider import CacheProvider
from .mongodb_cache_provider import MemoryCacheProvider
from .storage.local_storage_provider import LocalStorageProvider

# 导入所有AI Provider实现
from ..services.deepseek_service import DeepSeekService

logger = logging.getLogger(__name__)

class ProviderFactory:
    """Provider工厂，用于创建和获取各类Provider"""
    
    # 支持的AI服务提供者映射
    AI_PROVIDERS = {
        "deepseek": DeepSeekService,
        # 可以添加其他AI Provider，如OpenAI、Claude等
    }
    
    # 支持的存储提供者映射
    STORAGE_PROVIDERS = {
        "local": LocalStorageProvider,
        # 可以添加其他存储Provider，如S3、Azure Blob等
    }
    
    # 支持的缓存提供者映射
    CACHE_PROVIDERS = {
        "memory": MemoryCacheProvider,
        # 可以添加其他缓存Provider，如Redis等
    }
    
    @classmethod
    def get_ai_provider(cls, provider_type: str = "deepseek", **kwargs) -> AIProvider:
        """
        获取AI Provider
        
        Args:
            provider_type: AI Provider类型
            **kwargs: 传递给Provider构造函数的参数
            
        Returns:
            AI Provider实例
            
        Raises:
            ValueError: 如果Provider类型不支持
        """
        if provider_type not in cls.AI_PROVIDERS:
            supported = ", ".join(cls.AI_PROVIDERS.keys())
            error_msg = f"不支持的AI Provider类型: {provider_type}，支持的类型: {supported}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        provider_class = cls.AI_PROVIDERS[provider_type]
        logger.info(f"创建AI Provider: {provider_type}")
        return provider_class(**kwargs)
    
    @classmethod
    def get_storage_provider(cls, provider_type: str = "local", **kwargs) -> StorageProvider:
        """
        获取存储Provider
        
        Args:
            provider_type: 存储Provider类型
            **kwargs: 传递给Provider构造函数的参数
            
        Returns:
            存储Provider实例
            
        Raises:
            ValueError: 如果Provider类型不支持
        """
        if provider_type not in cls.STORAGE_PROVIDERS:
            supported = ", ".join(cls.STORAGE_PROVIDERS.keys())
            error_msg = f"不支持的存储Provider类型: {provider_type}，支持的类型: {supported}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        provider_class = cls.STORAGE_PROVIDERS[provider_type]
        logger.info(f"创建存储Provider: {provider_type}")
        return provider_class(**kwargs)
    
    @classmethod
    def get_cache_provider(cls, provider_type: str = "memory", collection_name: str = "document_cache", **kwargs) -> Optional[CacheProvider]:
        """
        获取缓存Provider
        
        Args:
            provider_type: 缓存Provider类型
            collection_name: 集合名称
            **kwargs: 传递给Provider构造函数的参数
            
        Returns:
            缓存Provider实例，如果类型不支持则返回None
        """
        if provider_type not in cls.CACHE_PROVIDERS:
            logger.warning(f"不支持的缓存Provider类型: {provider_type}，将不使用缓存")
            return None
            
        provider_class = cls.CACHE_PROVIDERS[provider_type]
        logger.info(f"创建缓存Provider: {provider_type}")
        return provider_class(collection_name=collection_name, **kwargs) 