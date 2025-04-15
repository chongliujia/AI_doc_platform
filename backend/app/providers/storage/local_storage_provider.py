import os
import logging
from typing import List, Optional, BinaryIO
from pathlib import Path

from ...core.config import settings
from .storage_provider import StorageProvider

logger = logging.getLogger(__name__)

class LocalStorageProvider(StorageProvider):
    """本地文件存储Provider实现"""
    
    def __init__(self, base_dir: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化本地存储Provider
        
        Args:
            base_dir: 基础目录，默认为generated_docs
            base_url: 基础URL，默认为/downloads
        """
        self.base_dir = base_dir or os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
            "generated_docs"
        ))
        self.base_url = base_url or "/downloads"
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        
        logger.info(f"本地存储Provider初始化，基础目录: {self.base_dir}")
    
    async def save_file(self, file_path: str, content: BinaryIO) -> bool:
        """
        保存文件
        
        Args:
            file_path: 文件路径（相对于基础目录）
            content: 文件内容
            
        Returns:
            是否成功保存
        """
        try:
            # 获取完整路径
            full_path = os.path.join(self.base_dir, file_path)
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 写入文件
            with open(full_path, 'wb') as f:
                f.write(content.read())
            
            logger.info(f"文件已保存: {full_path}")
            return True
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return False
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """
        获取文件内容
        
        Args:
            file_path: 文件路径（相对于基础目录）
            
        Returns:
            文件内容，如果文件不存在则返回None
        """
        try:
            # 获取完整路径
            full_path = os.path.join(self.base_dir, file_path)
            
            # 检查文件是否存在
            if not os.path.exists(full_path):
                logger.warning(f"文件不存在: {full_path}")
                return None
            
            # 读取文件
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"获取文件失败: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径（相对于基础目录）
            
        Returns:
            是否成功删除
        """
        try:
            # 获取完整路径
            full_path = os.path.join(self.base_dir, file_path)
            
            # 检查文件是否存在
            if not os.path.exists(full_path):
                logger.warning(f"文件不存在: {full_path}")
                return False
            
            # 删除文件
            os.remove(full_path)
            logger.info(f"文件已删除: {full_path}")
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False
    
    async def list_files(self, directory: str = "") -> List[str]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径（相对于基础目录），默认为根目录
            
        Returns:
            文件路径列表（相对于基础目录）
        """
        try:
            # 获取完整路径
            full_path = os.path.join(self.base_dir, directory)
            
            # 检查目录是否存在
            if not os.path.exists(full_path) or not os.path.isdir(full_path):
                logger.warning(f"目录不存在: {full_path}")
                return []
            
            # 列出文件
            files = []
            for root, _, filenames in os.walk(full_path):
                for filename in filenames:
                    # 获取相对路径
                    rel_path = os.path.relpath(os.path.join(root, filename), self.base_dir)
                    files.append(rel_path)
            
            return files
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            return []
    
    async def get_file_url(self, file_path: str) -> str:
        """
        获取文件URL
        
        Args:
            file_path: 文件路径（相对于基础目录）
            
        Returns:
            文件URL
        """
        # 拼接URL
        return f"{self.base_url}/{file_path}" 