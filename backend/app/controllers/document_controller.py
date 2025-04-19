from typing import Any, Dict, List, Optional
from fastapi import BackgroundTasks, Depends, HTTPException
import uuid
from datetime import datetime
import logging
import re

from ..models.schemas import DocumentRequest, DocumentResponse, AdvancedDocumentRequest, GenerationStatus
from ..models.schemas import OutlinePreviewRequest, OutlinePreviewResponse, OutlineItem, OutlineConfirmRequest, OutlineUpdateRequest
from ..providers.ai.ai_provider import AIProvider
from ..providers.storage.storage_provider import StorageProvider
from ..providers.cache_provider import CacheProvider
from .base_controller import BaseController
from ..services.ppt_generator import PPTGenerator
from ..services.word_generator import WordGenerator
from ..services.pdf_generator import PDFGenerator

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
        self.outline_previews = {}  # 存储大纲预览
    
    async def title_agent(self, topic: str, doc_type: str, additional_info: Optional[str] = None) -> str:
        """
        标题生成智能体：根据主题和文档类型生成优化的标题
        
        Args:
            topic: 主题
            doc_type: 文档类型
            additional_info: 额外信息
            
        Returns:
            优化后的标题
        """
        # 检查主题是否是标题列表格式
        if "以下是" in topic and ("标题" in topic or "《" in topic):
            # 尝试提取实际主题
            import re
            # 尝试查找第一个引号包围的标题
            title_match = re.search(r'《([^》]+)》', topic)
            if title_match:
                actual_topic = title_match.group(1)
                logger.info(f"从标题列表中提取实际主题: '{actual_topic}'")
                topic = actual_topic
            else:
                # 尝试找到冒号后的第一个有意义的词组作为主题
                colon_match = re.search(r'[:：]\s*(.+?)(?=\s*\d|$)', topic)
                if colon_match:
                    actual_topic = colon_match.group(1).strip()
                    if len(actual_topic) > 3 and len(actual_topic) < 100:
                        logger.info(f"从冒号后提取实际主题: '{actual_topic}'")
                        topic = actual_topic
                else:
                    # 如果主题确实是标题列表，取"主题"之前的内容
                    theme_match = re.search(r'^(.+?)\s*(?:主题|标题)', topic)
                    if theme_match:
                        actual_topic = theme_match.group(1).strip()
                        if len(actual_topic) > 3:
                            logger.info(f"从主题前缀提取: '{actual_topic}'")
                            topic = actual_topic
        
        # 构建提示词，针对标题生成进行优化
        prompt = f"为以下主题创建一个引人注目、专业且简洁的标题，适合{doc_type}文档格式。\n\n主题: {topic}"
        
        if additional_info:
            prompt += f"\n\n额外背景信息: {additional_info}"
            
        # 可以使用不同的AI服务或参数配置专门优化标题生成
        try:
            title_result = await self.ai_provider.generate_optimized_title(prompt)
            logger.info(f"生成优化标题: '{title_result}' (原始主题: '{topic}')")
            return title_result if title_result else topic
        except Exception as e:
            logger.error(f"标题生成失败: {str(e)}")
            # 如果失败，返回原始主题作为备选
            return topic
    
    async def outline_agent(self, topic: str, doc_type: str, additional_info: Optional[str] = None, optimized_title: Optional[str] = None, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        大纲生成智能体：生成结构化的文档大纲
        
        Args:
            topic: 主题
            doc_type: 文档类型
            additional_info: 额外信息
            optimized_title: 优化后的标题
            max_pages: 最大页数限制
            
        Returns:
            文档大纲
        """
        # 使用优化的标题（如果有）
        title_to_use = optimized_title if optimized_title else topic
        
        # 构建专门针对大纲生成的提示词
        prompt = f"为标题为'{title_to_use}'的{doc_type}类型文档创建一个结构合理、内容全面的大纲。"
        
        # 添加页数限制
        if max_pages:
            if doc_type == "ppt":
                prompt += f"\n请确保大纲适合生成不超过{max_pages}张幻灯片的演示文稿。"
            elif doc_type == "word" or doc_type == "pdf":
                prompt += f"\n请确保大纲适合生成不超过{max_pages}页的文档。章节数量和深度应与此页数限制相适应。"
        
        if additional_info:
            prompt += f"\n\n请考虑以下额外信息: {additional_info}"
        
        # 添加特定文档类型的大纲要求
        if doc_type == "ppt":
            prompt += "\n请确保大纲适合演示文稿，包含引人注目的幻灯片标题和清晰的章节结构。每个章节应包含合理数量的幻灯片。"
        elif doc_type == "word":
            prompt += "\n请确保大纲有明确的章节和小节层级结构，适合学术或商业文档。"
        elif doc_type == "pdf":
            prompt += "\n请创建一个结构严谨的大纲，适合正式的PDF报告格式。"
        
        # 调用AI服务生成大纲，可以使用专门针对大纲生成的模型或配置
        try:
            outline = self.ai_provider.generate_document_outline(title_to_use, doc_type, prompt)
            if not outline:
                raise ValueError("大纲生成结果为空")
                
            logger.info(f"成功生成大纲: {len(outline)} 个章节")
            
            # 如果有页数限制，确认大纲在合理范围内
            if max_pages and doc_type == "ppt":
                total_slides = 0
                for section in outline:
                    if "slides" in section:
                        total_slides += len(section.get("slides", []))
                
                logger.info(f"大纲包含大约 {total_slides} 张幻灯片，页数限制为 {max_pages}")
                
                # 如果幻灯片数量明显超出限制，可以尝试重新生成
                if total_slides > max_pages * 1.5:
                    logger.warning(f"幻灯片数量 ({total_slides}) 明显超出限制 ({max_pages})，尝试优化大纲")
                    # 这里可以实现优化大纲的逻辑，简单起见暂不实现
            
            return outline
        except Exception as e:
            logger.error(f"大纲生成失败: {str(e)}")
            raise
    
    async def content_agent(
        self, 
        topic: str, 
        doc_type: str, 
        outline: List[Dict[str, Any]], 
        additional_info: Optional[str] = None,
        optimized_title: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        内容生成智能体：根据大纲生成详细内容
        
        Args:
            topic: 主题
            doc_type: 文档类型
            outline: 文档大纲
            additional_info: 额外信息
            optimized_title: 优化后的标题
            max_pages: 最大页数限制
            
        Returns:
            生成的详细内容
        """
        # 处理标题 - 确保标题是一个简短的字符串，而不是长文本或标题列表
        title_to_use = optimized_title if optimized_title else topic
        
        # 检查标题是否过长或包含标题列表格式
        if len(title_to_use) > 200 or "以下是" in title_to_use or "《" in title_to_use:
            # 尝试从标题中提取实际标题
            import re
            # 尝试查找《》格式的标题
            title_match = re.search(r'《([^》]+)》', title_to_use)
            if title_match:
                title_to_use = title_match.group(1)
                logger.info(f"从长格式标题中提取: '{title_to_use}'")
            else:
                # 如果标题过长，使用原始主题
                logger.warning(f"标题格式不正确或过长: '{title_to_use[:50]}...'，使用原始主题: '{topic}'")
                title_to_use = topic
        
        # 创建特定于内容生成的提示词
        base_prompt = f"基于以下大纲为'{title_to_use}'的{doc_type}文档创建详细、专业的内容。"
        
        # 添加页数限制
        if max_pages:
            if doc_type == "ppt":
                base_prompt += f"\n生成的内容应适合不超过{max_pages}张幻灯片的演示文稿。请确保内容简洁有力。"
            elif doc_type == "word":
                base_prompt += f"\n生成的内容应适合不超过{max_pages}页的Word文档。"
            elif doc_type == "pdf":
                base_prompt += f"\n生成的内容应适合不超过{max_pages}页的PDF文档。"
        
        if additional_info:
            base_prompt += f"\n\n应考虑的额外信息: {additional_info}"
        
        # 添加特定于文档类型的内容指导
        if doc_type == "ppt":
            base_prompt += "\n为每张幻灯片创建简洁有力的内容，包括要点和支持信息。避免过长的段落。每个要点应该简明扼要，易于理解和记忆。"
        elif doc_type == "word":
            base_prompt += "\n为每个章节和小节创建详细的内容，包括介绍性段落、支持性论点和总结。内容应专业且信息丰富，但避免过于冗长。"
        elif doc_type == "pdf":
            base_prompt += "\n创建专业、详细的内容，适合正式报告。确保逻辑流畅，论点清晰。内容应该既有深度又保持简明。"
        
        # 估算每个章节可分配的内容量
        if max_pages and len(outline) > 0:
            # 简单估算每个章节可分配的内容量
            sections_count = len(outline)
            pages_per_section = max_pages / sections_count
            
            base_prompt += f"\n考虑到总页数限制为{max_pages}页，该文档有{sections_count}个章节，平均每个章节应占用约{pages_per_section:.1f}页。请相应调整各章节内容的详细程度。"
        
        # 逐章节生成内容，可以并行处理以提高效率
        try:
            content_result = {"title": title_to_use, "sections": []}
            
            # 这里可以实现并行处理，但简单起见，先用串行方式
            for section_index, section in enumerate(outline):
                section_title = section["title"]
                logger.info(f"为章节 {section_index+1}/{len(outline)}: '{section_title}' 生成内容")
                
                # 为当前章节构建提示词
                section_prompt = f"{base_prompt}\n\n当前正在处理的章节: {section_title}"
                
                # 如果有页数限制，添加章节级别的页数指导
                if max_pages and len(outline) > 0:
                    if doc_type == "ppt" and "slides" in section:
                        slides_count = len(section.get("slides", []))
                        # 修复章节占比计算，使用总大纲中的幻灯片数量而非max_pages
                        total_slides = sum(len(s.get("slides", [])) for s in outline)
                        if total_slides > 0:
                            section_prompt += f"\n本章节包含{slides_count}张幻灯片，这占总幻灯片数的{slides_count/total_slides*100:.1f}%。请确保内容量适当。"
                        else:
                            section_prompt += f"\n本章节包含{slides_count}张幻灯片。请确保内容量适当。"
                    elif doc_type in ["word", "pdf"] and "subsections" in section:
                        subsections_count = len(section.get("subsections", []))
                        # 同样修复子章节占比计算
                        total_subsections = sum(len(s.get("subsections", [])) for s in outline)
                        if total_subsections > 0:
                            section_prompt += f"\n本章节有{subsections_count}个子章节，占总子章节数的{subsections_count/total_subsections*100:.1f}%。在总体页数限制下，请确保内容量适当。"
                        else:
                            section_prompt += f"\n本章节有{subsections_count}个子章节，在总体页数限制下，请确保内容量适当。"
                
                # 根据文档类型和章节内容调用AI服务
                if doc_type == "ppt" and "slides" in section:
                    # 为PPT幻灯片生成内容
                    enriched_slides = await self.ai_provider.generate_slides_content(
                        title_to_use, 
                        section_title,
                        section.get("slides", []),
                        section_prompt
                    )
                    section["slides"] = enriched_slides
                elif "subsections" in section:
                    # 为文档子章节生成内容
                    enriched_subsections = await self.ai_provider.generate_subsections_content(
                        title_to_use,
                        section_title,
                        section.get("subsections", []),
                        section_prompt
                    )
                    section["subsections"] = enriched_subsections
                
                content_result["sections"].append(section)
            
            logger.info(f"内容生成完成，共 {len(content_result['sections'])} 个章节")
            return content_result
            
        except Exception as e:
            logger.error(f"内容生成失败: {str(e)}")
            raise
    
    async def create_outline_preview(self, request: OutlinePreviewRequest, background_tasks: BackgroundTasks) -> OutlinePreviewResponse:
        """
        创建大纲预览
        
        Args:
            request: 大纲预览请求
            background_tasks: 后台任务队列
            
        Returns:
            大纲预览响应
        """
        # 创建预览ID
        preview_id = str(uuid.uuid4())
        
        # 尝试生成优化的标题
        optimized_title = await self.title_agent(request.topic, request.doc_type, request.additional_info)
        
        # 生成标题建议列表
        title_suggestions = await self._generate_title_suggestions(request.topic, request.doc_type, request.additional_info)
        
        # 生成大纲
        try:
            outline = await self.outline_agent(request.topic, request.doc_type, request.additional_info, optimized_title)
        except Exception as e:
            logger.error(f"大纲生成失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")
        
        # 将大纲转换为前端需要的格式
        outline_items = []
        
        for i, section in enumerate(outline):
            section_id = f"section_{i}"
            section_title = section.get("title", f"章节 {i+1}")
            
            # 添加章节
            outline_items.append(
                OutlineItem(
                    id=section_id,
                    title=section_title,
                    level=1,
                    parent_id=None,
                    order=i
                )
            )
            
            # 添加子章节/幻灯片内容
            if "slides" in section and request.doc_type == "ppt":
                for j, slide in enumerate(section["slides"]):
                    slide_id = f"{section_id}_slide_{j}"
                    slide_title = slide.get("title", f"幻灯片 {j+1}")
                    
                    outline_items.append(
                        OutlineItem(
                            id=slide_id,
                            title=slide_title,
                            level=2,
                            parent_id=section_id,
                            order=j
                        )
                    )
            elif "subsections" in section:
                for j, subsection in enumerate(section["subsections"]):
                    subsection_id = f"{section_id}_subsection_{j}"
                    subsection_title = subsection.get("title", f"子章节 {j+1}")
                    
                    outline_items.append(
                        OutlineItem(
                            id=subsection_id,
                            title=subsection_title,
                            level=2,
                            parent_id=section_id,
                            order=j
                        )
                    )
        
        # 保存大纲预览
        preview_data = {
            "id": preview_id,
            "topic": request.topic,
            "doc_type": request.doc_type,
            "additional_info": request.additional_info,
            "original_outline": outline,
            "optimized_title": optimized_title,
            "title_suggestions": title_suggestions,
            "created_at": datetime.now()
        }
        
        self.outline_previews[preview_id] = preview_data
        
        # 创建响应
        response = OutlinePreviewResponse(
            id=preview_id,
            topic=request.topic,
            doc_type=request.doc_type,
            outline_items=outline_items,
            created_at=datetime.now(),
            title_suggestions=title_suggestions,
            selected_title=optimized_title
        )
        
        # 在后台进一步丰富大纲内容
        background_tasks.add_task(self.enrich_outline_details, preview_id)
        
        return response

    async def _generate_title_suggestions(self, topic: str, doc_type: str, additional_info: Optional[str] = None) -> List[str]:
        """
        生成标题建议列表
        
        Args:
            topic: 主题
            doc_type: 文档类型
            additional_info: 额外信息
            
        Returns:
            标题建议列表
        """
        try:
            # 构建提示词，要求生成多个标题选项
            prompt = f"""为以下主题创建3-5个可选的标题建议，适合{doc_type}文档格式。这些标题应该专业、简洁、有吸引力。
            
            主题: {topic}
            
            请生成不同风格和结构的标题选项，以便用户可以选择。返回格式为标题列表，每行一个标题。"""
            
            if additional_info:
                prompt += f"\n\n额外背景信息参考: {additional_info}"
            
            # 调用AI服务生成标题
            result = await self.ai_provider.generate_completion([
                {"role": "system", "content": "你是一个创意标题生成专家，专长于为各类文档创建专业、吸引人的标题。"},
                {"role": "user", "content": prompt}
            ])
            
            # 解析标题列表
            if not result:
                return [topic]  # 如果失败返回原始主题作为唯一选项
            
            import re
            # 尝试解析出标题列表
            titles = []
            
            # 处理可能的编号格式 (1. 标题, 1) 标题, - 标题, • 标题)
            for line in result.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # 去除编号前缀
                clean_title = re.sub(r'^(\d+[\.\)、]|\-|\•|\*)\s*', '', line)
                
                # 去除引号
                clean_title = re.sub(r'^[\'\"「『]|[\'\"」』]$', '', clean_title)
                
                if clean_title and len(clean_title) > 3:  # 忽略过短的标题
                    titles.append(clean_title)
            
            # 如果无法解析出标题，返回原始主题
            if not titles:
                titles = [topic]
                
            # 确保返回的标题列表中包含原始主题
            if topic not in titles:
                titles.append(topic)
                
            # 对标题进行去重并限制数量
            titles = list(dict.fromkeys(titles))[:5]  # 最多返回5个标题
            
            logger.info(f"为主题 '{topic}' 生成了 {len(titles)} 个标题建议")
            return titles
            
        except Exception as e:
            logger.error(f"生成标题建议时出错: {str(e)}")
            return [topic]  # 失败时返回原始主题

    async def update_outline_preview(self, preview_id: str, request: OutlineUpdateRequest) -> OutlinePreviewResponse:
        """
        更新大纲预览
        
        Args:
            preview_id: 预览ID
            request: 更新请求
            
        Returns:
            更新后的大纲预览响应
        """
        if preview_id not in self.outline_previews:
            raise HTTPException(status_code=404, detail="预览不存在")
        
        preview = self.outline_previews[preview_id]
        
        # 更新大纲项
        if request.outline_items:
            updated_outline = []
            
            # 按照顺序重新组织大纲
            section_items = {}
            
            # 按照层级分组
            level_1_items = []
            level_2_items = {}
            
            for item in request.outline_items:
                if item.level == 1:
                    level_1_items.append(item)
                else:
                    if item.parent_id not in level_2_items:
                        level_2_items[item.parent_id] = []
                    level_2_items[item.parent_id].append(item)
            
            # 按顺序排序
            level_1_items.sort(key=lambda x: x.order)
            
            for parent_id, items in level_2_items.items():
                level_2_items[parent_id] = sorted(items, key=lambda x: x.order)
            
            # 重建大纲
            for section in level_1_items:
                section_dict = {
                    "title": section.title
                }
                
                # 添加子项（幻灯片或子章节）
                if section.id in level_2_items:
                    if preview["doc_type"] == "ppt":
                        section_dict["slides"] = [
                            {"title": item.title} for item in level_2_items[section.id]
                        ]
                    else:
                        section_dict["subsections"] = [
                            {"title": item.title} for item in level_2_items[section.id]
                        ]
                
                updated_outline.append(section_dict)
            
            # 更新预览中的大纲
            preview["original_outline"] = updated_outline
        
        # 更新主题（如果提供）
        if request.topic:
            preview["topic"] = request.topic
            
        # 更新选定的标题（如果提供）
        if request.selected_title:
            preview["selected_title"] = request.selected_title
        
        # 重新构建响应
        response_items = []
        
        # 按更新后的大纲重新构建项目
        for i, section in enumerate(preview["original_outline"]):
            section_id = f"section_{i}"
            
            response_items.append(
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
                    
                    response_items.append(
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
                    
                    response_items.append(
                        OutlineItem(
                            id=subsection_id,
                            title=subsection["title"],
                            level=2,
                            parent_id=section_id,
                            order=j
                        )
                    )
        
        # 创建响应
        return OutlinePreviewResponse(
            id=preview_id,
            topic=preview["topic"],
            doc_type=preview["doc_type"],
            outline_items=response_items,
            created_at=preview["created_at"],
            title_suggestions=preview.get("title_suggestions", []),
            selected_title=preview.get("selected_title", preview["topic"])
        )

    async def confirm_outline(
        self, 
        request: OutlineConfirmRequest, 
        background_tasks: BackgroundTasks
    ) -> DocumentResponse:
        """
        确认大纲并开始生成文档
        
        Args:
            request: 确认请求
            background_tasks: 后台任务队列
            
        Returns:
            文档响应
        """
        if request.preview_id not in self.outline_previews:
            raise HTTPException(status_code=404, detail="预览不存在")
        
        preview = self.outline_previews[request.preview_id]
        
        # 使用选定的标题（如果提供）
        if request.selected_title:
            preview["selected_title"] = request.selected_title
        elif "selected_title" not in preview:
            # 如果没有提供选定标题且预览中没有，使用优化标题或原始主题
            preview["selected_title"] = preview.get("optimized_title", preview["topic"])
            
        # 清理标题以便安全使用
        preview["selected_title"] = self._sanitize_filename(preview["selected_title"])
        
        # 生成文档ID
        doc_id = str(uuid.uuid4())
        
        # 创建响应
        response = DocumentResponse(
            id=doc_id,
            topic=preview["topic"],
            doc_type=preview["doc_type"],
            status="queued",
            created_at=datetime.now()
        )
        
        # 存储任务状态
        self.generation_tasks[doc_id] = {
            "status": "queued",
            "progress": 0.0,
            "message": "已确认大纲，排队等待生成文档",
            "topic": preview["topic"],
            "doc_type": preview["doc_type"],
            "selected_title": preview["selected_title"]
        }
        
        # 添加后台任务
        background_tasks.add_task(
            self.generate_document_from_outline,
            doc_id=doc_id,
            preview_id=request.preview_id,
            template_id=request.template_id,
            max_pages=request.max_pages
        )
        
        return response
    
    async def generate_document_from_outline(
        self,
        doc_id: str,
        preview_id: str,
        template_id: Optional[str] = None,
        max_pages: Optional[int] = None
    ):
        """
        从大纲生成文档
        
        Args:
            doc_id: 文档ID
            preview_id: 预览ID
            template_id: 模板ID（可选）
            max_pages: 最大页数（可选）
        """
        try:
            if preview_id not in self.outline_previews:
                self.generation_tasks[doc_id]["status"] = "failed"
                self.generation_tasks[doc_id]["message"] = "找不到预览大纲"
                return
            
            preview = self.outline_previews[preview_id]
            
            # 更新任务状态
            self.generation_tasks[doc_id].update({
                "status": "processing",
                "progress": 0.1,
                "message": "开始生成文档内容..."
            })
            
            # 提取必要信息
            topic = preview["topic"]
            doc_type = preview["doc_type"]
            additional_info = preview.get("additional_info", "")
            original_outline = preview["original_outline"]
            selected_title = preview.get("selected_title", preview.get("optimized_title", topic))
            
            # 更新任务状态
            self.generation_tasks[doc_id].update({
                "progress": 0.3,
                "message": "正在生成文档内容..."
            })
            
            # 生成详细内容
            try:
                content_result = await self.content_agent(
                    topic, 
                    doc_type, 
                    original_outline, 
                    additional_info, 
                    selected_title, 
                    max_pages
                )
            except Exception as e:
                logger.error(f"内容生成失败: {str(e)}")
                # 如果内容生成失败，使用大纲作为基础继续生成
                content_result = {"title": selected_title, "sections": original_outline}
            
            # 更新进度
            self.generation_tasks[doc_id]["progress"] = 0.6
            self.generation_tasks[doc_id]["message"] = "内容准备完成，开始创建文档..."
            
            # 根据文档类型生成文件
            file_path = None
            
            if doc_type == "ppt":
                generator = PPTGenerator()
                file_path = generator.generate(selected_title, content_result["sections"], template_id, max_pages)
            elif doc_type == "word":
                generator = WordGenerator()
                file_path = generator.generate(selected_title, content_result["sections"], template_id, max_pages)
            elif doc_type == "pdf":
                generator = PDFGenerator()
                file_path = generator.generate(selected_title, content_result["sections"], template_id, max_pages)
            
            if not file_path:
                raise ValueError("文档生成失败")
            
            # 文件生成成功
            # 提取文件名
            import os
            file_name = os.path.basename(file_path)
            
            self.generation_tasks[doc_id]["status"] = "completed"
            self.generation_tasks[doc_id]["progress"] = 1.0
            self.generation_tasks[doc_id]["message"] = "文档生成完成"
            self.generation_tasks[doc_id]["download_url"] = f"/downloads/{file_name}"
            self.generation_tasks[doc_id]["preview_url"] = f"/previews/{file_name}"
            self.generation_tasks[doc_id]["created_at"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"从大纲生成文档时出错: {str(e)}")
            self.generation_tasks[doc_id]["status"] = "failed"
            self.generation_tasks[doc_id]["message"] = f"生成失败: {str(e)}"
    
    def _get_file_extension(self, doc_type: str) -> str:
        """获取文件扩展名"""
        if doc_type == "ppt":
            return "pptx"
        elif doc_type == "word":
            return "docx"
        else:
            return "pdf"
    
    def _sanitize_filename(self, name: str) -> str:
        """
        将主题或标题名称转换为有效的文件名
        
        Args:
            name: 原始名称
            
        Returns:
            有效的文件名
        """
        # 移除不合法的文件名字符
        sanitized = re.sub(r'[\\/*?:"<>|]', '', name)
        # 移除换行符并替换多个空格为单个空格
        sanitized = re.sub(r'\s+', ' ', sanitized.replace('\n', ' '))
        # 限制长度
        max_length = 100
        if len(sanitized) > max_length:
            # 如果太长，截断并添加提示
            sanitized = sanitized[:max_length] + "..."
        # 确保文件名不为空
        if not sanitized.strip():
            sanitized = "AI_document"
        return sanitized.strip()
    
    async def create_document(
        self, 
        request: DocumentRequest, 
    ) -> DocumentResponse:
        # Implementation of create_document method
        pass

    async def enrich_outline_details(self, preview_id: str):
        """
        丰富大纲详情，在后台运行以提供更详细的大纲内容
        
        Args:
            preview_id: 预览ID
        """
        try:
            if preview_id not in self.outline_previews:
                logger.warning(f"尝试丰富不存在的大纲预览: {preview_id}")
                return
                
            preview = self.outline_previews[preview_id]
            logger.info(f"开始丰富大纲 {preview_id} 的详情")
            
            topic = preview["topic"]
            doc_type = preview["doc_type"]
            additional_info = preview.get("additional_info", "")
            outline = preview["original_outline"]
            
            # 这里可以添加更多丰富大纲的逻辑
            # 例如为每个章节添加更详细的描述、关键点、参考资料等
            
            for section in outline:
                section_title = section["title"]
                
                # 生成章节描述（简单示例）
                try:
                    prompt = f"为'{topic}'文档中的章节'{section_title}'生成一段简短描述，说明该章节将包含哪些内容和要点。"
                    
                    if additional_info:
                        prompt += f"\n\n参考信息: {additional_info}"
                        
                    description_result = await self.ai_provider.generate_completion([
                        {"role": "system", "content": "你是一个专业的文档内容规划助手，擅长概括章节内容要点。"},
                        {"role": "user", "content": prompt}
                    ])
                    
                    if description_result:
                        # 添加生成的描述到章节
                        section["description"] = description_result.strip()
                        logger.info(f"为章节 '{section_title}' 添加了描述")
                except Exception as e:
                    logger.error(f"为章节 '{section_title}' 生成描述时出错: {str(e)}")
            
            # 更新预览数据
            self.outline_previews[preview_id]["original_outline"] = outline
            self.outline_previews[preview_id]["enriched"] = True
            
            logger.info(f"大纲 {preview_id} 的详情丰富完成")
            
        except Exception as e:
            logger.error(f"丰富大纲详情时出错: {str(e)}")
    
    async def get_document_status(self, doc_id: str) -> GenerationStatus:
        """
        获取文档生成任务的状态
        
        Args:
            doc_id: 文档ID
            
        Returns:
            生成状态信息
            
        Raises:
            HTTPException: 如果文档不存在
        """
        if doc_id not in self.generation_tasks:
            logger.warning(f"尝试获取不存在的文档状态: {doc_id}")
            raise HTTPException(status_code=404, detail="文档不存在")
        
        task_info = self.generation_tasks[doc_id]
        
        # 构建生成状态响应
        return GenerationStatus(
            id=doc_id,
            status=task_info.get("status", "unknown"),
            progress=task_info.get("progress", 0.0),
            message=task_info.get("message", ""),
            download_url=task_info.get("download_url"),
            preview_url=task_info.get("preview_url"),
            created_at=task_info.get("created_at", datetime.now().isoformat())
        )
    