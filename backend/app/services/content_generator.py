import logging
from typing import Dict, Any, Optional, List
import re  # 将re模块导入移到文件顶部

from .ai_client import AIClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentGenerator:
    """
    文档内容生成器
    """
    
    def __init__(self, ai_client: AIClient):
        """
        初始化内容生成器
        
        Args:
            ai_client: AI客户端实例
        """
        self.ai_client = ai_client
        logger.info("内容生成器初始化完成")
    
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
        try:
            logger.info(f"开始为章节 '{section_title}' 生成内容 (主题: {topic}, 类型: {doc_type})")
            if additional_prompt:
                logger.info(f"附加提示词: {additional_prompt[:100]}...")
            
            # 构建提示
            prompt = self._build_section_prompt(topic, section_title, doc_type, additional_prompt)
            
            # 调用AI客户端
            messages = [
                {"role": "system", "content": "你是一个专业的文档内容生成助手，擅长创建高质量、信息丰富的文档内容。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.ai_client.call_api(messages)
            
            if not response:
                logger.warning(f"生成章节 '{section_title}' 内容失败，使用模拟内容")
                return self._get_mock_section_content(topic, section_title)
            
            # 提取内容
            content = self.ai_client.extract_response_content(response)
            
            if not content:
                logger.warning(f"从响应中提取章节 '{section_title}' 内容失败，使用模拟内容")
                return self._get_mock_section_content(topic, section_title)
            
            # 记录生成的内容摘要
            content_preview = content.replace('\n', ' ')[:100] + "..." if len(content) > 100 else content
            logger.info(f"成功生成章节 '{section_title}' 内容: {content_preview}")
            
            return content
            
        except Exception as e:
            logger.error(f"生成章节内容时出错: {str(e)}")
            return self._get_mock_section_content(topic, section_title)
    
    def generate_slide_content(self, topic: str, section_title: str, slide_title: str, slide_type: str, additional_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        生成幻灯片内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            slide_title: 幻灯片标题
            slide_type: 幻灯片类型 (content, two_column, image_content)
            additional_prompt: 附加提示词
            
        Returns:
            幻灯片内容
        """
        try:
            logger.info(f"开始为幻灯片 '{slide_title}' 生成内容 (章节: {section_title}, 类型: {slide_type})")
            if additional_prompt:
                logger.info(f"附加提示词: {additional_prompt[:100]}...")
            
            # 构建提示
            prompt = self._build_slide_prompt(topic, section_title, slide_title, slide_type, additional_prompt)
            
            # 调用AI客户端
            messages = [
                {"role": "system", "content": "你是一个专业的PPT内容生成助手，擅长创建简洁、有力的幻灯片内容。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.ai_client.call_api(messages)
            
            if not response:
                logger.warning(f"生成幻灯片 '{slide_title}' 内容失败，使用模拟内容")
                return self._get_mock_slide_content(slide_title, slide_type)
            
            # 提取内容
            content = self.ai_client.extract_response_content(response)
            
            if not content:
                logger.warning(f"从响应中提取幻灯片 '{slide_title}' 内容失败，使用模拟内容")
                return self._get_mock_slide_content(slide_title, slide_type)
            
            # 解析内容
            slide_content = self._parse_slide_content(content, slide_title, slide_type)
            
            # 记录生成的内容摘要
            if slide_type == "content":
                points = slide_content.get("points", [])
                logger.info(f"成功生成幻灯片 '{slide_title}' 内容: {len(points)} 个要点")
                for i, point in enumerate(points[:2]):  # 只记录前2个要点
                    logger.info(f"  要点 {i+1}: {point.get('main', '未知')}")
                if len(points) > 2:
                    logger.info(f"  ... 还有 {len(points) - 2} 个要点")
            elif slide_type == "two_column":
                left_points = slide_content.get("left_points", [])
                right_points = slide_content.get("right_points", [])
                logger.info(f"成功生成幻灯片 '{slide_title}' 内容: 左侧 {len(left_points)} 个要点, 右侧 {len(right_points)} 个要点")
            elif slide_type == "image_content":
                points = slide_content.get("points", [])
                image_desc = slide_content.get("image_description", "")
                logger.info(f"成功生成幻灯片 '{slide_title}' 内容: {len(points)} 个要点, 图片描述: {image_desc[:50]}...")
            
            return slide_content
            
        except Exception as e:
            logger.error(f"生成幻灯片内容时出错: {str(e)}")
            return self._get_mock_slide_content(slide_title, slide_type)
    
    def _build_section_prompt(self, topic: str, section_title: str, doc_type: str, additional_prompt: Optional[str] = None) -> str:
        """
        构建生成章节内容的提示
        
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
            请为主题"{topic}"中的章节"{section_title}"生成详细的内容。
            
            要求:
            1. 内容应该全面、准确、专业
            2. 包含该章节的关键概念、原理和应用
            3. 使用清晰的结构和逻辑
            4. 适合PPT演示的简洁表达
            5. 内容长度适中，约500-800字
            """
        else:
            base_prompt = f"""
            请为主题"{topic}"中的章节"{section_title}"生成详细的内容。
            
            要求:
            1. 内容应该全面、准确、专业
            2. 包含该章节的关键概念、原理和应用
            3. 使用清晰的结构和逻辑
            4. 适合学术或专业文档的正式表达
            5. 内容长度适中，约1000-1500字
            """
            
        # 添加附加提示词
        if additional_prompt:
            base_prompt += f"\n\n附加要求:\n{additional_prompt}\n"
            
        base_prompt += """
            请直接返回内容，不需要额外的格式或标记。
            """
            
        return base_prompt
    
    def _build_slide_prompt(self, topic: str, section_title: str, slide_title: str, slide_type: str, additional_prompt: Optional[str] = None) -> str:
        """
        构建生成幻灯片内容的提示
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            slide_title: 幻灯片标题
            slide_type: 幻灯片类型
            additional_prompt: 附加提示词
            
        Returns:
            提示文本
        """
        base_prompt = f"""
        请为主题"{topic}"中章节"{section_title}"的幻灯片"{slide_title}"生成内容。
        
        幻灯片类型: {slide_type}
        """
        
        type_specific_prompt = ""
        if slide_type == "content":
            type_specific_prompt = """
            要求:
            1. 创建3-5个简洁的要点
            2. 每个要点包含一个主要观点和1-2个支持细节
            3. 内容应该简洁明了，适合PPT展示
            """
        elif slide_type == "two_column":
            type_specific_prompt = """
            要求:
            1. 创建左右两列内容
            2. 每列包含2-3个要点
            3. 每个要点包含一个主要观点和1-2个支持细节
            """
        else:  # image_content
            type_specific_prompt = """
            要求:
            1. 创建3-4个要点，描述与图片相关的内容
            2. 每个要点包含一个主要观点和1-2个支持细节
            3. 添加一个图片描述，用于检索相关图片
            4. 图片描述应该具体、明确、视觉化，适合通过关键词搜索找到合适的图片
            5. 图片描述应该是5-15个单词，应专注于描述视觉元素而不是抽象概念
            6. 图片描述应该包含主题、动作、背景等关键元素
            7. 避免使用太过抽象或难以可视化的描述词
            
            图片描述示例:
            - "商务人士在会议室讨论图表"
            - "森林中的清澈小溪自然风景"
            - "科学家在实验室使用显微镜"
            - "城市摩天大楼鸟瞰图，日落时分"
            """
            
        # 添加附加提示词
        if additional_prompt:
            type_specific_prompt += f"\n附加要求:\n{additional_prompt}\n"
            
        # 添加JSON格式输出要求
        json_format = ""
        if slide_type == "content":
            json_format = """
            请以JSON格式返回，格式如下:
            {
                "points": [
                    {
                        "main": "主要要点1",
                        "details": ["细节1", "细节2"]
                    },
                    ...
                ]
            }
            """
        elif slide_type == "two_column":
            json_format = """
            请以JSON格式返回，格式如下:
            {
                "left_points": [
                    {
                        "main": "左侧要点1",
                        "details": ["细节1", "细节2"]
                    },
                    ...
                ],
                "right_points": [
                    {
                        "main": "右侧要点1",
                        "details": ["细节1", "细节2"]
                    },
                    ...
                ]
            }
            """
        else:  # image_content
            json_format = """
            请以JSON格式返回，格式如下:
            {
                "points": [
                    {
                        "main": "主要要点1",
                        "details": ["细节1", "细节2"]
                    },
                    ...
                ],
                "image_description": "具体、详细的图片描述，5-15个单词"
            }
            """
            
        # 组合提示
        full_prompt = f"{base_prompt}\n\n{type_specific_prompt}\n\n{json_format}"
        return full_prompt.strip()
    
    def _parse_slide_content(self, content: str, slide_title: str, slide_type: str) -> Dict[str, Any]:
        """
        解析从AI生成的幻灯片内容
        
        Args:
            content: 生成的内容
            slide_title: 幻灯片标题
            slide_type: 幻灯片类型
            
        Returns:
            解析后的内容
        """
        try:
            # 提取JSON部分
            import json
            
            # 先清理可能的注释
            content = re.sub(r'//.*?\n', '\n', content)
            
            # 1. 尝试提取带有三个反引号的Markdown代码块
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                logger.info(f"从Markdown代码块提取到内容: {json_str[:50]}...")
            else:
                # 2. 如果没有Markdown格式，直接尝试提取JSON对象
                object_match = re.search(r"(\{[\s\S]*\})", content, re.DOTALL)
                if object_match:
                    json_str = object_match.group(1)
                    logger.info(f"从文本中提取到JSON对象: {json_str[:50]}...")
                else:
                    # 如果仍然找不到，使用整个内容作为基础进行解析
                    json_str = content
                    logger.info("未找到JSON对象，将使用整个内容进行处理")
            
            # 尝试清理和解析JSON
            try:
                # 1. 确保json_str是一个完整的JSON对象
                if not (json_str.startswith('{') and json_str.endswith('}')):
                    # 如果不是完整JSON，尝试提取
                    object_match = re.search(r"(\{[\s\S]*\})", json_str, re.DOTALL)
                    if object_match:
                        json_str = object_match.group(1)
                
                # 2. 清理JSON字符串
                # 移除多余的逗号
                cleaned_json = re.sub(r',\s*}', '}', json_str)
                cleaned_json = re.sub(r',\s*]', ']', cleaned_json)
                
                # 修复可能的引号问题
                cleaned_json = cleaned_json.replace("'", '"')
                
                # 修复可能的尾部逗号问题 - 常见的JSON解析错误
                cleaned_json = re.sub(r',(\s*[\]}])', r'\1', cleaned_json)
                
                # 修复没有双引号的键
                cleaned_json = re.sub(r'(\{|\,)\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', cleaned_json)
                
                logger.info(f"尝试解析清理后的JSON: {cleaned_json[:50]}...")
                
                # 3. 解析JSON
                parsed = json.loads(cleaned_json)
                
                # 验证和处理JSON数据
                if slide_type == "image_content" and "image_description" in parsed:
                    # 优化图片描述用于搜索
                    image_desc = parsed["image_description"]
                    image_desc = re.sub(r'["\'\[\]\{\}]', '', image_desc)
                    if len(image_desc.split()) > 15:
                        image_desc = ' '.join(image_desc.split()[:15])
                    parsed["image_description"] = image_desc
                
                return parsed
            except json.JSONDecodeError as e:
                # JSON解析失败，记录错误详情，但继续使用结构化提取
                logger.warning(f"JSON解析失败 ({str(e)}): {cleaned_json[:100]}...，尝试结构化提取内容")
            
            # 如果JSON解析失败，使用结构化提取
            result = {}
            
            if slide_type == "content" or slide_type == "image_content":
                # 提取要点
                points = self._extract_points_from_text(content)
                result["points"] = points
                
                # 如果是图片内容类型，还需要提取图片描述
                if slide_type == "image_content":
                    # 提取图片描述
                    image_desc_match = re.search(r"(?:图片描述|image description)[：:]\s*(.*?)(?=\n|$)", content, re.IGNORECASE)
                    
                    if image_desc_match:
                        # 处理图片描述以优化搜索
                        image_desc = image_desc_match.group(1).strip()
                        # 去除多余标点和格式
                        image_desc = re.sub(r'["\'\[\]\{\}]', '', image_desc)
                        # 如果描述很长，取前15个单词
                        if len(image_desc.split()) > 15:
                            image_desc = ' '.join(image_desc.split()[:15])
                        result["image_description"] = image_desc
                    else:
                        # 如果没有找到图片描述，根据幻灯片标题和内容生成一个
                        result["image_description"] = f"{slide_title}, {' '.join([p.get('main', '').split()[:3] for p in points[:1]])}"
                
            elif slide_type == "two_column":
                # 提取左右两列内容
                left_points = []
                right_points = []
                
                # 检查是否有明确的左侧右侧标记
                left_section = re.search(r"左[侧栏].*?(?=右[侧栏]|$)", content, re.DOTALL)
                right_section = re.search(r"右[侧栏].*", content, re.DOTALL)
                
                if left_section and right_section:
                    left_points = self._extract_points_from_text(left_section.group(0))
                    right_points = self._extract_points_from_text(right_section.group(0))
                else:
                    # 如果没有明确标记，尝试将内容平均分配
                    all_points = self._extract_points_from_text(content)
                    mid_point = len(all_points) // 2
                    left_points = all_points[:mid_point + (1 if len(all_points) % 2 else 0)]
                    right_points = all_points[mid_point + (1 if len(all_points) % 2 else 0):]
                
                result["left_points"] = left_points
                result["right_points"] = right_points
            
            return result
            
        except Exception as e:
            logger.error(f"解析幻灯片内容时出错: {str(e)}")
            
            # 返回默认内容
            if slide_type == "content":
                return {"points": [{"main": "未能解析内容", "details": ["请参考其他资料"]}]}
            elif slide_type == "two_column":
                return {
                    "left_points": [{"main": "左侧要点", "details": ["请参考其他资料"]}],
                    "right_points": [{"main": "右侧要点", "details": ["请参考其他资料"]}]
                }
            else:  # image_content
                return {
                    "points": [{"main": "未能解析内容", "details": ["请参考其他资料"]}],
                    "image_description": slide_title  # 使用幻灯片标题作为图片描述
                }
    
    def _extract_points_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取要点和详情
        
        Args:
            text: 提取要点的文本
            
        Returns:
            要点列表，每个要点包含main和details字段
        """
        points = []
        current_point = None
        current_details = []
        
        # 确保是文本
        if not isinstance(text, str):
            logger.warning(f"无效的文本类型: {type(text)}")
            return [{"main": "无效内容", "details": ["请参考其他资料"]}]
        
        # 清理文本，去除可能的代码块标记
        clean_text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # 按行拆分
        lines = clean_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是主要要点（使用更强的匹配模式）
            main_point_match = re.search(r'^(?:\d+\.|\*|\-|\•|\○|\◆|\★|\◇|\→|\》|[A-Z]\.)\s*(.+)$', line)
            
            if main_point_match:
                # 如果已有要点，保存当前要点
                if current_point:
                    points.append({
                        "main": current_point,
                        "details": current_details
                    })
                    current_details = []
                
                # 设置新的要点
                current_point = main_point_match.group(1)
            elif current_point:
                # 子要点或详情
                detail_match = re.search(r'^(?:  |\t)(?:\d+\.|\*|\-|\•|\○|\◇|\→|\》|[a-z]\.)\s*(.+)$', line)
                if detail_match:
                    current_details.append(detail_match.group(1))
                else:
                    # 可能是要点的继续
                    # 检查是否是以某些特定词语开头，这通常表示这是一个新的要点
                    new_point_indicators = ['首先', '其次', '再次', '此外', '最后', '总之', '另外', '第一', '第二', '第三', '第四']
                    
                    is_new_point = False
                    for indicator in new_point_indicators:
                        if line.startswith(indicator):
                            is_new_point = True
                            break
                            
                    if is_new_point:
                        # 保存当前要点
                        if current_point:
                            points.append({
                                "main": current_point,
                                "details": current_details
                            })
                            current_details = []
                        
                        # 设置新的要点
                        current_point = line
                    elif line and len(line) > 5:  # 忽略太短的行
                        # 将这行作为详情添加
                        current_details.append(line)
        
        # 添加最后一个要点
        if current_point:
            points.append({
                "main": current_point,
                "details": current_details
            })
            
        # 如果没有提取到要点，尝试使用其他方法
        if not points:
            # 尝试直接按段落拆分
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', clean_text) if p.strip()]
            
            for para in paragraphs:
                if len(para) > 10:  # 忽略太短的段落
                    # 将段落的第一句作为主要内容
                    sentences = re.split(r'[.。!！?？]', para)
                    if sentences:
                        main = sentences[0].strip()
                        details = []
                        if len(sentences) > 1:
                            details = [s.strip() for s in sentences[1:] if s.strip()]
                        
                        points.append({
                            "main": main,
                            "details": details
                        })
        
        # 如果仍然没有内容，返回默认内容
        if not points:
            points = [{"main": "未能提取要点", "details": ["请参考其他资料"]}]
            
        return points
    
    def _get_mock_section_content(self, topic: str, section_title: str) -> str:
        """
        获取模拟的章节内容
        
        Args:
            topic: 文档主题
            section_title: 章节标题
            
        Returns:
            模拟的章节内容
        """
        return f"""
{section_title}是{topic}的重要组成部分。本章节将详细介绍其关键概念、应用场景和发展趋势。

首先，{section_title}的基本概念建立在多年的研究和实践基础上。它包含多个核心要素，这些要素相互关联，共同构成了完整的理论体系。理解这些基本概念对于掌握整个主题至关重要。

其次，{section_title}在多个领域有广泛的应用场景。无论是在教育、商业还是技术创新方面，都能找到其成功应用的案例。这些应用不仅验证了理论的有效性，也为未来的发展提供了宝贵的经验。

最后，随着新技术和新方法的出现，{section_title}正在不断发展。未来研究将进一步探索其潜力和应用前景，我们有理由相信，它将在{topic}的发展中发挥更加重要的作用。
        """
    
    def _get_mock_slide_content(self, slide_title: str, slide_type: str) -> Dict[str, Any]:
        """
        获取模拟的幻灯片内容
        
        Args:
            slide_title: 幻灯片标题
            slide_type: 幻灯片类型
            
        Returns:
            模拟的幻灯片内容
        """
        if slide_type == "content":
            return {
                "points": [
                    {
                        "main": f"{slide_title}的核心要素",
                        "details": ["包含多个关键组成部分", "这些组成部分相互关联"]
                    },
                    {
                        "main": "应用场景广泛",
                        "details": ["适用于多个领域", "有丰富的实践案例"]
                    },
                    {
                        "main": "未来发展趋势",
                        "details": ["将继续创新和完善", "有望解决更多实际问题"]
                    }
                ]
            }
        elif slide_type == "two_column":
            return {
                "left_points": [
                    {
                        "main": "理论基础",
                        "details": ["建立在坚实的研究基础上", "有完整的理论体系"]
                    },
                    {
                        "main": "核心优势",
                        "details": ["高效、可靠", "易于实施和推广"]
                    }
                ],
                "right_points": [
                    {
                        "main": "实际应用",
                        "details": ["已在多个领域成功应用", "取得了显著成效"]
                    },
                    {
                        "main": "未来展望",
                        "details": ["将继续发展和完善", "有更广阔的应用前景"]
                    }
                ]
            }
        else:  # image_content
            return {
                "points": [
                    {
                        "main": f"{slide_title}的图示说明",
                        "details": ["直观展示关键概念", "帮助理解复杂关系"]
                    },
                    {
                        "main": "实际案例",
                        "details": ["展示真实应用场景", "验证理论的有效性"]
                    },
                    {
                        "main": "对比分析",
                        "details": ["与其他方法的对比", "突出独特优势"]
                    }
                ],
                "image_description": f"关于{slide_title}的图示，展示其核心概念和关系"
            } 