<template>
  <div class="post" v-if="article">
    <!-- 操作按钮栏 -->
    <div class="post-actions">
      <button @click="toggleEditMode" class="edit-btn">编辑</button>
      <button @click="confirmDelete" class="delete-btn">删除</button>
    </div>

    <!-- 编辑模式 -->
    <div v-if="isEditing" class="edit-form">
      <input v-model="editForm.title" placeholder="标题" class="form-input" />
      <input v-model="editForm.tags" placeholder="标签（逗号分隔）" class="form-input" />
      <textarea v-model="editForm.content" placeholder="内容（Markdown）" rows="12" class="form-textarea"></textarea>
      <div class="form-buttons">
        <button @click="submitEdit" class="save-btn">保存修改</button>
        <button @click="cancelEdit" class="cancel-btn">取消</button>
      </div>
    </div>

    <!-- 正常显示模式 -->
    <div v-else>
      <h1>{{ article.title }}</h1>
      <div class="post-meta">
        <span>{{ article.date }}</span>
        <div class="tags">
          <span v-for="tag in article.tags" :key="tag" class="tag">
            {{ tag }}
          </span>
        </div>
      </div>
      <div class="post-content" v-html="article.content"></div>
    </div>
  </div>
  <div v-else-if="loading" class="loading">
    <p>加载中...</p>
  </div>
  <div v-else class="error">
    <p>加载失败，请检查文章是否存在</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import { parseFrontmatter } from '@/utils/markdown'

const API_BASE_URL = 'https://你的后端域名.up.railway.app'
const route = useRoute()
const router = useRouter()
const article = ref(null)
const loading = ref(true)

// 编辑相关
const isEditing = ref(false)
const editForm = ref({
  title: '',
  tags: '',
  content: ''
})

// 填充编辑表单
const fillEditForm = () => {
  editForm.value = {
    title: article.value.title,
    tags: article.value.tags.join(', '),
    content: article.value.rawContent
  }
}

// 切换编辑模式
const toggleEditMode = () => {
  if (!isEditing.value) {
    fillEditForm()
  }
  isEditing.value = !isEditing.value
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
}

// 提交编辑
const submitEdit = async () => {
  if (!editForm.value.title.trim() || !editForm.value.content.trim()) {
    alert('标题和内容不能为空')
    return
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/update-post/${route.params.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: editForm.value.title,
        tags: editForm.value.tags,
        content: editForm.value.content
      })
    })
    const data = await response.json()
    if (data.success) {
      alert('文章已更新')
      // 如果文件名变了，跳转到新 URL
      if (data.new_filename && data.new_filename !== route.params.id) {
        router.push(`/post/${data.new_filename}`)
      } else {
        // 重新加载当前文章
        await loadArticle()
      }
      isEditing.value = false
    } else {
      alert('更新失败：' + data.error)
    }
  } catch (err) {
    console.error(err)
    alert('请求后端失败')
  }
}

// 确认删除
const confirmDelete = () => {
  if (confirm('确定要删除这篇文章吗？此操作不可恢复。')) {
    deleteArticle()
  }
}

const deleteArticle = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/delete-post/${route.params.id}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    if (data.success) {
      alert('文章已删除')
      router.push('/')  // 跳转回首页
    } else {
      alert('删除失败：' + data.error)
    }
  } catch (err) {
    console.error(err)
    alert('请求后端失败')
  }
}

// 配置 markdown-it
const md = new MarkdownIt({
  html: true,
  breaks: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (err) {
        console.error(err)
      }
    }
    return ''
  }
})

// 加载文章内容
const loadArticle = async () => {
  loading.value = true
  try {
    const id = route.params.id
    console.log('加载文章:', id)
    
    // 获取 markdown 文件
    const response = await fetch(`/posts/${id}.md`)
    if (!response.ok) {
      throw new Error(`文章不存在: ${id}`)
    }
    const text = await response.text()
    
    // 解析 frontmatter
    const { data, content } = parseFrontmatter(text)
    
    // 渲染 markdown 为 HTML
    const htmlContent = md.render(content)
    
    article.value = {
      id,
      title: data.title || '无标题',
      date: data.date || '',
      tags: data.tags || [],
      content: htmlContent,
      rawContent: content  // 保存原始 Markdown
    }
    
    console.log('文章加载成功:', article.value.title)
  } catch (error) {
    console.error('加载文章失败:', error)
    article.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadArticle()
})
</script>

<style scoped>
.post {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.post h1 {
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.post-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
  color: #666;
  font-size: 0.875rem;
  flex-wrap: wrap;
}

.tags {
  display: flex;
  gap: 0.5rem;
}

.tag {
  background: #f0f0f0;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.post-content {
  line-height: 1.8;
  color: #333;
}

.post-content h2 {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #2c3e50;
}

.post-content p {
  margin-bottom: 1rem;
}

.post-content pre {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  margin: 1rem 0;
}

.post-content code {
  background: #f5f5f5;
  padding: 0.125rem 0.25rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.875em;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.loading, .error {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.error {
  color: #e74c3c;
}

.post-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-bottom: 1rem;
}
.edit-btn, .delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.3rem 0.8rem;
  border-radius: 4px;
}
.edit-btn {
  background: #42b983;
  color: white;
}
.delete-btn {
  background: #e74c3c;
  color: white;
}

/* 编辑表单样式 */
.edit-form {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #eaeef5;
}

.edit-form .form-input,
.edit-form .form-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  border: 1px solid #dce4ec;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  transition: all 0.2s ease;
  background-color: #fafbfc;
}

.edit-form .form-input:focus,
.edit-form .form-textarea:focus {
  outline: none;
  border-color: #42b983;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.1);
}

.edit-form .form-textarea {
  resize: vertical;
  min-height: 300px;
  line-height: 1.5;
}

.form-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.save-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 0.6rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover {
  background: #359268;
}

.cancel-btn {
  background: #e2e6ea;
  color: #4a5568;
  border: none;
  padding: 0.6rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.cancel-btn:hover {
  background: #cbd5e0;
}
</style>