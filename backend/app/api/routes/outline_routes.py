from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from ...controllers.document_controller import DocumentController
from ...dependencies.controller_dependencies import get_document_controller
from ...models.schemas import OutlinePreviewRequest, OutlinePreviewResponse, OutlineUpdateRequest, OutlineConfirmRequest, DocumentResponse, OutlineItem

router = APIRouter()

@router.post("/preview", response_model=OutlinePreviewResponse)
async def create_outline_preview(
    request: OutlinePreviewRequest,
    background_tasks: BackgroundTasks,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """创建文档大纲预览"""
    response = await document_controller.create_outline_preview(request, background_tasks)
    return response

@router.get("/{preview_id}", response_model=OutlinePreviewResponse)
async def get_outline_preview(
    preview_id: str,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """获取文档大纲预览"""
    preview = document_controller.outline_previews.get(preview_id)
    if not preview:
        raise HTTPException(status_code=404, detail="预览不存在")
    
    # 转换存储的预览数据为响应模型
    outline_items = []
    
    # 按存储的大纲重建项目
    for i, section in enumerate(preview["original_outline"]):
        section_id = f"section_{i}"
        
        outline_items.append(
            OutlineItem(
                id=section_id,
                title=section["title"],
                level=1,
                parent_id=None,
                order=i
            )
        )
        
        # 添加子项
        if "slides" in section and preview["doc_type"] == "ppt":
            for j, slide in enumerate(section["slides"]):
                slide_id = f"{section_id}_slide_{j}"
                
                outline_items.append(
                    OutlineItem(
                        id=slide_id,
                        title=slide["title"],
                        level=2,
                        parent_id=section_id,
                        order=j
                    )
                )
        elif "subsections" in section:
            for j, subsection in enumerate(section["subsections"]):
                subsection_id = f"{section_id}_subsection_{j}"
                
                outline_items.append(
                    OutlineItem(
                        id=subsection_id,
                        title=subsection["title"],
                        level=2,
                        parent_id=section_id,
                        order=j
                    )
                )
    
    # 返回响应
    return OutlinePreviewResponse(
        id=preview_id,
        topic=preview["topic"],
        doc_type=preview["doc_type"],
        outline_items=outline_items,
        created_at=preview["created_at"],
        title_suggestions=preview.get("title_suggestions", []),
        selected_title=preview.get("selected_title", preview["optimized_title"] if "optimized_title" in preview else preview["topic"])
    )

@router.put("/{preview_id}", response_model=OutlinePreviewResponse)
async def update_outline_preview(
    preview_id: str,
    request: OutlineUpdateRequest,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """更新文档大纲预览"""
    response = await document_controller.update_outline_preview(preview_id, request)
    return response

@router.post("/{preview_id}/confirm", response_model=DocumentResponse)
async def confirm_outline(
    preview_id: str,
    request: OutlineConfirmRequest,
    background_tasks: BackgroundTasks,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """确认大纲并生成文档"""
    # 确保传递所有参数
    response = await document_controller.confirm_outline(request, background_tasks)
    return response 