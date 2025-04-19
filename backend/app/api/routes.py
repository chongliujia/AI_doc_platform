from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
import uuid
from datetime import datetime
import os
from pydantic import ValidationError
import asyncio
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
import json
import logging
from fastapi.staticfiles import StaticFiles

from ..models.schemas import (
    DocumentRequest, DocumentResponse, GenerationStatus, 
    AdvancedDocumentRequest, PageChapterContent,
    OutlinePreviewRequest, OutlinePreviewResponse, 
    OutlineUpdateRequest, OutlineConfirmRequest
)
from ..controllers.document_controller import DocumentController
from ..api.dependencies import get_document_controller
from ..services.ai_service_factory import AIServiceFactory
from ..services.ppt_generator import PPTGenerator
from ..services.word_generator import WordGenerator
from ..services.pdf_generator import PDFGenerator
from ..services.advanced_content_generator import AdvancedContentGenerator

router = APIRouter()
ai_service = AIServiceFactory.get_default_service()

# 存储生成任务的状态
generation_tasks = {}

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 在 main.py 中添加静态文件挂载
# app.mount("/downloads", StaticFiles(directory="generated_docs"), name="downloads")
# app.mount("/previews", StaticFiles(directory="generated_docs"), name="previews")

# 大纲预览相关路由
@router.post("/outline-preview/", response_model=OutlinePreviewResponse)
async def create_outline_preview(
    request: OutlinePreviewRequest,
    background_tasks: BackgroundTasks,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    创建文档大纲预览
    """
    return await document_controller.create_outline_preview(request, background_tasks)

@router.put("/outline-preview/{preview_id}", response_model=OutlinePreviewResponse)
async def update_outline_preview(
    preview_id: str,
    request: OutlineUpdateRequest,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    更新文档大纲预览
    """
    return await document_controller.update_outline_preview(preview_id, request)

@router.post("/outline-confirm/", response_model=DocumentResponse)
async def confirm_outline(
    request: OutlineConfirmRequest,
    background_tasks: BackgroundTasks,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    确认大纲并开始生成文档
    """
    return await document_controller.confirm_outline(request, background_tasks)

# 现有文档生成路由
@router.post("/documents/", response_model=DocumentResponse)
async def create_document(
    request: DocumentRequest, 
    background_tasks: BackgroundTasks,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    创建新的文档生成任务
    """
    # 确保 doc_type 是有效值
    if request.doc_type not in ["ppt", "word", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    return await document_controller.create_document(request, background_tasks)

@router.get("/documents/{doc_id}/status", response_model=GenerationStatus)
async def get_document_status(
    doc_id: str,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    获取文档生成任务的状态
    """
    try:
        return await document_controller.get_document_status(doc_id)
    except HTTPException as e:
        if e.status_code == 404:
            # 提供更有用的错误信息
            active_docs = list(document_controller.generation_tasks.keys())
            error_msg = "文档不存在"
            if active_docs:
                error_msg += f"。当前活跃的文档ID: {', '.join(active_docs[:5])}"
                if len(active_docs) > 5:
                    error_msg += f"... 等共 {len(active_docs)} 个"
            
            logger.info(f"文档ID '{doc_id}' 不存在。正在返回有用的错误信息。")
            raise HTTPException(
                status_code=404, 
                detail=error_msg
            )
        raise

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    获取生成的文档信息
    """
    print(f"Fetching document with ID: {document_id}")
    print(f"Available document IDs: {list(generation_tasks.keys())}")
    
    if document_id not in generation_tasks:
        # 返回更友好的错误信息
        return JSONResponse(
            status_code=404,
            content={"detail": f"文档不存在，可用的文档ID: {list(generation_tasks.keys())}"}
        )
    
    task_info = generation_tasks[document_id]
    
    if task_info["status"] != "completed":
        return DocumentResponse(
            id=document_id,
            topic=task_info.get("topic", "未知"),
            doc_type="ppt",  # 使用有效的默认值，而不是 "unknown"
            status=task_info["status"],
            created_at=datetime.now().isoformat()
        )
    
    # 确保 doc_type 是有效的枚举值
    doc_type = task_info.get("doc_type")
    if doc_type not in ["ppt", "word", "pdf"]:
        doc_type = "ppt"  # 设置默认值
    
    return DocumentResponse(
        id=document_id,
        topic=task_info.get("topic", "未知"),
        doc_type=doc_type,
        status=task_info["status"],
        download_url=task_info.get("download_url"),
        preview_url=task_info.get("preview_url"),
        created_at=task_info.get("created_at", datetime.now().isoformat())
    )

@router.get("/documents/{document_id}/stream")
async def stream_document_status(
    document_id: str,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    使用 SSE 流式传输文档生成状态
    """
    if document_id not in document_controller.generation_tasks:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    async def event_generator():
        # 发送初始状态
        task_info = document_controller.generation_tasks[document_id]
        yield f"data: {json.dumps(task_info)}\n\n"
        
        # 持续发送更新
        last_status = task_info.get("status")
        last_progress = task_info.get("progress", 0)
        
        while True:
            await asyncio.sleep(0.5)  # 更频繁地检查更新
            
            if document_id not in document_controller.generation_tasks:
                yield f"data: {json.dumps({'error': '文档不存在'})}\n\n"
                break
            
            task_info = document_controller.generation_tasks[document_id]
            current_status = task_info.get("status")
            current_progress = task_info.get("progress", 0)
            
            # 只在状态或进度变化时发送更新
            if (current_status != last_status or 
                abs(current_progress - last_progress) >= 0.01):  # 进度变化超过1%
                
                yield f"data: {json.dumps(task_info)}\n\n"
                
                last_status = current_status
                last_progress = current_progress
            
            # 如果任务已完成或失败，发送最终状态并结束流
            if current_status in ['completed', 'failed']:
                # 确保发送最终状态
                yield f"data: {json.dumps(task_info)}\n\n"
                break
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )

@router.get("/downloads/{file_name}")
async def download_file(file_name: str):
    """
    下载生成的文件
    """
    # 修正路径：直接从 downloads 子目录查找文件
    file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_docs", "downloads", file_name))
    logger.info(f"尝试下载文件: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 如果完整路径不存在，尝试查找匹配的文件
        logger.warning(f"文件不存在: {file_path}")
        logger.info("尝试查找匹配的文件...")
        
        base_dir = os.path.dirname(file_path)
        if os.path.exists(base_dir):
            # 获取目录中的所有文件
            files = os.listdir(base_dir)
            
            # 查找含有相似名称（文件名的一部分）或相似后缀的文件
            # 先提取文件后缀
            file_ext = os.path.splitext(file_name)[1]
            matched_files = []
            
            for f in files:
                # 同类型文件
                if f.endswith(file_ext):
                    matched_files.append(f)
                    logger.info(f"找到潜在匹配文件: {f}")
            
            if matched_files:
                # 找到最近修改的文件作为默认选择
                latest_file = max(matched_files, key=lambda x: os.path.getmtime(os.path.join(base_dir, x)))
                logger.info(f"使用最近生成的文件: {latest_file}")
                file_path = os.path.join(base_dir, latest_file)
            else:
                logger.error(f"无法找到匹配的文件")
                raise HTTPException(status_code=404, detail="文件不存在")
        else:
            logger.error(f"目录不存在: {base_dir}")
            raise HTTPException(status_code=404, detail="文件不存在")
    
    # 获取实际文件名用于响应头
    actual_filename = os.path.basename(file_path)
    logger.info(f"准备下载文件: {actual_filename}")
    
    return FileResponse(
        path=file_path, 
        filename=actual_filename,
        media_type="application/octet-stream"
    )

@router.get("/previews/{file_name}")
async def preview_file(file_name: str):
    """
    预览生成的文件
    """
    # 修正路径：直接从 previews 子目录查找文件
    file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_docs", "previews", file_name))
    logger.info(f"尝试预览文件: {file_path}")
    
    # 由于我们保存文件时都存储在 downloads 目录中，而不是 previews 目录
    # 如果 previews 目录中不存在，则尝试从 downloads 目录中查找
    if not os.path.exists(file_path):
        downloads_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_docs", "downloads", file_name))
        if os.path.exists(downloads_path):
            file_path = downloads_path
            logger.info(f"在downloads目录中找到文件: {file_path}")
        else:
            # 如果完整路径不存在，尝试查找匹配的文件
            logger.warning(f"文件不存在: {file_path}")
            logger.info("尝试查找匹配的文件...")
            
            # 首先在downloads目录中查找
            downloads_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_docs", "downloads"))
            if os.path.exists(downloads_dir):
                # 获取目录中的所有文件
                files = os.listdir(downloads_dir)
                
                # 查找含有相似名称（文件名的一部分）或相似后缀的文件
                # 先提取文件后缀
                file_ext = os.path.splitext(file_name)[1]
                matched_files = []
                
                for f in files:
                    # 同类型文件
                    if f.endswith(file_ext):
                        matched_files.append(f)
                        logger.info(f"找到潜在匹配文件: {f}")
                
                if matched_files:
                    # 找到最近修改的文件作为默认选择
                    latest_file = max(matched_files, key=lambda x: os.path.getmtime(os.path.join(downloads_dir, x)))
                    logger.info(f"使用最近生成的文件: {latest_file}")
                    file_path = os.path.join(downloads_dir, latest_file)
                else:
                    logger.error(f"无法找到匹配的文件")
                    raise HTTPException(status_code=404, detail="文件不存在")
            else:
                logger.error(f"目录不存在: {downloads_dir}")
                raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据文件类型设置适当的媒体类型
    media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if file_name.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_name.endswith(".pdf"):
        media_type = "application/pdf"
    
    # 获取实际文件名用于响应头
    actual_filename = os.path.basename(file_path)
    logger.info(f"准备预览文件: {actual_filename}")
    
    return FileResponse(
        path=file_path,
        media_type=media_type
    )

@router.post("/advanced-documents/", response_model=DocumentResponse)
async def create_advanced_document(
    request: AdvancedDocumentRequest, 
    background_tasks: BackgroundTasks,
    document_controller: DocumentController = Depends(get_document_controller)
):
    """
    创建新的高级文档生成任务，支持页面/章节限制和自定义内容
    """
    # 确保 doc_type 是有效值
    if request.doc_type not in ["ppt", "word", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    return await document_controller.create_advanced_document(request, background_tasks)

async def generate_document_background(
    doc_id: str, 
    topic: str, 
    doc_type: str,
    additional_info: str = None,
    template_id: str = None,
    ai_service_type: str = "deepseek"  # 添加AI服务类型参数
):
    """
    后台文档生成任务，提供更细粒度的进度更新
    
    Args:
        doc_id: 文档ID
        topic: 文档主题
        doc_type: 文档类型
        additional_info: 额外信息
        template_id: 模板ID
        ai_service_type: AI服务类型，默认为"deepseek"
    """
    try:
        # 初始状态
        generation_tasks[doc_id].update({
            "status": "processing",
            "progress": 0.05,
            "message": "正在准备生成...",
            "topic": topic,
            "doc_type": doc_type,
            "created_at": datetime.now().isoformat()
        })
        
        logger.info(f"开始生成文档: ID={doc_id}, 主题='{topic}', 类型={doc_type}, AI服务={ai_service_type}")
        if additional_info:
            logger.info(f"附加信息: {additional_info}")
        if template_id:
            logger.info(f"使用模板: {template_id}")
        
        # 获取指定的AI服务
        service = AIServiceFactory.create_service(ai_service_type)
        logger.info(f"成功创建AI服务: {ai_service_type}")
        
        # 步骤1: 分析主题
        generation_tasks[doc_id].update({
            "progress": 0.1,
            "message": "正在分析主题..."
        })
        logger.info(f"[文档 {doc_id}] 步骤1: 分析主题 '{topic}'")
        await asyncio.sleep(1)  # 给前端一些时间更新UI
        
        # 步骤2: 生成文档大纲
        generation_tasks[doc_id].update({
            "progress": 0.2,
            "message": "正在生成文档大纲..."
        })
        logger.info(f"[文档 {doc_id}] 步骤2: 开始生成文档大纲")
        
        # 使用 try-except 块包装大纲生成
        try:
            outline = service.generate_document_outline(topic, doc_type)
            if not outline:
                raise ValueError("生成大纲失败")
                
            # 记录大纲信息
            logger.info(f"[文档 {doc_id}] 成功生成大纲: {len(outline)} 个章节")
            for i, section in enumerate(outline):
                section_title = section.get("title", "未知章节")
                if doc_type == "ppt" and "slides" in section:
                    slides_count = len(section.get("slides", []))
                    logger.info(f"  章节 {i+1}: {section_title} ({slides_count} 张幻灯片)")
                elif "subsections" in section:
                    subsections_count = len(section.get("subsections", []))
                    logger.info(f"  章节 {i+1}: {section_title} ({subsections_count} 个子章节)")
                else:
                    logger.info(f"  章节 {i+1}: {section_title}")
                
        except Exception as e:
            logger.error(f"[文档 {doc_id}] 生成大纲时出错: {str(e)}")
            generation_tasks[doc_id].update({
                "status": "failed",
                "message": "无法生成文档大纲，请检查主题是否合适或稍后重试"
            })
            return
        
        # 步骤3: 准备内容
        generation_tasks[doc_id].update({
            "progress": 0.4,
            "message": "大纲已生成，正在准备内容..."
        })
        logger.info(f"[文档 {doc_id}] 步骤3: 准备内容")
        await asyncio.sleep(1)  # 给前端一些时间更新UI
        
        # 步骤4: 创建文档
        generation_tasks[doc_id].update({
            "progress": 0.6,
            "message": "正在创建文档..."
        })
        logger.info(f"[文档 {doc_id}] 步骤4: 开始创建文档")
        
        # 根据文档类型选择生成器
        file_path = None
        try:
            if doc_type == "ppt":
                logger.info(f"[文档 {doc_id}] 使用PPT生成器")
                generator = PPTGenerator(ai_service_type=ai_service_type)
                file_path = generator.generate(topic, outline, template_id)
            elif doc_type == "word":
                logger.info(f"[文档 {doc_id}] 使用Word生成器")
                generator = WordGenerator(ai_service_type=ai_service_type)
                file_path = generator.generate(topic, outline, template_id)
            elif doc_type == "pdf":
                logger.info(f"[文档 {doc_id}] 使用PDF生成器")
                generator = PDFGenerator(ai_service_type=ai_service_type)
                file_path = generator.generate(topic, outline, template_id)
            else:
                raise ValueError(f"不支持的文档类型: {doc_type}")
            
            if not file_path:
                raise ValueError("文档生成失败")
                
            logger.info(f"[文档 {doc_id}] 文档生成成功: {file_path}")
        except Exception as e:
            logger.error(f"[文档 {doc_id}] 创建文档时出错: {str(e)}")
            generation_tasks[doc_id].update({
                "status": "failed",
                "message": f"文档生成失败: {str(e)}"
            })
            return
        
        # 步骤5: 完成格式化
        generation_tasks[doc_id].update({
            "progress": 0.8,
            "message": "正在完成格式化..."
        })
        logger.info(f"[文档 {doc_id}] 步骤5: 完成格式化")
        await asyncio.sleep(1)  # 给前端一些时间更新UI
        
        # 文件生成成功，更新下载链接
        base_url = "http://localhost:8001"  # 应该从配置中获取
        download_url = f"{base_url}/downloads/{os.path.basename(file_path)}"
        preview_url = f"{base_url}/previews/{os.path.basename(file_path)}"
        
        # 完成
        generation_tasks[doc_id].update({
            "status": "completed",
            "progress": 1.0,
            "message": "文档生成完成",
            "download_url": download_url,
            "preview_url": preview_url
        })
        
        logger.info(f"[文档 {doc_id}] 文档生成任务完成")
        logger.info(f"[文档 {doc_id}] 下载链接: {download_url}")
        logger.info(f"[文档 {doc_id}] 预览链接: {preview_url}")
        
    except Exception as e:
        logger.error(f"[文档 {doc_id}] 文档生成过程中出错: {str(e)}")
        generation_tasks[doc_id].update({
            "status": "failed",
            "message": f"生成过程中出错: {str(e)}"
        }) 

async def generate_advanced_document_background(
    doc_id: str,
    topic: str,
    doc_type: str,
    additional_info: Optional[str] = None,
    template_id: Optional[str] = None,
    ai_service_type: str = "deepseek",
    max_pages: Optional[int] = None,
    detailed_content: Optional[List[PageChapterContent]] = None
):
    """
    后台处理高级文档生成任务
    """
    try:
        # 更新状态为处理中，并保存主题和文档类型信息
        generation_tasks[doc_id].update({
            "status": "processing",
            "progress": 0.05,
            "message": "开始高级文档生成...",
            "topic": topic,  # 添加主题信息
            "doc_type": doc_type,  # 添加文档类型信息
            "created_at": datetime.now().isoformat()  # 添加创建时间
        })

        logger.info(f"开始高级文档生成: ID={doc_id}, 主题='{topic}', 类型={doc_type}")
        
        # 根据文档类型选择生成器
        advanced_content_generator = AdvancedContentGenerator(ai_service_type)
        
        # 创建进度回调函数
        def update_progress(progress: float, message: str):
            generation_tasks[doc_id]["progress"] = progress
            generation_tasks[doc_id]["message"] = message
            logger.info(f"任务 {doc_id} 进度: {progress:.2f} - {message}")
        
        try:
            # 使用高级内容生成器生成内容
            document_content = await advanced_content_generator.generate_with_constraints(
                topic,
                doc_type,
                additional_info,
                max_pages,
                detailed_content,
                update_progress
            )
        except Exception as content_error:
            # 内容生成失败时，尝试使用默认生成
            logger.error(f"高级内容生成失败，切换到基础生成: {str(content_error)}")
            update_progress(0.4, "高级内容生成失败，切换到基础生成...")
            
            # 使用基础生成方式
            service = AIServiceFactory.create_service(ai_service_type)
            outline = service.generate_document_outline(topic, doc_type)
            document_content = {"title": topic, "sections": outline or []}
        
        # 根据文档类型生成最终文档
        update_progress(0.8, "生成最终文档文件...")
        
        try:
            if doc_type == "ppt":
                # 生成PPT
                ppt_generator = PPTGenerator(ai_service_type)
                output_path = ppt_generator.generate(topic, document_content.get("sections", []), template_id)
                file_type = "pptx"
            elif doc_type == "word":
                # 生成Word文档
                word_generator = WordGenerator(ai_service_type)
                output_path = word_generator.generate(topic, document_content.get("sections", []), template_id)
                file_type = "docx"
            elif doc_type == "pdf":
                # 生成PDF文档
                pdf_generator = PDFGenerator(ai_service_type)
                output_path = pdf_generator.generate(topic, document_content.get("sections", []), template_id)
                file_type = "pdf"
            else:
                raise ValueError(f"不支持的文档类型: {doc_type}")
                
            if not output_path:
                raise ValueError("文档生成失败，请检查内容或重试")
                
            # 生成下载和预览URL
            base_name = f"{topic}_{'presentation' if doc_type == 'ppt' else 'document'}.{file_type}"
            base_url = "http://localhost:8001"  # 应该从配置中获取
            download_url = f"{base_url}/downloads/{base_name}"
            preview_url = f"{base_url}/previews/{base_name}"
            
            # 更新任务状态为完成
            generation_tasks[doc_id].update({
                "status": "completed",
                "progress": 1.0,
                "message": "文档生成完成",
                "download_url": download_url,
                "preview_url": preview_url
            })
            
            logger.info(f"高级文档生成完成: ID={doc_id}, 文件={base_name}")
            
        except Exception as doc_error:
            # 文档生成过程中出错
            logger.error(f"生成文档文件时出错: {str(doc_error)}")
            generation_tasks[doc_id]["status"] = "failed"
            generation_tasks[doc_id]["message"] = f"生成文档失败: {str(doc_error)}"
            return
        
    except Exception as e:
        # 如果发生错误，更新状态为失败
        logger.error(f"高级文档生成错误: {str(e)}")
        generation_tasks[doc_id]["status"] = "failed"
        generation_tasks[doc_id]["message"] = f"生成失败: {str(e)}" 