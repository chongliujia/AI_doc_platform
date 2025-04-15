from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, BinaryIO
from pathlib import Path

class StorageProvider(ABC):
    """
    存储服务提供者接口，定义了所有存储服务必须实现的方法
    """
    
    @abstractmethod
    async def save_file(self, file_path: str, content: BinaryIO) -> bool:
        """
        保存文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功保存
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """
        获取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容，如果文件不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    async def list_files(self, directory: str) -> List[str]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            
        Returns:
            文件路径列表
        """
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """
        获取文件URL
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件URL
        """
        pass 