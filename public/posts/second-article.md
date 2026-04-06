---
title: Vue3 入门(组合式API)
date: 2026-03-31
tags: Vue, 前端, 入门, 文章
---

# Vue3 组合式API 学习笔记

## 什么是组合式API？

组合式API（Composition API）是 Vue 3 新增的写法，让代码组织更灵活。

## 代码示例

```javascript
<script setup>
import { ref } from 'vue'

const count = ref(0)

function increment() {
  count.value++
}
</script>