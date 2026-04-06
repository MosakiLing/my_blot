from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import re
from urllib.parse import unquote

app = Flask(__name__)
CORS(app, origins='*')

#限制请求体大小（防止过大）
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# 配置文件夹路径
POSTS_DIR = os.path.join('public', 'posts')
JSON_PATH = os.path.join('public', 'posts.json')

# 确保 posts 文件夹存在
os.makedirs(POSTS_DIR, exist_ok=True)

@app.route('/posts.json')
def get_posts_json():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    else:
        return jsonify([])

@app.route('/posts/<filename>.md')
def get_md_file(filename):
    file_path = os.path.join(POSTS_DIR, f'{filename}.md')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/markdown'}
    else:
        return jsonify({'error': 'Not found'}), 404

def generate_filename(title):
    """将标题转换为合法的文件名（英文+数字+中文）"""
    # 保留中文、字母、数字，其他符号变成横线
    base = re.sub(r'[^\w\u4e00-\u9fa5]', '-', title)
    base = re.sub(r'-+', '-', base).strip('-')
    if not base:
        base = str(int(datetime.now().timestamp()))
    filename = base
    counter = 1
    while os.path.exists(os.path.join(POSTS_DIR, f'{filename}.md')):
        filename = f"{base}-{counter}"
        counter += 1
    return filename

@app.route('/api/save-post', methods=['POST', 'OPTIONS'])
def save_post():
    if request.method == 'OPTIONS':
        return '', 200
    
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

#更新文章
@app.route('/api/update-post/<path:filename>', methods=['PUT', 'OPTIONS'])
def update_post(filename):
    if request.method == 'OPTIONS':
        return '', 200
    
    filename = unquote(filename)

    data = request.get_json()
    new_title = data.get('title', '').strip()
    new_tags = data.get('tags', '').strip()
    new_content = data.get('content', '').strip()

    if not new_title or not new_content:
        return jsonify({'error': '标题和内容不能为空'}), 400

    old_file_path = os.path.join(POSTS_DIR, f'{filename}.md')
    if not os.path.exists(old_file_path):
        return jsonify({'error': '文章不存在'}), 404

    # 读取旧文件，提取原标题
    with open(old_file_path, 'r', encoding='utf-8') as f:
        old_content = f.read()
    old_title_match = re.search(r'^---\n(.*?)\n---', old_content, re.DOTALL)
    old_title = None
    if old_title_match:
        for line in old_title_match.group(1).split('\n'):
            if line.startswith('title:'):
                old_title = line.split(':', 1)[1].strip()
                break

    # 如果标题未变，则沿用原文件名，否则生成新文件名
    if old_title == new_title:
        new_filename = filename
    else:
        new_filename = generate_filename(new_title)
    
    new_file_path = os.path.join(POSTS_DIR, f'{new_filename}.md')
    tag_list = [t.strip() for t in new_tags.split(',') if t.strip()]
    today = datetime.now().strftime('%Y-%m-%d')
    md_content = f"""---
title: {new_title}
date: {today}
tags: {', '.join(tag_list)}
---

{new_content}
"""

    if new_filename != filename:
        # 保存新文件
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        # 删除旧文件
        os.remove(old_file_path)
        # 更新 posts.json
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        if filename in posts:
            posts.remove(filename)
        if new_filename not in posts:
            posts.append(new_filename)
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
    else:
        # 文件名不变，直接覆盖
        with open(old_file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

    return jsonify({'success': True, 'new_filename': new_filename})

#删除文章
@app.route('/api/delete-post/<path:filename>', methods=['DELETE', 'OPTIONS'])
def delete_post(filename):
    if request.method == 'OPTIONS':
        return '', 200
    
    filename = unquote(filename)  # 解码中文

    file_path = os.path.join(POSTS_DIR, f'{filename}.md')
    if not os.path.exists(file_path):
        return jsonify({'error': '文章不存在'}), 404

    # 删除 .md 文件
    os.remove(file_path)

    # 更新 posts.json
    json_path = os.path.join(POSTS_DIR, '..', 'posts.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        if filename in posts:
            posts.remove(filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)

    return jsonify({'success': True})

if __name__ == '__main__':
    # 监听 3000 端口（与 Node 版保持一致，前端不用改）
    app.run(host='0.0.0.0', port=3000, debug=True)