<template>
  <pre :class="$style.textPreview">{{ text }}</pre>
</template>

<script setup lang="ts">
defineProps<{
  text: string;
}>();
</script>

<style module>
.textPreview {
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 20px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  overflow: auto;
  box-sizing: border-box;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}
</style>
