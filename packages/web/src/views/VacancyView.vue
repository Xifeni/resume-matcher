<template>
  <el-container :class="$style.documentLayout">
    <el-header :class="$style.documentHeader">
      <el-button @click="router.push('/')">Back</el-button>
      <h3 :class="$style.documentTitle">
        {{ fileObject?.name || "Vacancy Not Found" }}
      </h3>
    </el-header>
    <el-main :class="$style.documentMain">
      <FilePreview v-if="fileObject" :file="fileObject" />
      <div v-else :class="$style.notFound">
        File not available in local storage.
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useFileStore } from "@/stores/fileStore";
import FilePreview from "@/components/FilePreview.vue";

const route = useRoute();
const router = useRouter();
const fileStore = useFileStore();

const docId = Number(route.params.id);

const fileObject = computed(() => {
  return fileStore.vacancyFiles.find((v) => v.id === docId)?.file || null;
});
</script>

<style module>
.documentLayout {
  height: 100vh;
}
.documentHeader {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e6e6e6;
  background-color: #fff;
}
.documentTitle {
  margin-left: 20px;
  color: #303133;
}
.documentMain {
  background-color: #f3f4f6;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  overflow: hidden;
  box-sizing: border-box;
}
.notFound {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
}
</style>
