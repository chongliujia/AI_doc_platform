import logging
import os
import sys
from pathlib import Path

# 添加父目录到路径以便导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ppt_generator import PPTGenerator
from app.services.ai_service_factory import AIServiceFactory

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ppt_generation():
    """
    测试PPT生成功能，包括图片处理
    """
    try:
        # 使用示例主题和大纲
        topic = "人工智能在医疗领域的应用"
        
        # 创建简化的大纲，包含带图片的幻灯片
        outline = [
            {
                "title": "人工智能在医疗领域的概述",
                "slides": [
                    {
                        "title": "医疗AI的发展历程",
                        "type": "content"
                    },
                    {
                        "title": "医疗AI的关键技术",
                        "type": "two_column"
                    }
                ]
            },
            {
                "title": "医疗影像诊断中的AI应用",
                "slides": [
                    {
                        "title": "AI辅助放射诊断",
                        "type": "image_content"
                    },
                    {
                        "title": "案例研究：肺部CT扫描分析",
                        "type": "image_content"
                    }
                ]
            },
            {
                "title": "医疗AI的挑战与展望",
                "slides": [
                    {
                        "title": "当前面临的技术挑战",
                        "type": "content"
                    },
                    {
                        "title": "未来发展趋势",
                        "type": "image_content"
                    }
                ]
            }
        ]
        
        # 创建PPT生成器
        ppt_generator = PPTGenerator()
        
        # 生成PPT文档
        output_path = ppt_generator.generate(topic, outline)
        
        if output_path and os.path.exists(output_path):
            logger.info(f"PPT生成成功，文件路径: {output_path}")
            logger.info(f"文件大小: {os.path.getsize(output_path) / 1024:.2f} KB")
            
            # 尝试打开文件（仅在桌面环境中有效）
            try:
                import platform
                system = platform.system()
                
                if system == "Darwin":  # macOS
                    os.system(f"open '{output_path}'")
                elif system == "Windows":
                    os.system(f'start "" "{output_path}"')
                elif system == "Linux":
                    os.system(f"xdg-open '{output_path}'")
                    
                logger.info("已尝试打开生成的PPT文件")
            except Exception as e:
                logger.warning(f"尝试打开文件时出错: {str(e)}")
        else:
            logger.error("PPT生成失败")
    
    except Exception as e:
        logger.error(f"测试PPT生成时出错: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_ppt_generation() 