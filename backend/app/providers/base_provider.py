from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')

class BaseProvider(ABC, Generic[T]):
    """
    基础Provider接口类，定义了所有Provider必须实现的方法
    
    泛型参数T定义了Provider操作的资源类型
    """
    
    @abstractmethod
    async def get(self, resource_id: str) -> Optional[T]:
        """
        获取指定ID的资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            资源对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """
        创建新资源
        
        Args:
            data: 资源数据
            
        Returns:
            新创建的资源对象
        """
        pass
    
    @abstractmethod
    async def update(self, resource_id: str, data: Dict[str, Any]) -> Optional[T]:
        """
        更新资源
        
        Args:
            resource_id: 资源ID
            data: 更新数据
            
        Returns:
            更新后的资源对象，如果资源不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, resource_id: str) -> bool:
        """
        删除资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    async def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        列出符合条件的资源
        
        Args:
            filters: 过滤条件
            
        Returns:
            资源列表
        """
        pass 