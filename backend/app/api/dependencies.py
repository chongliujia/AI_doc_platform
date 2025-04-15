from fastapi import Depends
from typing import Optional

from ..providers.provider_factory import ProviderFactory
from ..providers.ai.ai_provider import AIProvider
from ..providers.storage.storage_provider import StorageProvider
from ..providers.cache_provider import CacheProvider
from ..controllers.document_controller import DocumentController

# 缓存Provider单例
_cache_provider = None

# 存储Provider单例
_storage_provider = None

# 文档Controller单例
_document_controller = None

def get_ai_provider(provider_type: str = "deepseek") -> AIProvider:
    """获取AI Provider依赖"""
    return ProviderFactory.get_ai_provider(provider_type)

def get_storage_provider() -> StorageProvider:
    """获取存储Provider依赖（单例）"""
    global _storage_provider
    if _storage_provider is None:
        _storage_provider = ProviderFactory.get_storage_provider("local")
    return _storage_provider

def get_cache_provider() -> Optional[CacheProvider]:
    """获取缓存Provider依赖（单例）"""
    global _cache_provider
    if _cache_provider is None:
        _cache_provider = ProviderFactory.get_cache_provider("memory")
    return _cache_provider

def get_document_controller(
    ai_provider: AIProvider = Depends(get_ai_provider),
    storage_provider: StorageProvider = Depends(get_storage_provider),
    cache_provider: Optional[CacheProvider] = Depends(get_cache_provider)
) -> DocumentController:
    """获取文档Controller依赖（单例）"""
    global _document_controller
    if _document_controller is None:
        _document_controller = DocumentController(
            ai_provider=ai_provider,
            storage_provider=storage_provider,
            cache_provider=cache_provider
        )
    return _document_controller 