import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径，以便能够导入应用模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.ppt_generator import PPTGenerator
from app.controllers.document_controller import DocumentController


class TestFilenameSanitization(unittest.TestCase):
    """测试文件名清理功能"""

    def setUp(self):
        """设置测试环境"""
        self.ppt_generator = PPTGenerator()
        
        # 创建一个DocumentController实例，mock所需的依赖
        class MockAIProvider:
            async def generate_completion(self, *args, **kwargs):
                return "Mock response"
                
            async def generate_optimized_title(self, *args, **kwargs):
                return "Mock title"
                
            def generate_document_outline(self, *args, **kwargs):
                return []
                
        class MockStorageProvider:
            async def save_file(self, *args, **kwargs):
                return "mock_path"
                
            async def get_file_url(self, *args, **kwargs):
                return "mock_url"
                
        self.doc_controller = DocumentController(
            ai_provider=MockAIProvider(),
            storage_provider=MockStorageProvider()
        )

    def test_ppt_generator_sanitize_filename(self):
        """测试PPTGenerator中的文件名清理功能"""
        test_cases = [
            # 输入, 预期输出
            ("正常标题", "正常标题"),
            ("标题 with spaces", "标题 with spaces"),
            ("标题/with/slashes", "标题withslashes"),
            ("标题*with*stars", "标题withstars"),
            ("标题?with?questions", "标题withquestions"),
            ("标题\"with\"quotes", "标题withquotes"),
            ("标题<with>brackets", "标题withbrackets"),
            ("标题|with|pipes", "标题withpipes"),
            ("带有\n换行符的标题", "带有 换行符的标题"),
            ("带有    多个空格    的标题", "带有 多个空格 的标题"),
            ("", "AI_presentation"),  # 空标题
            ("x" * 200, "x" * 100 + "..."),  # 超长标题
        ]
        
        for input_title, expected_output in test_cases:
            sanitized = self.ppt_generator._sanitize_filename(input_title)
            self.assertEqual(sanitized, expected_output, f"Failed for input: '{input_title}'")
            
    def test_doc_controller_sanitize_filename(self):
        """测试DocumentController中的文件名清理功能"""
        test_cases = [
            # 输入, 预期输出
            ("正常标题", "正常标题"),
            ("标题 with spaces", "标题 with spaces"),
            ("标题/with/slashes", "标题withslashes"),
            ("标题*with*stars", "标题withstars"),
            ("标题?with?questions", "标题withquestions"),
            ("标题\"with\"quotes", "标题withquotes"),
            ("标题<with>brackets", "标题withbrackets"),
            ("标题|with|pipes", "标题withpipes"),
            ("带有\n换行符的标题", "带有 换行符的标题"),
            ("带有    多个空格    的标题", "带有 多个空格 的标题"),
            ("", "AI_document"),  # 空标题
            ("x" * 200, "x" * 100 + "..."),  # 超长标题
            # 测试AI生成的长标题
            ("以下是为您的PPT文档设计的几个标题选项，兼顾专业性、简洁性和视觉吸引力：\n\n1. **《人工智能：定义、原理与未来展望》**  \n   （经典三段式结构，适合学术/商业场景）", 
             "以下是为您的PPT文档设计的几个标题选项，兼顾专业性、简洁性和视觉吸引力： 1. 《人工智能：定义、原理与未来展...")
        ]
        
        for input_title, expected_output in test_cases:
            sanitized = self.doc_controller._sanitize_filename(input_title)
            self.assertEqual(sanitized, expected_output, f"Failed for input: '{input_title}'")


if __name__ == "__main__":
    unittest.main() 