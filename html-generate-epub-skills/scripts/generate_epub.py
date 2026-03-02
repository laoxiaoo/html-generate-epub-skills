# -*- coding: utf-8 -*-
import os
import sys
import re
import urllib.request
import base64
from ebooklib import epub
from bs4 import BeautifulSoup

HLJS_COLORS = {
    'hljs-keyword': '#a71d5d',
    'hljs-string': '#df5000',
    'hljs-number': '#005cc5',
    'hljs-comment': '#969896',
    'hljs-function': '#6f42c1',
    'hljs-title': '#6f42c1',
    'hljs-class': '#6f42c1',
    'hljs-params': '#24292e',
    'hljs-built_in': '#005cc5',
    'hljs-literal': '#0086b3',
    'hljs-attr': '#6f42c1',
}

CODE_STYLE = """
.common-content pre {
  background-color: #f6f8fa;
  border-radius: 4px;
  padding: 16px;
  margin: 16px 0;
  overflow-x: auto;
  font-family: Consolas, "Liberation Mono", Menlo, Monaco, Courier, monospace;
  font-size: 13px;
  line-height: 1.5;
  border: 1px solid #e1e4e8;
}
.common-content pre code {
  background-color: transparent;
  padding: 0;
  font-size: inherit;
  color: #24292e;
}
.hljs-keyword { color: #a71d5d; }
.hljs-string { color: #df5000; }
.hljs-number { color: #005cc5; }
.hljs-comment { color: #969896; }
.hljs-function { color: #6f42c1; }
.hljs-title { color: #6f42c1; }
.hljs-class { color: #6f42c1; }
.hljs-params { color: #24292e; }
.hljs-built_in { color: #005cc5; }
.hljs-literal { color: #0086b3; }
.hljs-attr { color: #6f42c1; }
"""

def get_all_html_files(base_dir):
    """获取所有HTML文件"""
    html_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    return html_files

def extract_code_as_html(container):
    """从代码容器中提取代码为HTML格式"""
    code_lines = container.find_all(attrs={'data-slate-type': 'code-line'})
    if not code_lines:
        return None
    
    html_lines = []
    
    for line in code_lines:
        # 找到所有包含data-slate-string的span
        text_spans = line.find_all(attrs={'data-slate-string': True})
        if not text_spans:
            html_lines.append('')
            continue
        
        line_html = ''
        for span in text_spans:
            text = span.get_text(strip=False)
            # 替换普通空格为不间断空格，保留缩进
            text = text.replace(' ', '\u00A0')
            
            color = '#24292e'
            # 查找当前span的class
            classes = span.get('class', [])
            for cls in classes:
                if cls in HLJS_COLORS:
                    color = HLJS_COLORS[cls]
                    break
            
            # 如果没找到，查找父span的class
            if color == '#24292e':
                parent = span.parent
                if parent:
                    classes = parent.get('class', [])
                    for cls in classes:
                        if cls in HLJS_COLORS:
                            color = HLJS_COLORS[cls]
                            break
            
            # 直接使用原始文本（包含空格）
            line_html += f'<span style="color: {color};">{text}</span>'
        
        html_lines.append(line_html)
    
    if not html_lines:
        return None
    
    # 格式化每行，保留缩进空格
    formatted_lines = []
    for line in html_lines:
        # 保持原有格式
        formatted_lines.append(line)
    
    pre_style = 'style="background-color: #f6f8fa; border-radius: 4px; padding: 16px; margin: 16px 0; overflow-x: auto; font-family: Consolas, monospace; font-size: 13px; line-height: 1.5; border: 1px solid #e1e4e8; white-space: pre-wrap;"'
    code_html = f'<pre class="code-block" {pre_style}><code>\n' + '\n'.join(formatted_lines) + '\n</code></pre>'
    return code_html

