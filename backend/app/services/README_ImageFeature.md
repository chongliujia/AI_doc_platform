# PPT 生成器图片增强功能

## 功能概述

PPT生成器现在支持自动为幻灯片添加相关图片，使演示文稿更加生动和专业。该功能主要通过以下几个方面实现：

1. **智能图片描述生成**：AI服务会根据幻灯片内容生成具体的图片描述
2. **图片搜索和获取**：使用Unsplash API根据图片描述搜索并获取高质量图片
3. **无缝集成到PPT**：将获取的图片自动添加到相应的幻灯片中

## 技术实现

### 核心组件

- **ImageService**: 负责图片搜索、下载和管理
- **增强的ContentGenerator**: 生成更适合图片搜索的图片描述
- **修改的PPTGenerator**: 整合图片功能到幻灯片生成过程

### 工作流程

1. AI生成幻灯片内容时，为"image_content"类型的幻灯片生成具体的图片描述
2. ImageService使用图片描述通过Unsplash API搜索相关图片
3. 下载图片并保存到临时目录
4. PPT生成器将图片添加到幻灯片中
5. 文档生成完成后，自动清理临时图片文件

## 配置和使用

### 环境变量

设置以下环境变量以启用图片搜索功能：

```
UNSPLASH_API_KEY=your_unsplash_api_key
```

如果未设置API密钥，系统将使用本地生成的占位图片。

### 示例代码

```python
from app.services.ppt_generator import PPTGenerator

# 创建PPT生成器实例
ppt_generator = PPTGenerator()

# 定义带有图片幻灯片的大纲
outline = [
    {
        "title": "章节标题",
        "slides": [
            {
                "title": "普通内容幻灯片",
                "type": "content"
            },
            {
                "title": "带图片的内容幻灯片",
                "type": "image_content"  # 指定为带图片的幻灯片类型
            }
        ]
    }
]

# 生成PPT
output_path = ppt_generator.generate("演示文稿主题", outline)
```

### 测试脚本

使用提供的测试脚本来验证图片功能：

```bash
cd backend
python -m app.test_ppt_generator
```

## 图片类型和描述

为获得最佳图片搜索结果，图片描述应该：

1. **具体明确**：清晰描述所需图片的主题和内容
2. **注重视觉元素**：描述可见的对象、场景或动作
3. **简洁有力**：通常5-15个单词最为有效
4. **避免抽象概念**：优先使用具体、可视化的描述

示例：
- ✅ "医生使用显微镜分析样本"
- ✅ "人工智能在医院辅助诊断"
- ❌ "医疗技术的未来发展"（过于抽象）

## 故障排除

如果图片功能不正常：

1. 检查Unsplash API密钥是否正确设置
2. 确认网络连接正常
3. 查看日志中的错误信息
4. 确保安装了Pillow库（`pip install pillow`）

## 注意事项

- 每个Unsplash API密钥有请求限制，请合理使用
- 遵守Unsplash的使用条款和版权规定
- 生成的图片仅用于演示目的，生产环境使用请替换为适当的图片资源 