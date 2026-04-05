<template>
  <HomeView />
</template>

<script setup>
import HomeView from './views/HomeView.vue'
</script>

<style>
/*
 * 修复 Vuetify 3 按钮点击/悬停后蒙层残留问题：
 * 当指针离开按钮时，overlay 快速淡出；聚焦按钮不显示持久蒙层。
 */
.v-btn .v-btn__overlay {
  transition: opacity 0.12s ease !important;
}
.v-btn:not(:hover):not(:focus-visible) .v-btn__overlay {
  opacity: 0 !important;
}
/* 去掉卡片操作区按钮点击后残留的激活色块 */
.v-card-actions .v-btn--active .v-btn__overlay {
  opacity: 0 !important;
}
</style>