def extract_main_content(html_file, book, file_idx):
    """提取HTML主体内容，去除评论部分"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    main_content = {}
    
    h1 = soup.find('h1')
    if h1:
        main_content['title'] = h1.get_text(strip=True)
    else:
        main_content['title'] = os.path.basename(html_file).replace('.html', '')
    
    body = soup.find('body')
    if not body:
        return None
    
    body_html = str(body)
    
    h1_tag = soup.find('h1')
    if not h1_tag:
        return None
    
    start_idx = body_html.find('<h1')
    if start_idx == -1:
        return None
    
    if '写留言' in body_html:
        end_idx = body_html.find('写留言')
        body_html = body_html[start_idx:end_idx]
    else:
        body_html = body_html[start_idx:]
    
    body_html = body_html + '</body></html>'
    
    content_soup = BeautifulSoup(body_html, 'html.parser')
    
    code_containers = content_soup.find_all(attrs={"data-slate-type": "pre"})
    for container in code_containers:
        code_html = extract_code_as_html(container)
        if code_html:
            code_tag = BeautifulSoup(code_html, 'html.parser')
            container.insert_before(code_tag)
            container.decompose()
    
    img_count = 0
    processed_images = {}
    
    for img in content_soup.find_all('img'):
        if img.get('src', '').startswith('code_'):
            continue
        
        img_url = img.get('data-savepage-src') or img.get('src')
        
        if not img_url or img_url == 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==':
            img.decompose()
            continue
        
        if img_url in processed_images:
            img['src'] = processed_images[img_url]
            continue
        
        try:
            if img_url.startswith('data:image'):
                base64_data = img_url.split(',')[1]
                img_data = base64.b64decode(base64_data)
                ext = img_url.split(';')[0].split('/')[1]
                if ext == 'jpeg':
                    ext = 'jpg'
            else:
                req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    img_data = response.read()
                    ext = img_url.split('.')[-1].split('?')[0]
                    if not ext or len(ext) > 5:
                        ext = 'jpg'
            
            img_name = f'image_{file_idx}_{img_count}.{ext}'
            
            epub_img = epub.EpubItem(
                file_name=img_name,
                media_type=f'image/{ext}',
                content=img_data
            )
            book.add_item(epub_img)
            
            img['src'] = img_name
            
            if ext == 'png':
                img['style'] = 'max-width: 100%; height: auto;'
            
            processed_images[img_url] = img_name
            img_count += 1
        except Exception as e:
            print(f"处理图片失败: {img_url}, 错误: {e}")
            img.decompose()
    
    html_with_style = '<html><head><style>' + CODE_STYLE + '</style></head>' + str(content_soup) + '</html>'
    main_content['html'] = html_with_style
    
    return main_content

def create_epub(base_dir, output_dir, output_filename):
    """创建EPUB文件"""
    book = epub.EpubBook()
    
    book.set_identifier('id123456')
    book.set_language('zh-CN')
    
    html_files = get_all_html_files(base_dir)
    html_files.sort()
    
    base_dir_name = os.path.basename(base_dir)
    book.set_title(base_dir_name)
    
    chapters = []
    spine = ['nav']
    
    for idx, html_file in enumerate(html_files):
        print(f"处理文件: {html_file}")
        
        main_content = extract_main_content(html_file, book, idx)
        if not main_content:
            print(f"无法提取内容: {html_file}")
            continue
        
        chapter_title = main_content['title']
        html_content = main_content['html']
        
        styled_html = html_content.replace('<body>', '<body><style>' + CODE_STYLE + '</style>')
        
        chapter = epub.EpubHtml(title=chapter_title, file_name=f'chapter_{idx}.xhtml', lang='zh-CN')
        chapter.content = styled_html
        
        book.add_item(chapter)
        chapters.append(chapter)
        spine.append(chapter)
    
    book.toc = chapters
    book.spine = spine
    
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, output_filename)
    epub.write_epub(output_path, book, {})
    
    print(f"EPUB文件已生成: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("用法: python generate_epub.py <基础目录> <输出目录> <输出文件名>")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    output_dir = sys.argv[2]
    output_filename = sys.argv[3]
    
    create_epub(base_dir, output_dir, output_filename)
