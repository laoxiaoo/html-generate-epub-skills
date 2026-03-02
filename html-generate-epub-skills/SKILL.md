---
name: html-generate-epub-skills
description: 将HTML文件转换为EPUB电子书
---

# Skill: HTML转EPUB生成器

## 描述
将HTML文件集合转换为EPUB电子书，支持指定目录结构。一级目录作为顶级标题，二级目录作为子标题。

## 功能特性
1. **去除无用内容**: 自动去除"写留言"、评论、上下篇导航等内容
2. **代码块处理**: 
   - 提取HTML中的代码块
   - 保留代码关键字颜色高亮
   - 保留代码缩进格式
   - 添加灰色背景和边框样式
3. **图片处理**: 自动下载并嵌入HTML中的图片到EPUB
4. **目录结构**: 根据HTML文件的目录结构生成EPUB章节

## 使用方法
1. 指定包含HTML文件的**基础目录**
2. 指定生成的EPUB文件的**输出目录**和**文件名**
3. 运行skill生成EPUB文件

## 命令格式
```
generate-epub <基础目录> <输出目录> <输出文件名>
```

## 示例
```bash
html-generate-epub-skills D:/AI/htmltoepub/测试 D:/AI/htmltoepub c.epub
```

## 依赖
- Python 3.x
- ebooklib: `pip install ebooklib`
- beautifulsoup4: `pip install beautifulsoup4`

## 文件结构
```
generate-epub/
├── SKILL.md
└── scripts/
    └── generate_epub.py
```

## 示例目录结构
```
基础目录/
├── 目录1/
│   ├── 子目录1-1/
│   │   └── 文件1-1-1.html
│   └── 子目录1-2/
│       └── 文件1-2-1.html
└── 目录2/
    └── 子目录2-1/
        └── 文件2-1-1.html
```

生成的EPUB将包含:
- 目录1 (一级标题)
  - 子目录1-1 (二级标题)
    - 文件1-1-1.html内容
  - 子目录1-2 (二级标题)
    - 文件1-2-1.html内容
- 目录2 (一级标题)
  - 子目录2-1 (二级标题)
    - 文件2-1-1.html内容
