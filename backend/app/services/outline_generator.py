import json
import logging
import re
from typing import List, Dict, Any, Optional

from .ai_client import AIClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutlineGenerator:
    """
    文档大纲生成器
    """
    
    def __init__(self, ai_client: AIClient):
        """
        初始化大纲生成器
        
        Args:
            ai_client: AI客户端实例
        """
        self.ai_client = ai_client
        logger.info("大纲生成器初始化完成")
    
    def generate_document_outline(self, topic: str, doc_type: str, additional_prompt: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        生成文档大纲
        
        Args:
            topic: 文档主题
            doc_type: 文档类型 (ppt, word, pdf)
            additional_prompt: 附加提示词，用于自定义大纲生成过程
            
        Returns:
            文档大纲，如果生成失败则返回None
        """
        try:
            logger.info(f"开始为主题 '{topic}' 生成 {doc_type} 类型的文档大纲")
            if additional_prompt:
                logger.info(f"附加提示词: {additional_prompt[:100]}...")
            
            # 1. 首先生成主要章节
            main_sections = self._generate_main_sections(topic, doc_type, additional_prompt)
            if not main_sections:
                logger.error(f"生成主要章节失败: 主题={topic}, 类型={doc_type}")
                return None
            
            logger.info(f"成功生成主要章节: {len(main_sections)} 个章节")
            for i, section in enumerate(main_sections):
                logger.info(f"  章节 {i+1}: {section.get('title', '未知标题')}")
            
            # 2. 然后为每个章节生成子章节
            outline = []
            for section in main_sections:
                section_title = section.get("title", "")
                logger.info(f"为章节 '{section_title}' 生成详细内容")
                
                section_detail = self._generate_section_detail(topic, section, doc_type, additional_prompt)
                if section_detail:
                    outline.append(section_detail)
                    
                    # 记录子章节或幻灯片信息
                    if doc_type == "ppt" and "slides" in section_detail:
                        slides = section_detail.get("slides", [])
                        logger.info(f"  生成了 {len(slides)} 张幻灯片")
                        for i, slide in enumerate(slides[:3]):  # 只记录前3张幻灯片
                            logger.info(f"    幻灯片 {i+1}: {slide.get('title', '未知标题')} ({slide.get('type', 'content')})")
                        if len(slides) > 3:
                            logger.info(f"    ... 还有 {len(slides) - 3} 张幻灯片")
                    elif "subsections" in section_detail:
                        subsections = section_detail.get("subsections", [])
                        logger.info(f"  生成了 {len(subsections)} 个子章节")
                        for i, subsection in enumerate(subsections[:3]):  # 只记录前3个子章节
                            logger.info(f"    子章节 {i+1}: {subsection.get('title', '未知标题')}")
                        if len(subsections) > 3:
                            logger.info(f"    ... 还有 {len(subsections) - 3} 个子章节")
            
            logger.info(f"文档大纲生成完成: 共 {len(outline)} 个章节")
            return outline
            
        except Exception as e:
            logger.error(f"生成大纲时出错: {str(e)}")
            return None
    
    def _generate_main_sections(self, topic: str, doc_type: str, additional_prompt: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        生成文档的主要章节
        
        Args:
            topic: 文档主题
            doc_type: 文档类型
            additional_prompt: 附加提示词
            
        Returns:
            主要章节列表，如果生成失败则返回None
        """
        try:
            # 构建提示
            prompt = self._build_main_sections_prompt(topic, doc_type, additional_prompt)
            
            # 调用AI客户端
            messages = [
                {"role": "system", "content": "你是一个专业的文档生成助手，擅长创建结构化的文档大纲。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.ai_client.call_api(messages)
            if not response:
                return self._get_mock_main_sections(topic, doc_type)
            
            # 提取内容
            content = self.ai_client.extract_response_content(response)
            if not content:
                return self._get_mock_main_sections(topic, doc_type)
            
            # 解析内容
            sections = self._extract_sections_from_text(content)
            if not sections:
                return self._get_mock_main_sections(topic, doc_type)
            
            return sections
            
        except Exception as e:
            logger.error(f"生成主要章节时出错: {str(e)}")
            return self._get_mock_main_sections(topic, doc_type)
    
    def _generate_section_detail(self, topic: str, section: Dict[str, Any], doc_type: str, additional_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        为章节生成详细内容
        
        Args:
            topic: 文档主题
            section: 章节信息
            doc_type: 文档类型
            additional_prompt: 附加提示词
            
        Returns:
            详细的章节信息，如果生成失败则返回None
        """
        try:
            section_title = section.get("title", "")
            if not section_title:
                return None
            
            # 构建提示
            prompt = self._build_section_detail_prompt(topic, section_title, doc_type, additional_prompt)
            
            # 调用AI客户端
            messages = [
                {"role": "system", "content": "你是一个专业的文档生成助手，擅长创建结构化的文档大纲。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.ai_client.call_api(messages)
            if not response:
                return self._get_mock_section_detail(section, doc_type)
            
            # 提取内容
            content = self.ai_client.extract_response_content(response)
            if not content:
                return self._get_mock_section_detail(section, doc_type)
            
            # 解析内容
            if doc_type == "ppt":
                subsections = self._extract_slides_from_text(content, section_title)
                return {
                    "title": section_title,
                    "slides": subsections
                }
            else:
                subsections = self._extract_subsections_from_text(content, section_title)
                return {
                    "title": section_title,
                    "subsections": subsections
                }
            
        except Exception as e:
            logger.error(f"生成章节详情时出错: {str(e)}")
            return self._get_mock_section_detail(section, doc_type)
    
    def _build_main_sections_prompt(self, topic: str, doc_type: str, additional_prompt: Optional[str] = None) -> str:
        """
        构建生成主要章节的提示
        
        Args:
            topic: 文档主题
            doc_type: 文档类型
            additional_prompt: 附加提示词
            
        Returns:
            提示文本
        """
        base_prompt = ""
        if doc_type == "ppt":
            base_prompt = f"""
            请为主题"{topic}"创建一个PPT演示文稿的主要章节列表。
            
            要求:
            1. 创建5-7个主要章节
            2. 每个章节应该是主题的一个重要方面
            3. 章节应该有逻辑顺序，从介绍到结论
            """
        else:
            base_prompt = f"""
            请为主题"{topic}"创建一个文档的主要章节列表。
            
            要求:
            1. 创建5-7个主要章节
            2. 每个章节应该是主题的一个重要方面
            3. 章节应该有逻辑顺序，从介绍到结论
            """
            
        # 添加附加提示词
        if additional_prompt:
            base_prompt += f"\n\n附加要求:\n{additional_prompt}\n"
            
        # 添加JSON格式输出要求
        base_prompt += """
            请以JSON格式返回，格式如下:
            [
                {"title": "章节1标题"},
                {"title": "章节2标题"},
                ...
            ]
            
            确保JSON格式正确，可以直接解析。
            """
            
        return base_prompt
    
    def _build_section_detail_prompt(self, topic: str, section_title: str, doc_type: str, additional_prompt: Optional[str] = None) -> str:
        """
        构建生成章节详情的提示
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            doc_type: 文档类型
            additional_prompt: 附加提示词
            
        Returns:
            提示文本
        """
        base_prompt = ""
        if doc_type == "ppt":
            base_prompt = f"""
            请为主题"{topic}"中的章节"{section_title}"创建详细的PPT幻灯片内容。
            
            要求:
            1. 创建3-5个幻灯片
            2. 每个幻灯片应该有一个标题和类型
            3. 类型可以是"content"(普通内容)、"two_column"(两列内容)或"image_content"(带图片的内容)
            """
        else:
            base_prompt = f"""
            请为主题"{topic}"中的章节"{section_title}"创建详细的子章节内容。
            
            要求:
            1. 创建3-5个子章节
            2. 每个子章节应该详细探讨章节的一个方面
            3. 子章节应该有逻辑连贯性
            """
            
        # 添加附加提示词
        if additional_prompt:
            base_prompt += f"\n\n附加要求:\n{additional_prompt}\n"
        
        # 添加JSON格式输出要求
        if doc_type == "ppt":
            base_prompt += """
            请以JSON格式返回，格式如下:
            [
                {
                    "title": "幻灯片1标题",
                    "type": "content"
                },
                {
                    "title": "幻灯片2标题",
                    "type": "two_column"
                },
                ...
            ]
            
            确保JSON格式正确，可以直接解析。
            """
        else:
            base_prompt += """
            请以JSON格式返回，格式如下:
            [
                {
                    "title": "子章节1标题"
                },
                {
                    "title": "子章节2标题"
                },
                ...
            ]
            
            确保JSON格式正确，可以直接解析。
            """
            
        return base_prompt
    
    def _extract_sections_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        从文本中提取章节信息
        
        Args:
            text: 文本内容
            
        Returns:
            章节列表
        """
        try:
            # 尝试直接解析JSON
            sections = json.loads(text)
            if isinstance(sections, list) and all(isinstance(s, dict) and "title" in s for s in sections):
                return sections
        except json.JSONDecodeError:
            pass
        
        # 如果直接解析失败，尝试从文本中提取JSON部分
        json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if json_match:
            try:
                sections = json.loads(json_match.group(0))
                if isinstance(sections, list) and all(isinstance(s, dict) and "title" in s for s in sections):
                    return sections
            except json.JSONDecodeError:
                pass
        
        # 如果仍然失败，尝试从文本中提取章节标题
        sections = []
        for line in text.split('\n'):
            # 查找类似 "1. 章节标题" 或 "第一章：章节标题" 的模式
            match = re.search(r'(?:\d+\.\s*|\w+章[：:]\s*)(.+)', line)
            if match:
                sections.append({"title": match.group(1).strip()})
        
        return sections if sections else self._get_mock_main_sections("未知主题", "word")
    
    def _extract_subsections_from_text(self, text: str, section_title: str) -> List[Dict[str, Any]]:
        """
        从文本中提取子章节信息
        
        Args:
            text: 文本内容
            section_title: 章节标题
            
        Returns:
            子章节列表
        """
        try:
            # 尝试直接解析JSON
            subsections = json.loads(text)
            if isinstance(subsections, list) and all(isinstance(s, dict) and "title" in s for s in subsections):
                return subsections
        except json.JSONDecodeError:
            pass
        
        # 如果直接解析失败，尝试从文本中提取JSON部分
        json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if json_match:
            try:
                subsections = json.loads(json_match.group(0))
                if isinstance(subsections, list) and all(isinstance(s, dict) and "title" in s for s in subsections):
                    return subsections
            except json.JSONDecodeError:
                pass
        
        # 如果仍然失败，尝试从文本中提取子章节标题
        subsections = []
        for line in text.split('\n'):
            # 查找类似 "1.1 子章节标题" 或 "- 子章节标题" 的模式
            match = re.search(r'(?:\d+\.\d+\s*|\-\s*)(.+)', line)
            if match:
                subsections.append({"title": match.group(1).strip()})
        
        return subsections if subsections else self._get_mock_subsections(section_title)
    
    def _extract_slides_from_text(self, text: str, section_title: str) -> List[Dict[str, Any]]:
        """
        从文本中提取幻灯片信息
        
        Args:
            text: 文本内容
            section_title: 章节标题
            
        Returns:
            幻灯片列表
        """
        try:
            # 尝试直接解析JSON
            slides = json.loads(text)
            if isinstance(slides, list) and all(isinstance(s, dict) and "title" in s for s in slides):
                return slides
        except json.JSONDecodeError:
            pass
        
        # 如果直接解析失败，尝试从文本中提取JSON部分
        json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if json_match:
            try:
                slides = json.loads(json_match.group(0))
                if isinstance(slides, list) and all(isinstance(s, dict) and "title" in s for s in slides):
                    return slides
            except json.JSONDecodeError:
                pass
        
        # 如果仍然失败，尝试从文本中提取幻灯片标题和类型
        slides = []
        current_title = None
        current_type = "content"  # 默认类型
        
        for line in text.split('\n'):
            # 查找幻灯片标题
            title_match = re.search(r'(?:幻灯片\s*\d+\s*[:：]\s*|标题\s*[:：]\s*)(.+)', line)
            if title_match:
                if current_title:  # 如果已经有标题，保存当前幻灯片
                    slides.append({"title": current_title, "type": current_type})
                current_title = title_match.group(1).strip()
                current_type = "content"  # 重置类型
                continue
            
            # 查找幻灯片类型
            type_match = re.search(r'(?:类型\s*[:：]\s*)(\w+)', line)
            if type_match and current_title:
                type_text = type_match.group(1).lower()
                if "两列" in type_text or "two" in type_text:
                    current_type = "two_column"
                elif "图片" in type_text or "image" in type_text:
                    current_type = "image_content"
                else:
                    current_type = "content"
        
        # 添加最后一个幻灯片
        if current_title:
            slides.append({"title": current_title, "type": current_type})
        
        return slides if slides else self._get_mock_slides(section_title)
    
    def _get_mock_main_sections(self, topic: str, doc_type: str) -> List[Dict[str, Any]]:
        """
        获取模拟的主要章节
        
        Args:
            topic: 文档主题
            doc_type: 文档类型
            
        Returns:
            模拟的章节列表
        """
        return [
            {"title": "引言"},
            {"title": f"{topic}的基本概念"},
            {"title": f"{topic}的主要特点"},
            {"title": f"{topic}的应用场景"},
            {"title": f"{topic}的发展趋势"},
            {"title": "总结与展望"}
        ]
    
    def _get_mock_section_detail(self, section: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
        """
        获取模拟的章节详情
        
        Args:
            section: 章节信息
            doc_type: 文档类型
            
        Returns:
            模拟的章节详情
        """
        section_title = section.get("title", "未知章节")
        
        if doc_type == "ppt":
            return {
                "title": section_title,
                "slides": self._get_mock_slides(section_title)
            }
        else:
            return {
                "title": section_title,
                "subsections": self._get_mock_subsections(section_title)
            }
    
    def _get_mock_slides(self, section_title: str) -> List[Dict[str, Any]]:
        """
        获取模拟的幻灯片
        
        Args:
            section_title: 章节标题
            
        Returns:
            模拟的幻灯片列表
        """
        return [
            {"title": f"{section_title}概述", "type": "content"},
            {"title": f"{section_title}的关键要素", "type": "two_column"},
            {"title": f"{section_title}的应用示例", "type": "image_content"},
            {"title": f"{section_title}的最佳实践", "type": "content"}
        ]
    
    def _get_mock_subsections(self, section_title: str) -> List[Dict[str, Any]]:
        """
        获取模拟的子章节
        
        Args:
            section_title: 章节标题
            
        Returns:
            模拟的子章节列表
        """
        return [
            {"title": f"{section_title}概述"},
            {"title": f"{section_title}的关键要素"},
            {"title": f"{section_title}的应用示例"},
            {"title": f"{section_title}的最佳实践"}
        ]