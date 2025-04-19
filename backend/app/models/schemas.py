from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class DocumentType(str, Enum):
    PPT = "ppt"
    WORD = "word"
    PDF = "pdf"

class DocumentRequest(BaseModel):
    topic: str = Field(..., description="文档的主题")
    doc_type: str = Field(..., description="文档类型")
    additional_info: Optional[str] = Field(None, description="额外的信息或要求")
    template_id: Optional[str] = Field(None, description="模板ID，如果使用预定义模板")
    ai_service_type: Optional[str] = Field("deepseek", description="AI服务类型，如deepseek、openai等")
    max_pages: Optional[int] = Field(None, description="限制生成的最大页数/章节数")

# 新增大纲预览模型
class OutlinePreviewRequest(BaseModel):
    topic: str = Field(..., description="文档的主题")
    doc_type: str = Field(..., description="文档类型")
    additional_info: Optional[str] = Field(None, description="额外的信息或要求")
    ai_service_type: Optional[str] = Field("deepseek", description="AI服务类型")

class OutlineItem(BaseModel):
    id: str = Field(..., description="大纲项ID")
    title: str = Field(..., description="标题")
    level: int = Field(1, description="层级，1为章节，2为子章节")
    parent_id: Optional[str] = Field(None, description="父项ID，顶级项为None")
    order: int = Field(..., description="排序顺序")
    
class OutlinePreviewResponse(BaseModel):
    id: str = Field(..., description="预览ID")
    topic: str = Field(..., description="文档的主题")
    doc_type: DocumentType = Field(..., description="文档类型")
    outline_items: List[OutlineItem] = Field(..., description="大纲项列表")
    created_at: datetime = Field(..., description="创建时间")
    title_suggestions: Optional[List[str]] = Field(None, description="AI生成的标题建议列表")
    selected_title: Optional[str] = Field(None, description="已选择的标题")

class OutlineUpdateRequest(BaseModel):
    outline_items: List[OutlineItem] = Field(..., description="更新后的大纲项列表")
    topic: Optional[str] = Field(None, description="更新的主题")
    selected_title: Optional[str] = Field(None, description="用户选择的标题")

# 新增大纲确认请求
class OutlineConfirmRequest(BaseModel):
    preview_id: str = Field(..., description="预览ID")
    template_id: Optional[str] = Field(None, description="模板ID")
    max_pages: Optional[int] = Field(None, description="限制生成的最大页数/章节数")
    selected_title: Optional[str] = Field(None, description="用户选择的标题，如果为None则使用默认标题")

# 新增高级文档请求模型
class PageChapterContent(BaseModel):
    """页面或章节的具体内容定义"""
    title: str = Field(..., description="页面或章节标题")
    content: Optional[str] = Field(None, description="页面或章节的具体内容")
    position: int = Field(..., description="页面/章节的位置顺序")

class AdvancedDocumentRequest(DocumentRequest):
    """高级文档请求，支持限制页数和定义具体页面/章节内容"""
    max_pages: Optional[int] = Field(None, description="限制生成的最大页数/章节数")
    detailed_content: Optional[List[PageChapterContent]] = Field(None, description="用户定义的页面/章节内容")
    is_advanced_mode: bool = Field(True, description="标记为高级模式")

class DocumentResponse(BaseModel):
    id: str = Field(..., description="文档ID")
    topic: str = Field(..., description="文档的主题")
    doc_type: DocumentType = Field(..., description="文档类型")
    status: str = Field(..., description="生成状态")
    download_url: Optional[str] = Field(None, description="下载URL")
    preview_url: Optional[str] = Field(None, description="预览URL")
    created_at: datetime = Field(..., description="创建时间")
    user_id: Optional[str] = Field(None, description="创建者ID")

class DocumentOutline(BaseModel):
    title: str = Field(..., description="文档标题")
    sections: List[Dict[str, Any]] = Field(..., description="文档章节")
    
class GenerationStatus(BaseModel):
    id: str = Field(..., description="任务ID")
    status: str = Field(..., description="当前状态")
    progress: float = Field(..., description="完成百分比")
    message: Optional[str] = Field(None, description="状态消息") 