import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timedelta

from .cache_provider import CacheProvider

T = TypeVar('T')

logger = logging.getLogger(__name__)

class MemoryCacheProvider(CacheProvider[T]):
    """内存缓存Provider实现"""
    
    def __init__(self, collection_name: str, ttl_seconds: int = 604800):  # 默认7天
        """
        初始化内存缓存Provider
        
        Args:
            collection_name: 集合名称（仅用于日志）
            ttl_seconds: 默认缓存过期时间（秒）
        """
        self.collection_name = collection_name
        self.default_ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"初始化内存缓存: {collection_name}, TTL: {ttl_seconds}秒")
    
    async def get(self, key: str) -> Optional[T]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在则返回None
        """
        try:
            if key not in self.cache:
                logger.debug(f"缓存未命中: {key}")
                return None
                
            item = self.cache[key]
            
            # 检查是否过期
            if "expires_at" in item and item["expires_at"] < datetime.now():
                logger.debug(f"缓存已过期: {key}")
                await self.delete(key)
                return None
                
            logger.debug(f"缓存命中: {key}")
            return item.get("value")
        except Exception as e:
            logger.error(f"获取缓存出错: {str(e)}")
            return None
    
    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 过期时间（秒），如果为None则使用默认值
            
        Returns:
            是否成功设置
        """
        try:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # 构造缓存项
            cache_item = {
                "key": key,
                "value": value,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            if expires_at:
                cache_item["expires_at"] = expires_at
            
            # 更新缓存
            self.cache[key] = cache_item
            
            logger.debug(f"缓存已设置: {key}, TTL: {ttl}秒")
            return True
        except Exception as e:
            logger.error(f"设置缓存出错: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"已删除缓存: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除缓存出错: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否成功清空
        """
        try:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"已清空缓存, 删除数量: {count}")
            return True
        except Exception as e:
            logger.error(f"清空缓存出错: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> Optional[int]:
        """
        获取缓存过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余过期时间（秒），如果不存在或已过期则返回None
        """
        try:
            if key not in self.cache or "expires_at" not in self.cache[key]:
                return None
                
            # 计算剩余时间
            remaining = (self.cache[key]["expires_at"] - datetime.now()).total_seconds()
            return max(0, int(remaining)) if remaining > 0 else None
        except Exception as e:
            logger.error(f"获取TTL出错: {str(e)}")
            return None 