import os
from typing import List, Dict, Any, Optional
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import datetime

from .ai_service_factory import AIServiceFactory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFGenerator:
    """
    生成PDF文档
    """
    def __init__(self, ai_service_type: str = "deepseek"):
        # 修正路径：生成文档目录和app是同级的
        self.output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_docs"))
        logger.info(f"PDF生成器输出目录: {self.output_dir}")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 确保目录权限正确
        try:
            os.chmod(self.output_dir, 0o777)
        except Exception as e:
            logger.warning(f"无法修改目录权限: {e}")
            
        self.ai_service = AIServiceFactory.create_service(ai_service_type)
    
    def generate(self, topic: str, outline: List[Dict[str, Any]], template_id: Optional[str] = None, max_pages: Optional[int] = None) -> Optional[str]:
        """
        生成PDF文档
        
        Args:
            topic: 主题
            outline: 大纲内容
            template_id: 模板ID（当前不使用）
            max_pages: 最大页数限制
            
        Returns:
            生成的PDF文件路径
        """
        try:
            logger.info(f"开始生成PDF文档: 主题='{topic}', 章节数={len(outline)}")
            
            # 创建报告样式
            styles = getSampleStyleSheet()
            
            # 自定义样式
            styles.add(ParagraphStyle(
                name='Heading1',
                parent=styles['Heading1'],
                fontName='Times-Bold',
                fontSize=18,
                spaceAfter=12
            ))
            
            styles.add(ParagraphStyle(
                name='Heading2',
                parent=styles['Heading2'],
                fontName='Times-Bold',
                fontSize=14,
                spaceAfter=8
            ))
            
            styles.add(ParagraphStyle(
                name='Normal_Justified',
                parent=styles['Normal'],
                fontName='Times-Roman',
                fontSize=12,
                alignment=4,  # 两端对齐
                spaceAfter=10,
                firstLineIndent=20
            ))
            
            # 使用安全的文件名
            sanitized_topic = self._sanitize_filename(topic)
            # 确保文件保存到 downloads 子目录
            downloads_dir = os.path.join(self.output_dir, "downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            file_path = os.path.join(downloads_dir, f"{sanitized_topic}_report.pdf")
            
            logger.info(f"PDF将保存到: {file_path}")
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            logger.info(f"创建新的PDF文档对象，页面大小: {letter}")
            
            # 创建内容元素列表
            elements = []
            
            # 添加标题页
            logger.info("添加标题页")
            elements.append(Paragraph(topic, styles['Heading1']))
            elements.append(Paragraph("AI自动生成的文档", styles['Heading2']))
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph(datetime.datetime.now().strftime("%Y年%m月%d日"), styles['Normal_Justified']))
            elements.append(PageBreak())
            
            # 添加目录
            logger.info("添加目录")
            elements.append(Paragraph("目录", styles['Heading1']))
            elements.append(Spacer(1, 0.25*inch))
            
            # 估算固定元素数量和页数（标题页和目录页）
            fixed_elements = len(elements)
            elements_per_page = 20  # 估计每页的元素数量
            fixed_pages = 2  # 标题页和目录页
            
            # 如果有页数限制，可能需要裁剪章节
            if max_pages:
                available_pages = max_pages - fixed_pages
                if available_pages <= 0:
                    logger.warning(f"页数限制({max_pages})太小，至少需要{fixed_pages}页基本内容，将使用最小合理值")
                    available_pages = 1
                
                # 如果章节数超过可用页数，需要裁剪章节
                if len(outline) > available_pages:
                    logger.warning(f"章节数({len(outline)})超过可用页数({available_pages})，将裁剪章节")
                    # 保留最重要的章节（如开头和结尾章节）
                    if available_pages >= 2:
                        outline = outline[:available_pages-1] + [outline[-1]]
                    else:
                        outline = outline[:available_pages]
                
                # 重新计算每个章节可用的页数
                available_pages = max_pages - fixed_pages
                pages_per_section = available_pages // len(outline)
                remaining_pages = available_pages % len(outline)
                
                # 分配给每个章节的页数
                section_page_allocation = [pages_per_section] * len(outline)
                # 将剩余页数分配给前面的章节
                for i in range(remaining_pages):
                    section_page_allocation[i] += 1
                
                logger.info(f"章节页数分配: {section_page_allocation}")
            
            # 更新目录（使用可能裁剪后的大纲）
            for i, section in enumerate(outline):
                section_title = section.get("title", "未知章节")
                elements.append(Paragraph(f"{i+1}. {section_title}", styles['Normal_Justified']))
                
                # 添加子章节到目录
                subsections = section.get("subsections", [])
                for j, subsection in enumerate(subsections):
                    subsection_title = subsection.get("title", "未知子章节")
                    elements.append(Paragraph(f"   {i+1}.{j+1} {subsection_title}", styles['Normal_Justified']))
            
            elements.append(PageBreak())
            
            # 添加章节内容
            total_elements = len(elements)
            for section_index, section in enumerate(outline):
                section_title = section.get("title", "未知章节")
                logger.info(f"处理章节 {section_index+1}/{len(outline)}: '{section_title}'")
                
                # 如果有页数限制，计算本章节可用的元素数量
                max_section_elements = None
                if max_pages and 'section_page_allocation' in locals():
                    max_section_elements = section_page_allocation[section_index] * elements_per_page
                    logger.info(f"  章节 '{section_title}' 可用页数: {section_page_allocation[section_index]}，估计元素数: {max_section_elements}")
                
                # 记录章节开始位置
                section_start_elements = len(elements)
                
                # 添加章节标题
                elements.append(Paragraph(f"{section_index+1}. {section_title}", styles['Heading1']))
                
                # 生成章节内容
                content = self.ai_service.generate_section_content(topic, section_title, "pdf")
                paragraphs = content.strip().split('\n\n')
                for p_text in paragraphs:
                    if p_text:
                        elements.append(Paragraph(p_text.strip(), styles['Normal_Justified']))
                
                # 处理子章节
                subsections = section.get("subsections", [])
                if subsections:
                    logger.info(f"  章节 '{section_title}' 包含 {len(subsections)} 个子章节")
                    
                    for subsection_index, subsection in enumerate(subsections):
                        subsection_title = subsection.get("title", "未知子章节")
                        logger.info(f"    处理子章节 {subsection_index+1}/{len(subsections)}: '{subsection_title}'")
                        
                        # 添加子章节标题
                        elements.append(Paragraph(
                            f"{section_index+1}.{subsection_index+1} {subsection_title}", 
                            styles['Heading2']
                        ))
                        
                        # 生成子章节内容
                        subcontent = self.ai_service.generate_section_content(topic, subsection_title, "pdf")
                        subparagraphs = subcontent.strip().split('\n\n')
                        for p_text in subparagraphs:
                            if p_text:
                                elements.append(Paragraph(p_text.strip(), styles['Normal_Justified']))
                
                # 检查是否超出章节限制，如果是则裁剪
                if max_section_elements:
                    section_elements = len(elements) - section_start_elements
                    if section_elements > max_section_elements:
                        logger.warning(f"  章节 '{section_title}' 元素数({section_elements})超过限制({max_section_elements})，进行裁剪")
                        # 保留所有标题元素，裁剪内容元素
                        elements = elements[:section_start_elements + max_section_elements]
                
                total_elements = len(elements)
            
            # 添加参考文献
            logger.info("添加参考文献")
            elements.append(PageBreak())
            elements.append(Paragraph("参考文献", styles['Heading1']))
            elements.append(Spacer(1, 0.25*inch))
            
            # 生成一些模拟的参考文献
            references = [
                f"[1] AI文档生成系统. (2023). {topic}研究综述.",
                f"[2] 智能文档分析小组. (2023). {topic}的最新进展.",
                f"[3] 文档自动化协会. (2022). {topic}标准与实践."
            ]
            
            for ref in references:
                elements.append(Paragraph(ref, styles['Normal_Justified']))
                elements.append(Spacer(1, 0.1*inch))
            
            # 构建文档
            logger.info("构建PDF文档")
            doc.build(elements)
            
            # 估算页数
            total_elements = len(elements) - fixed_elements
            page_count = (total_elements // elements_per_page) + fixed_pages
            logger.info(f"PDF文档生成成功: 约 {page_count} 页, 保存至: {file_path}")
            
            if max_pages:
                logger.info(f"页数限制: {max_pages} 页, 估计实际生成: {page_count} 页")
                if page_count > max_pages:
                    logger.warning(f"生成的页数({page_count})可能超过限制({max_pages})，但已尽量控制内容量")
            
            return file_path
            
        except Exception as e:
            logger.error(f"生成PDF文档时出错: {str(e)}")
            return None 

    def _sanitize_filename(self, filename: str) -> str:
        """
        对文件名进行安全处理
        """
        # 替换非法字符为下划线
        sanitized = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in filename)
        # 确保文件名长度不超过255个字符
        return sanitized[:255] 