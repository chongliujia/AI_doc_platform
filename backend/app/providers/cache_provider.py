from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')

class CacheProvider(ABC, Generic[T]):
    """
    缓存服务提供者接口，定义了所有缓存服务必须实现的方法
    
    泛型参数T定义了缓存存储的数据类型
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 过期时间（秒），如果为None则不过期
            
        Returns:
            是否成功设置
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否成功清空
        """
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> Optional[int]:
        """
        获取缓存过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余过期时间（秒），如果不存在或已过期则返回None
        """
        pass 