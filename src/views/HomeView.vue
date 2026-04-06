<template>
  <div class="home">
    <h2>最新魔法研究与旅行见闻：</h2>
    
    <!-- 按钮栏：切换撰写表单 -->
    <div class="action-bar">
      <button @click="showWriteForm = !showWriteForm" class="write-btn">
        {{ showWriteForm ? '← 返回首页' : '撰写文章' }}
      </button>
    </div>

    <!-- 撰写文章表单 -->
    <div v-if="showWriteForm" class="write-form">
      <h3>撰写新文章</h3>
      <input v-model="newPost.title" placeholder="文章标题" class="form-input" />
      <input v-model="newPost.tags" placeholder="标签（用逗号分隔，如：Vue,前端）" class="form-input" />
      <textarea v-model="newPost.content" placeholder="文章内容（支持 Markdown 语法）" class="form-textarea" rows="12"></textarea>
      <div class="form-buttons">
        <button @click="submitPost" class="submit-btn">提交文章</button>
        <button @click="showWriteForm = false" class="cancel-btn">取消</button>
      </div>
      <p class="hint">提示：提交后会自动保存到服务器，刷新首页即可看到新文章。</p>
    </div>

    <!-- 搜索框 -->
    <div class="search-bar">
      <input 
        type="text" 
        v-model="searchKeyword" 
        placeholder="搜索文章标题或内容..."
        class="search-input"
      />
      <button v-if="searchKeyword" @click="searchKeyword = ''" class="clear-btn">✕</button>
    </div>

    <!-- 标签栏 -->
    <div class="tags-bar">
      <button 
        :class="['tag-btn', { active: currentTag === 'all' }]"
        @click="currentTag = 'all'"
      >
        全部
      </button>
      <button 
        v-for="tag in allTags" 
        :key="tag"
        :class="['tag-btn', { active: currentTag === tag }]"
        @click="currentTag = tag"
      >
        {{ tag }}
      </button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 文章列表 -->
    <div v-else class="article-list">
      <router-link 
        v-for="article in filteredArticles" 
        :key="article.id" 
        class="article-item" 
        :to="`/post/${article.id}`"
      >
        <div class="article-title" v-html="highlightText(article.title, searchKeyword)"></div>
        <div class="article-meta">
          <span>{{ article.date }}</span>
          <span class="tags">
            <span v-for="tag in article.tags" :key="tag" class="tag">
              {{ tag }}
            </span>
          </span>
        </div>
        <div class="article-excerpt" v-html="highlightText(article.excerpt, searchKeyword)"></div>
      </router-link>

      <div v-if="filteredArticles.length === 0" class="no-articles">
        <span v-if="searchKeyword">没有找到"{{ searchKeyword }}"</span>
        <span v-else-if="currentTag !== 'all'">没有"{{ currentTag }}"标签的文章</span>
        <span v-else>暂无文章</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { parseFrontmatter, getPlainText } from '@/utils/markdown'

const API_BASE_URL = 'https://web-production-b655b.up.railway.app'
// ===== 数据 =====
const articles = ref([])
const loading = ref(true)
const currentTag = ref('all')
const searchKeyword = ref('')
const showWriteForm = ref(false)  // 是否显示撰写表单
const newPost = ref({
  title: '',
  tags: '',
  content: ''
})
const isSubmitting = ref(false)

// ===== 计算属性 =====
// 所有标签
const allTags = computed(() => {
  const tags = new Set()
  articles.value.forEach(article => {
    article.tags.forEach(tag => tags.add(tag))
  })
  return Array.from(tags).sort()
})

// 筛选后的文章（标签 + 搜索同时生效）
const filteredArticles = computed(() => {
  let result = articles.value
  
  // 标签筛选
  if (currentTag.value !== 'all') {
    result = result.filter(a => a.tags.includes(currentTag.value))
  }
  
  // 搜索筛选
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    result = result.filter(a => 
      a.title.toLowerCase().includes(kw) || 
      a.fullContent.toLowerCase().includes(kw)
    )
  }
  
  return result
})

// ===== 辅助函数 =====
// 高亮关键字
const highlightText = (text, keyword) => {
  if (!keyword || !text) return text
  const kw = keyword.toLowerCase()
  const lowerText = text.toLowerCase()
  const index = lowerText.indexOf(kw)
  if (index === -1) return text
  return text.slice(0, index) + 
         `<mark class="highlight">${text.slice(index, index + keyword.length)}</mark>` + 
         text.slice(index + keyword.length)
}

