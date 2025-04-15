import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class InMemoryDatabase:
    """内存数据库实现"""
    
    def __init__(self):
        self.collections: Dict[str, Dict[str, Any]] = {}
        logger.info("使用内存数据库")
    
    def __getitem__(self, collection_name: str):
        if collection_name not in self.collections:
            self.collections[collection_name] = {}
            logger.info(f"创建内存集合: {collection_name}")
        return InMemoryCollection(self.collections[collection_name])

class InMemoryCollection:
    """内存集合实现"""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        for doc_id, doc in self.data.items():
            matches = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    matches = False
                    break
            if matches:
                return dict(doc)
        return None
    
    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """插入单个文档"""
        # 创建简单的自增ID
        doc_id = str(len(self.data) + 1)
        document["_id"] = doc_id
        self.data[doc_id] = document
        logger.debug(f"插入文档: {document}")
        return type('InsertOneResult', (), {'inserted_id': doc_id})
    
    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> Any:
        """更新单个文档"""
        doc = await self.find_one(query)
        
        if doc:
            doc_id = doc["_id"]
            if "$set" in update:
                for key, value in update["$set"].items():
                    self.data[doc_id][key] = value
            logger.debug(f"更新文档 {doc_id}: {update}")
            return type('UpdateResult', (), {'modified_count': 1, 'matched_count': 1})
        elif upsert:
            # 创建新文档
            new_doc = {}
            for key, value in query.items():
                new_doc[key] = value
                
            if "$set" in update:
                for key, value in update["$set"].items():
                    new_doc[key] = value
                    
            result = await self.insert_one(new_doc)
            return type('UpdateResult', (), {'modified_count': 0, 'matched_count': 0, 'upserted_id': result.inserted_id})
        else:
            return type('UpdateResult', (), {'modified_count': 0, 'matched_count': 0})
    
    async def delete_one(self, query: Dict[str, Any]) -> Any:
        """删除单个文档"""
        doc = await self.find_one(query)
        if doc:
            doc_id = doc["_id"]
            del self.data[doc_id]
            logger.debug(f"删除文档: {doc_id}")
            return type('DeleteResult', (), {'deleted_count': 1})
        return type('DeleteResult', (), {'deleted_count': 0})
    
    async def delete_many(self, query: Dict[str, Any]) -> Any:
        """删除多个文档"""
        to_delete = []
        for doc_id, doc in self.data.items():
            matches = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    matches = False
                    break
            if matches:
                to_delete.append(doc_id)
                
        for doc_id in to_delete:
            del self.data[doc_id]
            
        logger.debug(f"批量删除 {len(to_delete)} 个文档")
        return type('DeleteResult', (), {'deleted_count': len(to_delete)})
    
    async def create_index(self, key: str, **kwargs):
        """创建索引（模拟）"""
        logger.debug(f"创建内存索引: {key} {kwargs}")
        # 内存实现不需要索引
        pass

class Database:
    db = None

db = Database()

async def connect_to_mongodb():
    """初始化数据库连接"""
    logger.info("初始化内存数据库...")
    db.db = InMemoryDatabase()
    logger.info("内存数据库初始化完成")

async def close_mongodb_connection():
    """关闭数据库连接"""
    logger.info("关闭数据库连接...")
    # 内存数据库无需关闭连接
    logger.info("数据库连接已关闭")

def get_database():
    """获取数据库对象"""
    return db.db