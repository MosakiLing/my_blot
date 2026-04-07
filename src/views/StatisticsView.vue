<template>
  <div class="statistics">
    <h1>文章数据统计</h1>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="charts-container">
      <div class="chart-box">
        <h2>文章标签分布</h2>
        <div ref="pieChartRef" class="chart"></div>
      </div>
      <div class="chart-box">
        <h2>每月发文数量</h2>
        <div ref="barChartRef" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { parseFrontmatter } from '@/utils/markdown'

const API_BASE_URL = 'https://web-production-b655b.up.railway.app'
// const API_BASE_URL = 'http://localhost:3000'
const pieChartRef = ref(null)
const barChartRef = ref(null)
const loading = ref(true)

// 获取所有文章数据
const fetchStatistics = async () => {
  try {
    loading.value = true
    const res = await fetch(`${API_BASE_URL}/posts.json`)
    const fileNames = await res.json()
    const articles = []

    for (const name of fileNames) {
      const mdRes = await fetch(`${API_BASE_URL}/posts/${name}.md`)
      const text = await mdRes.text()
      const { data } = parseFrontmatter(text)
      articles.push({
        title: data.title,
        date: data.date,
        tags: data.tags || []
      })
    }

    // 统计标签分布
    const tagCount = {}
    articles.forEach(article => {
      article.tags.forEach(tag => {
        tagCount[tag] = (tagCount[tag] || 0) + 1
      })
    })
    const pieData = Object.entries(tagCount).map(([name, value]) => ({ name, value }))

    // 统计每月发文数量
    const monthCount = {}
    articles.forEach(article => {
      if (article.date) {
        const yearMonth = article.date.slice(0, 7) // 格式 YYYY-MM
        monthCount[yearMonth] = (monthCount[yearMonth] || 0) + 1
      }
    })
    const sortedMonths = Object.keys(monthCount).sort()
    const barData = sortedMonths.map(month => monthCount[month])

    // 先关闭 loading，让图表容器渲染出来
    loading.value = false
    await nextTick()  // 等待 DOM 更新

    // 渲染饼图
    if (pieChartRef.value) {
      const pieChart = echarts.init(pieChartRef.value)
      pieChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 5 },
        series: [{
          type: 'pie',
          radius: '50%',
          data: pieData,
          emphasis: { scale: true },
          label: { show: true, formatter: '{b}: {d}%', avoidLabelOverlap: true }
        }]
      })
    }

    // 渲染柱状图
    if (barChartRef.value) {
      const barChart = echarts.init(barChartRef.value)
      barChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: sortedMonths, name: '月份' },
        yAxis: { type: 'value', name: '文章数量' },
        series: [{
          type: 'bar',
          data: barData,
          itemStyle: { color: '#42b983', borderRadius: [4,4,0,0] },
          barWidth: '30%',
          label: {
            show: true,
            position: 'top',
            formatter: '{c} 篇'
          }
        }]
      })
    }

  } catch (err) {
    console.error('统计数据加载失败', err)
    loading.value = false
  }
}

onMounted(() => {
  fetchStatistics()
})
</script>

<style scoped>
.statistics {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1rem;
}
.charts-container {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  justify-content: center;
}
.chart-box {
  flex: 1;
  min-width: 450px;
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.chart-box h3 {
  text-align: center;
  margin-bottom: 1rem;
  color: #2c3e50;
}
.chart {
  width: 100%;
  height: 400px;
}

@media (max-width: 640px) {
  .charts-container {
    flex-direction: column !important;
    align-items: stretch;
  }

  .chart-box {
    min-width: auto;
    width: 100%;
  }
  
  .statistics {
    padding: 0.5rem;
  }
  
  .charts-container {
    gap: 1rem;
  }
}
</style>