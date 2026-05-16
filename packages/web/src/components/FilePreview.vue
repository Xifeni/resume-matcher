<template>
  <div :class="$style.previewContainer">
    <div v-if="isDocx" ref="docxContainer" :class="$style.docxWrapper"></div>

    <div v-else-if="isDoc" :class="$style.empty">
      Preview for .doc is not available in the browser; the file will be
      processed on the server.
    </div>

    <embed
      v-else-if="isPdf && fileUrl"
      :src="fileUrl"
      type="application/pdf"
      width="100%"
      height="100%"
    />

    <div v-else :class="$style.empty">Format not supported for preview</div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  ref,
  onMounted,
  watch,
  onBeforeUnmount,
  nextTick,
} from "vue";
import { renderAsync } from "docx-preview";

const props = defineProps<{
  file: File | null;
}>();

const docxContainer = ref<HTMLElement | null>(null);
const fileUrl = ref<string>("");

const isPdf = computed(() => props.file?.type === "application/pdf");

const isDocx = computed(
  () =>
    props.file?.name.toLowerCase().endsWith(".docx") ||
    props.file?.type ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
);

const isDoc = computed(
  () =>
    props.file?.name.toLowerCase().endsWith(".doc") ||
    props.file?.type === "application/msword",
);

const updateFileUrl = () => {
  if (fileUrl.value) {
    URL.revokeObjectURL(fileUrl.value);
    fileUrl.value = "";
  }
  if (props.file && isPdf.value) {
    fileUrl.value = URL.createObjectURL(props.file);
  }
};

const renderDocx = async () => {
  if (isDocx.value && props.file && docxContainer.value) {
    docxContainer.value.innerHTML = "";

    try {
      const arrayBuffer = await props.file.arrayBuffer();
      await renderAsync(arrayBuffer, docxContainer.value);
    } catch (e) {
      console.error("Error rendering docx:", e);
      if (docxContainer.value) {
        docxContainer.value.innerHTML =
          "<div style='text-align: center; padding: 20px;'>Failed to preview document.</div>";
      }
    }
  }
};

const handleFileChange = async () => {
  updateFileUrl();

  if (isDocx.value) {
    await nextTick();
    renderDocx();
  }
};

onMounted(handleFileChange);
watch(() => props.file, handleFileChange);

onBeforeUnmount(() => {
  if (fileUrl.value) {
    URL.revokeObjectURL(fileUrl.value);
  }
});
</script>

<style module>
.previewContainer {
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.docxWrapper {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  box-sizing: border-box;
}
.empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
  font-size: 14px;
  text-align: center;
  padding: 20px;
}
</style>
