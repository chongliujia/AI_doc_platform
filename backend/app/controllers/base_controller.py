from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from fastapi import BackgroundTasks, Depends, HTTPException

from ..providers.base_provider import BaseProvider

T = TypeVar('T')

class BaseController(ABC, Generic[T]):
    """
    基础Controller类，定义了Controller的基本方法
    
    泛型参数T定义了Controller操作的资源类型
    """
    
    def __init__(self, provider: BaseProvider[T]):
        """
        初始化Controller
        
        Args:
            provider: 资源提供者
        """
        self.provider = provider
    
    async def get(self, resource_id: str) -> T:
        """
        获取指定ID的资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            资源对象
            
        Raises:
            HTTPException: 如果资源不存在
        """
        resource = await self.provider.get(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail=f"资源不存在: {resource_id}")
        return resource
    
    async def create(self, data: Dict[str, Any], background_tasks: Optional[BackgroundTasks] = None) -> T:
        """
        创建新资源
        
        Args:
            data: 资源数据
            background_tasks: 后台任务队列（可选）
            
        Returns:
            新创建的资源对象
        """
        return await self.provider.create(data)
    
    async def update(self, resource_id: str, data: Dict[str, Any]) -> T:
        """
        更新资源
        
        Args:
            resource_id: 资源ID
            data: 更新数据
            
        Returns:
            更新后的资源对象
            
        Raises:
            HTTPException: 如果资源不存在
        """
        resource = await self.provider.update(resource_id, data)
        if not resource:
            raise HTTPException(status_code=404, detail=f"资源不存在: {resource_id}")
        return resource
    
    async def delete(self, resource_id: str) -> Dict[str, bool]:
        """
        删除资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            包含success字段的对象
            
        Raises:
            HTTPException: 如果资源不存在或删除失败
        """
        success = await self.provider.delete(resource_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"资源不存在或删除失败: {resource_id}")
        return {"success": True}
    
    async def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        列出符合条件的资源
        
        Args:
            filters: 过滤条件
            
        Returns:
            资源列表
        """
        return await self.provider.list(filters) 