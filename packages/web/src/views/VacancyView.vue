<template>
  <el-container :class="$style.documentLayout">
    <el-header :class="$style.documentHeader">
      <el-button @click="router.push('/')">Back</el-button>
      <h3 :class="$style.documentTitle">{{ title }}</h3>
    </el-header>
    <el-main v-loading="loading" :class="$style.documentMain">
      <FilePreview v-if="fileObject" :file="fileObject" />
      <TextPreview
        v-else-if="remoteDoc"
        :text="remoteDoc.extracted_text"
      />
      <div v-else-if="loadError" :class="$style.notFound">
        {{ loadError }}
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import FilePreview from "@/components/FilePreview.vue";
import TextPreview from "@/components/TextPreview.vue";
import { useStoredDocument } from "@/composables/useStoredDocument";

const route = useRoute();
const router = useRouter();
const docId = Number(route.params.id);

const { fileObject, remoteDoc, loading, loadError, title } = useStoredDocument(
  docId,
  "vacancy",
  "Vacancy Not Found",
);
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
