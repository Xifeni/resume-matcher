<template>
  <div :class="$style.previewContainer">
    <div v-if="isDocx" ref="docxContainer" :class="$style.docxWrapper"></div>
    <div v-else-if="isDoc" :class="$style.empty">
      Предпросмотр .doc в браузере недоступен; файл будет обработан на сервере.
    </div>
    <embed
      v-else-if="isPdf"
      :src="fileUrl"
      type="application/pdf"
      width="100%"
      height="100%"
    />
    <div v-else :class="$style.empty">Format not supported for preview</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { renderAsync } from "docx-preview";

const props = defineProps<{
  file: File | null;
}>();

const docxContainer = ref<HTMLElement | null>(null);
const fileUrl = computed(() =>
  props.file ? URL.createObjectURL(props.file) : "",
);
const isPdf = computed(() => props.file?.type === "application/pdf");
const isDocx = computed(
  () =>
    props.file?.name.endsWith(".docx") ||
    props.file?.type ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
);
const isDoc = computed(
  () =>
    props.file?.name.toLowerCase().endsWith(".doc") ||
    props.file?.type === "application/msword",
);

const renderDocx = async () => {
  if (isDocx.value && props.file && docxContainer.value) {
    const arrayBuffer = await props.file.arrayBuffer();
    await renderAsync(arrayBuffer, docxContainer.value);
  }
};

onMounted(renderDocx);
watch(() => props.file, renderDocx);
</script>

<style module>
.previewContainer {
  width: 100%;
  height: calc(100vh - 200px);
  border: 1px solid #ddd;
  background: #fff;
}
.docxWrapper {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}
.empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}
</style>
