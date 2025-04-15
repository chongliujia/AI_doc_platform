from typing import Any, Dict, List, Optional
from fastapi import BackgroundTasks, Depends, HTTPException
import uuid
from datetime import datetime
import logging

from ..models.schemas import DocumentRequest, DocumentResponse, AdvancedDocumentRequest, GenerationStatus
from ..providers.ai.ai_provider import AIProvider
from ..providers.storage.storage_provider import StorageProvider
from ..providers.cache_provider import CacheProvider
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class DocumentController:
    """文档控制器，处理文档生成相关逻辑"""
    
    def __init__(
        self, 
        ai_provider: AIProvider,
        storage_provider: StorageProvider,
        cache_provider: Optional[CacheProvider] = None
    ):
        """
        初始化文档控制器
        
        Args:
            ai_provider: AI服务提供者
            storage_provider: 存储服务提供者
            cache_provider: 缓存服务提供者（可选）
        """
        self.ai_provider = ai_provider
        self.storage_provider = storage_provider
        self.cache_provider = cache_provider
        self.generation_tasks = {}  # 存储生成任务的状态
    
    async def create_document(
        self, 
        request: DocumentRequest, 
        background_tasks: BackgroundTasks
    ) -> DocumentResponse:
        """
        创建文档生成任务
        
        Args:
            request: 文档请求
            background_tasks: 后台任务队列
            
        Returns:
            文档响应
        """
        # 确保文档类型有效
        if request.doc_type not in ["ppt", "word", "pdf"]:
            raise HTTPException(status_code=400, detail="无效的文档类型")
        
        # 生成唯一ID
        doc_id = str(uuid.uuid4())
        
        # 创建初始响应
        response = DocumentResponse(
            id=doc_id,
            topic=request.topic,
            doc_type=request.doc_type,
            status="queued",
            created_at=datetime.now().isoformat()
        )
        
        # 存储任务状态
        self.generation_tasks[doc_id] = {
            "status": "queued",
            "progress": 0.0,
            "message": "任务已加入队列",
            "topic": request.topic,
            "doc_type": request.doc_type
        }
        
        # 添加到后台任务
        background_tasks.add_task(
            self.generate_document_background,
            doc_id=doc_id,
            topic=request.topic,
            doc_type=request.doc_type,
            additional_info=request.additional_info,
            template_id=request.template_id,
            ai_service_type=request.ai_service_type
        )
        
        return response
    
    async def create_advanced_document(
        self, 
        request: AdvancedDocumentRequest, 
        background_tasks: BackgroundTasks
    ) -> DocumentResponse:
        """
        创建高级文档生成任务
        
        Args:
            request: 高级文档请求
            background_tasks: 后台任务队列
            
        Returns:
            文档响应
        """
        # 确保文档类型有效
        if request.doc_type not in ["ppt", "word", "pdf"]:
            raise HTTPException(status_code=400, detail="无效的文档类型")
        
        # 生成唯一ID
        doc_id = str(uuid.uuid4())
        
        # 创建初始响应
        response = DocumentResponse(
            id=doc_id,
            topic=request.topic,
            doc_type=request.doc_type,
            status="queued",
            created_at=datetime.now().isoformat()
        )
        
        # 存储任务状态
        self.generation_tasks[doc_id] = {
            "status": "queued",
            "progress": 0.0,
            "message": "高级文档生成任务已加入队列",
            "topic": request.topic,
            "doc_type": request.doc_type
        }
        
        # 添加到后台任务
        background_tasks.add_task(
            self.generate_advanced_document_background,
            doc_id=doc_id,
            topic=request.topic,
            doc_type=request.doc_type,
            additional_info=request.additional_info,
            template_id=request.template_id,
            ai_service_type=request.ai_service_type,
            max_pages=request.max_pages,
            detailed_content=request.detailed_content
        )
        
        return response
    
    async def get_document_status(self, doc_id: str) -> GenerationStatus:
        """
        获取文档生成任务的状态
        
        Args:
            doc_id: 文档ID
            
        Returns:
            生成状态
            
        Raises:
            HTTPException: 如果任务不存在
        """
        if doc_id not in self.generation_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_info = self.generation_tasks[doc_id]
        return GenerationStatus(
            id=doc_id,
            status=task_info["status"],
            progress=task_info["progress"],
            message=task_info.get("message")
        )
    
    async def get_document(self, document_id: str) -> DocumentResponse:
        """
        获取生成的文档信息
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档响应
            
        Raises:
            HTTPException: 如果文档不存在
        """
        if document_id not in self.generation_tasks:
            raise HTTPException(
                status_code=404,
                detail=f"文档不存在，可用的文档ID: {list(self.generation_tasks.keys())}"
            )
        
        task_info = self.generation_tasks[document_id]
        
        if task_info["status"] != "completed":
            return DocumentResponse(
                id=document_id,
                topic=task_info.get("topic", "未知"),
                doc_type=task_info.get("doc_type", "ppt"),
                status=task_info["status"],
                created_at=datetime.now().isoformat()
            )
        
        return DocumentResponse(
            id=document_id,
            topic=task_info.get("topic", "未知"),
            doc_type=task_info.get("doc_type", "ppt"),
            status=task_info["status"],
            download_url=task_info.get("download_url"),
            preview_url=task_info.get("preview_url"),
            created_at=task_info.get("created_at", datetime.now().isoformat())
        )
    
    async def generate_document_background(
        self,
        doc_id: str,
        topic: str,
        doc_type: str,
        additional_info: Optional[str] = None,
        template_id: Optional[str] = None,
        ai_service_type: str = "deepseek"
    ):
        """
        后台生成文档
        
        Args:
            doc_id: 文档ID
            topic: 主题
            doc_type: 文档类型
            additional_info: 额外信息
            template_id: 模板ID
            ai_service_type: AI服务类型
        """
        # 处理文档生成的实际逻辑
        # 具体实现将在子类中提供
        pass
    
    async def generate_advanced_document_background(
        self,
        doc_id: str,
        topic: str,
        doc_type: str,
        additional_info: Optional[str] = None,
        template_id: Optional[str] = None,
        ai_service_type: str = "deepseek",
        max_pages: Optional[int] = None,
        detailed_content: Optional[List[Dict[str, Any]]] = None
    ):
        """
        后台生成高级文档
        
        Args:
            doc_id: 文档ID
            topic: 主题
            doc_type: 文档类型
            additional_info: 额外信息
            template_id: 模板ID
            ai_service_type: AI服务类型
            max_pages: 最大页数
            detailed_content: 详细内容
        """
        # 处理高级文档生成的实际逻辑
        # 具体实现将在子类中提供
        pass 