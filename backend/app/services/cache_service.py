import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from ..core.database import get_database

logger = logging.getLogger(__name__)

class CacheService:
    """文档内容缓存服务，减少重复生成"""
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.document_cache
        self.cache_ttl = timedelta(days=7)  # 缓存有效期为7天
    
    @staticmethod
    def generate_cache_key(topic: str, doc_type: str, additional_info: Optional[str] = None) -> str:
        """生成缓存键"""
        # 规范化输入
        topic = topic.lower().strip()
        doc_type = doc_type.lower().strip()
        additional_info = (additional_info or "").lower().strip()
        
        # 创建合并字符串
        cache_string = f"{topic}:{doc_type}:{additional_info}"
        
        # 生成哈希值作为缓存键
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    async def get_cached_content(self, topic: str, doc_type: str, additional_info: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取缓存的文档内容"""
        cache_key = self.generate_cache_key(topic, doc_type, additional_info)
        
        # 查询缓存
        cached_item = await self.collection.find_one({"cache_key": cache_key})
        
        if not cached_item:
            logger.info(f"缓存未命中: {cache_key}")
            return None
            
        # 检查缓存是否过期
        created_at = cached_item.get("created_at")
        if created_at and datetime.fromisoformat(created_at) + self.cache_ttl < datetime.now():
            logger.info(f"缓存已过期: {cache_key}")
            await self.collection.delete_one({"cache_key": cache_key})
            return None
            
        logger.info(f"缓存命中: {cache_key}")
        return cached_item.get("content")
    
    async def cache_content(self, topic: str, doc_type: str, content: Dict[str, Any], additional_info: Optional[str] = None) -> bool:
        """缓存文档内容"""
        cache_key = self.generate_cache_key(topic, doc_type, additional_info)
        
        try:
            # 存储缓存项
            await self.collection.update_one(
                {"cache_key": cache_key},
                {"$set": {
                    "cache_key": cache_key,
                    "topic": topic,
                    "doc_type": doc_type,
                    "additional_info": additional_info,
                    "content": content,
                    "created_at": datetime.now().isoformat()
                }},
                upsert=True
            )
            logger.info(f"内容已缓存: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"缓存内容失败: {str(e)}")
            return False
            
    async def clear_expired_cache(self) -> int:
        """清理过期缓存"""
        expiry_date = (datetime.now() - self.cache_ttl).isoformat()
        result = await self.collection.delete_many({"created_at": {"$lt": expiry_date}})
        deleted_count = result.deleted_count
        logger.info(f"已清理 {deleted_count} 条过期缓存")
        return deleted_count 