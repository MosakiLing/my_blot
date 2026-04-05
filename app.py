from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)  # 允许所有跨域请求

# 配置文件夹路径
POSTS_DIR = os.path.join('public', 'posts')
JSON_PATH = os.path.join('public', 'posts.json')

# 确保 posts 文件夹存在
os.makedirs(POSTS_DIR, exist_ok=True)

def generate_filename(title):
    """将标题转换为合法的文件名（英文+数字+中文）"""
    # 保留中文、字母、数字，其他符号变成横线
    filename = re.sub(r'[^\w\u4e00-\u9fa5]', '-', title)
    filename = re.sub(r'-+', '-', filename)  # 多个横线合并为一个
    filename = filename.strip('-')
    if not filename:
        filename = str(int(datetime.now().timestamp()))
    return filename

@app.route('/api/save-post', methods=['POST'])
def save_post():
    data = request.get_json()
    title = data.get('title', '').strip()
    tags = data.get('tags', '').strip()
    content = data.get('content', '').strip()

    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400

    # 生成文件名
    filename = generate_filename(title)

    # 处理标签
    tag_list = [t.strip() for t in tags.split(',') if t.strip()]

    # 生成 Markdown 文件内容（包含 frontmatter）
    today = datetime.now().strftime('%Y-%m-%d')
    md_content = f"""---
title: {title}
date: {today}
tags: {', '.join(tag_list)}
---

{content}
"""

    # 保存 .md 文件
    file_path = os.path.join(POSTS_DIR, f'{filename}.md')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 更新 posts.json
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    else:
        posts = []

    if filename not in posts:
        posts.append(filename)
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

    return jsonify({'success': True, 'filename': filename})

if __name__ == '__main__':
    # 监听 3000 端口（与 Node 版保持一致，前端不用改）
    app.run(host='0.0.0.0', port=3000, debug=True)