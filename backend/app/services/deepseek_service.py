import logging
from typing import List, Dict, Any, Optional

from .ai_service_interface import AIServiceInterface
from .deepseek_client import DeepSeekClient
from .outline_generator import OutlineGenerator
from .content_generator import ContentGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekService(AIServiceInterface):
    """
    DeepSeek服务，实现AI服务接口
    这是一个门面类，整合了各个组件的功能
    """
    
    def __init__(self):
        """
        初始化DeepSeek服务
        """
        # 初始化AI客户端
        self.client = DeepSeekClient()
        
        # 初始化大纲生成器
        self.outline_generator = OutlineGenerator(self.client)
        
        # 初始化内容生成器
        self.content_generator = ContentGenerator(self.client)
        
        logger.info("DeepSeek服务初始化完成")
    
    def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """
        生成文本完成
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制随机性
            max_tokens: 生成的最大token数
            
        Returns:
            生成的文本，如果请求失败则返回None
        """
        try:
            # 调用AI客户端
            response = self.client.call_api(messages, temperature, max_tokens)
            if not response:
                return None
            
            # 提取内容
            return self.client.extract_response_content(response)
            
        except Exception as e:
            logger.error(f"生成文本完成时出错: {str(e)}")
            return None
    
    def call_api(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> Optional[Dict[str, Any]]:
        """
        调用AI API
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制随机性
            max_tokens: 生成的最大token数
            
        Returns:
            API响应，如果请求失败则返回None
        """
        try:
            return self.client.call_api(messages, temperature, max_tokens)
        except Exception as e:
            logger.error(f"调用API时出错: {str(e)}")
            return None
    
    def generate_document_outline(self, topic: str, doc_type: str, additional_prompt: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        生成文档大纲
        
        Args:
            topic: 文档主题
            doc_type: 文档类型 (ppt, word, pdf)
            additional_prompt: 附加提示词
            
        Returns:
            文档大纲，如果生成失败则返回None
        """
        return self.outline_generator.generate_document_outline(topic, doc_type, additional_prompt)
    
    def generate_section_content(self, topic: str, section_title: str, doc_type: str, additional_prompt: Optional[str] = None) -> str:
        """
        生成文档章节内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            doc_type: 文档类型 (ppt, word, pdf)
            additional_prompt: 附加提示词
            
        Returns:
            章节内容
        """
        return self.content_generator.generate_section_content(topic, section_title, doc_type, additional_prompt)
    
    def generate_slide_content(self, topic: str, section_title: str, slide_title: str, slide_type: str) -> Dict[str, Any]:
        """
        生成幻灯片内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            slide_title: 幻灯片标题
            slide_type: 幻灯片类型 (content, two_column, image_content)
            
        Returns:
            幻灯片内容
        """
        return self.content_generator.generate_slide_content(topic, section_title, slide_title, slide_type)
        
    async def generate_optimized_title(self, prompt: str) -> Optional[str]:
        """
        标题智能体：生成优化的文档标题
        
        Args:
            prompt: 提示词，包含主题和上下文信息
            
        Returns:
            优化后的标题，如果生成失败则返回None
        """
        try:
            logger.info(f"生成优化标题，提示词: {prompt[:100]}...")
            
            messages = [{"role": "user", "content": prompt}]
            # 使用较低的温度使标题更精确
            completion = self.generate_completion(messages, temperature=0.5, max_tokens=100)
            
            if not completion:
                return None
                
            # 清理标题（去除引号和多余空格）
            title = completion.strip().replace('"', '').replace("'", "")
            
            logger.info(f"生成的优化标题: {title}")
            return title
        except Exception as e:
            logger.error(f"生成优化标题时出错: {str(e)}")
            return None
            
    async def generate_slides_content(self, 
                                    topic: str, 
                                    section_title: str,
                                    slides: List[Dict[str, Any]],
                                    prompt: str) -> Optional[List[Dict[str, Any]]]:
        """
        PPT内容智能体：为幻灯片生成详细内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            slides: 幻灯片信息列表
            prompt: 提示词
            
        Returns:
            包含详细内容的幻灯片列表，如果生成失败则返回None
        """
        try:
            logger.info(f"为章节'{section_title}'生成幻灯片内容，共{len(slides)}张幻灯片")
            
            # 为每张幻灯片生成内容
            enriched_slides = []
            for i, slide in enumerate(slides):
                slide_title = slide.get("title", "未知标题")
                slide_type = slide.get("type", "content")
                
                logger.info(f"处理幻灯片 {i+1}/{len(slides)}: '{slide_title}' (类型: {slide_type})")
                
                # 为当前幻灯片构建提示词
                slide_prompt = f"{prompt}\n\n当前处理的幻灯片: {slide_title}"
                
                # 生成幻灯片内容
                slide_content = self.content_generator.generate_slide_content(
                    topic, section_title, slide_title, slide_type
                )
                
                # 合并原始幻灯片信息和生成的内容
                enriched_slide = {**slide, **slide_content}
                enriched_slides.append(enriched_slide)
                
            logger.info(f"章节'{section_title}'的幻灯片内容生成完成")
            return enriched_slides
            
        except Exception as e:
            logger.error(f"生成幻灯片内容时出错: {str(e)}")
            return slides  # 返回原始幻灯片以避免完全失败
            
    async def generate_subsections_content(self,
                                        topic: str,
                                        section_title: str,
                                        subsections: List[Dict[str, Any]],
                                        prompt: str) -> Optional[List[Dict[str, Any]]]:
        """
        文档内容智能体：为文档子章节生成详细内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            subsections: 子章节信息列表
            prompt: 提示词
            
        Returns:
            包含详细内容的子章节列表，如果生成失败则返回None
        """
        try:
            logger.info(f"为章节'{section_title}'生成子章节内容，共{len(subsections)}个子章节")
            
            enriched_subsections = []
            for i, subsection in enumerate(subsections):
                subsection_title = subsection.get("title", "未知子章节")
                
                logger.info(f"处理子章节 {i+1}/{len(subsections)}: '{subsection_title}'")
                
                # 为当前子章节构建提示词
                subsection_prompt = f"{prompt}\n\n当前处理的子章节: {subsection_title}"
                
                # 生成子章节内容
                content = self.content_generator.generate_section_content(
                    topic, subsection_title, "word", subsection_prompt
                )
                
                # 合并原始子章节信息和生成的内容
                enriched_subsection = {
                    **subsection,
                    "content": content
                }
                enriched_subsections.append(enriched_subsection)
                
            logger.info(f"章节'{section_title}'的子章节内容生成完成")
            return enriched_subsections
            
        except Exception as e:
            logger.error(f"生成子章节内容时出错: {str(e)}")
            return subsections  # 返回原始子章节以避免完全失败