// 提交文章到后端
const submitPost = async () => {
  if (!newPost.value.title.trim()) {
    alert('请填写文章标题')
    return
  }
  if (!newPost.value.content.trim()) {
    alert('请填写文章内容')
    return
  }
  if (isSubmitting.value) return
  // 校验...
  isSubmitting.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/save-post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: newPost.value.title,
        tags: newPost.value.tags,
        content: newPost.value.content
      })
    })
    const data = await response.json()
    if (data.success) {
      alert('文章已保存！')
      // 重置表单并刷新文章列表
      newPost.value = { title: '', tags: '', content: '' }
      showWriteForm.value = false
      // 重新加载文章
      await fetchArticles()
    } else {
      alert('保存失败：' + data.error)
    }
  } catch (err) {
    console.error(err)
    alert('请求后端失败，请确保后端服务已启动（npm run server）')
  } finally {
    isSubmitting.value = false
  }
}

// ===== 加载文章 =====
const fetchArticles = async () => {
  loading.value = true
  try {
    const res = await fetch('${API_BASE_URL}/posts.json')
    if (!res.ok) throw new Error('加载失败')
    
    const fileNames = await res.json()
    const list = []
    
    for (const name of fileNames) {
      try {
        const mdRes = await fetch(`${API_BASE_URL}/posts/${name}.md`)
        if (!mdRes.ok) continue
        
        const text = await mdRes.text()
        const { data, content } = parseFrontmatter(text)
        const plain = getPlainText(content)
        
        list.push({
          id: name,
          title: data.title || '无标题',
          date: data.date || '',
          tags: data.tags || [],
          excerpt: plain.slice(0, 100) + (plain.length > 100 ? '...' : ''),
          fullContent: plain
        })
      } catch (err) {
        console.error(`加载 ${name} 失败：` + err)
      }
    }
    
    list.sort((a, b) => new Date(b.date) - new Date(a.date))
    articles.value = list
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchArticles)
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
/* 页面标题 */
.home h2 {
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

/* 搜索栏 */
.search-bar {
  position: relative;
  margin-bottom: 1.5rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.95rem;
  background-color: #f8f9fa;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #42b983;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.1);
}

.clear-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  color: #999;
  padding: 4px 8px;
  border-radius: 20px;
}

.clear-btn:hover {
  color: #666;
  background-color: #f0f0f0;
}

/* 标签栏 */
.tags-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.tag-btn {
  background: #f0f0f0;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s;
  color: #666;
}

.tag-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}

.tag-btn.active {
  background: #2c3e50;
  color: white;
}

/* 加载中 */
.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

/* 文章列表 */
.article-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.article-item {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s;
  text-decoration: none;
  display: block;
  color: inherit;
}

.article-item:hover {
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}

.article-title {
  font-size: 1.25rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.article-item:hover .article-title {
  color: #42b983;
}

.article-meta {
  display: flex;
  gap: 1rem;
  margin: 0.5rem 0;
  font-size: 0.875rem;
  color: #666;
  flex-wrap: wrap;
}

.tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.tag {
  background: #f0f0f0;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.article-excerpt {
  color: #666;
  line-height: 1.5;
  margin-top: 0.5rem;
}

/* 高亮 */
.highlight {
  background-color: #ffeb3b;
  color: #333;
  padding: 0 2px;
  border-radius: 2px;
}

/* 空状态 */
.no-articles {
  text-align: center;
  padding: 3rem;
  color: #999;
  background: white;
  border-radius: 8px;
}

/* 按钮栏 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}
.write-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.write-btn:hover {
  background: #359268;
}

/* 撰写表单 */
.write-form {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.write-form h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}
.form-input,
.form-textarea {
  width: 100%;
  padding: 10px;
  margin-bottom: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #42b983;
}
.form-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}
.submit-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
}
.cancel-btn {
  background: #ccc;
  color: #333;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
}
.hint {
  color: #999;
  font-size: 12px;
  margin-top: 0.5rem;
}

.search-bar,
.tags-bar,
.article-list {
  width: 700px;
}
</style>