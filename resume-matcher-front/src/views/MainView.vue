<template>
  <el-container :class="$style.layoutContainer">
    <el-aside :width="isCollapsed ? '64px' : '250px'" :class="$style.asideMenu">
      <div :class="$style.logoContainer">
        <h3 v-if="!isCollapsed">Resume matcher</h3>
        <h3 v-else>RM</h3>
      </div>

      <el-menu
        default-active="1"
        :class="$style.elMenuVertical"
        :collapse="isCollapsed"
        @select="handleMenuSelect"
      >
        <el-menu-item
          index="upload-resume"
          :class="{
            [$style.disabledItem]:
              fileStore.resumeFile || fileStore.isPredicting,
          }"
        >
          <el-icon><Document /></el-icon>
          <template #title>
            <div :class="$style.menuContent">
              <span>{{
                fileStore.resumeFile ? "Resume Loaded" : "Upload Resume"
              }}</span>
              <el-icon
                v-if="fileStore.resumeFile"
                @click.stop="clearResume"
                :class="$style.clearBtn"
                ><Close
              /></el-icon>
            </div>
          </template>
        </el-menu-item>

        <el-menu-item
          index="upload-vacancy"
          :class="{
            [$style.disabledItem]:
              fileStore.vacancyFile || fileStore.isPredicting,
          }"
        >
          <el-icon><Suitcase /></el-icon>
          <template #title>
            <div :class="$style.menuContent">
              <span>{{
                fileStore.vacancyFile ? "Vacancy Loaded" : "Upload Vacancy"
              }}</span>
              <el-icon
                v-if="fileStore.vacancyFile"
                @click.stop="clearVacancy"
                :class="$style.clearBtn"
                ><Close
              /></el-icon>
            </div>
          </template>
        </el-menu-item>

        <el-menu-item
          index="predict"
          :disabled="!canPredict || fileStore.isPredicting"
        >
          <el-icon v-if="fileStore.isPredicting" class="is-loading"
            ><Loading
          /></el-icon>
          <el-icon v-else><DataAnalysis /></el-icon>
          <template #title>Predict</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header :class="$style.header">
        <el-button
          @click="toggleSidebar"
          :icon="isCollapsed ? Expand : Fold"
          text
        />
        <div :class="$style.headerActions">
          <span :class="$style.userEmail" v-if="authStore.email">{{
            authStore.email
          }}</span>
          <el-button type="danger" text @click="logout">Log Out</el-button>
        </div>
      </el-header>

      <el-main :class="$style.mainContent">
        <el-tabs
          v-if="fileStore.resumeFile || fileStore.vacancyFile"
          v-model="activeTab"
          type="card"
        >
          <el-tab-pane v-if="fileStore.resumeFile" label="Resume" name="resume">
            <FilePreview :file="fileStore.resumeFile" />
          </el-tab-pane>
          <el-tab-pane
            v-if="fileStore.vacancyFile"
            label="Vacancy"
            name="vacancy"
          >
            <FilePreview :file="fileStore.vacancyFile" />
          </el-tab-pane>

          <el-tab-pane
            v-if="fileStore.predictionResult"
            label="Analysis Results"
            name="result"
          >
            <div :class="$style.resultContainer">
              <h2 :class="$style.resultTitle">Match Analysis</h2>

              <el-row :gutter="20">
                <el-col :span="8">
                  <el-card shadow="hover" :class="$style.scoreCard">
                    <template #header
                      ><div class="card-header">
                        Final Match Score
                      </div></template
                    >
                    <el-progress
                      type="dashboard"
                      :percentage="fileStore.predictionResult.final_score"
                      :color="scoreColors"
                    />
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card shadow="hover" :class="$style.scoreCard">
                    <template #header
                      ><div class="card-header">
                        Semantic Similarity
                      </div></template
                    >
                    <el-progress
                      type="dashboard"
                      :percentage="
                        fileStore.predictionResult.details.semantic_similarity
                      "
                      :color="scoreColors"
                    />
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card shadow="hover" :class="$style.scoreCard">
                    <template #header
                      ><div class="card-header">LLM Judge Score</div></template
                    >
                    <el-progress
                      type="dashboard"
                      :percentage="
                        fileStore.predictionResult.details.llm_judge_score
                      "
                      :color="scoreColors"
                    />
                  </el-card>
                </el-col>
              </el-row>

              <el-card shadow="never" :class="$style.reasoningCard">
                <template #header>
                  <div class="card-header">
                    <h3>AI Reasoning</h3>
                  </div>
                </template>
                <div :class="$style.reasoningText">
                  {{ fileStore.predictionResult.details.reasoning }}
                </div>
              </el-card>
            </div>
          </el-tab-pane>
        </el-tabs>

        <div v-else :class="$style.emptyState">
          <h2>Dashboard</h2>
          <p>Please upload a resume and a vacancy to start analysis.</p>
        </div>
      </el-main>
    </el-container>

    <el-dialog
      v-model="uploadDialogVisible"
      :title="uploadType === 'resume' ? 'Upload Resume' : 'Upload Vacancy'"
      width="400px"
      align-center
    >
      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        accept=".pdf,.docx"
        @change="handleFileUpload"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          Drop file here or <em>click to upload</em>
        </div>
        <template #tip>
          <div
            class="el-upload__tip"
            style="text-align: center; margin-top: 10px"
          >
            Supported formats: PDF, DOCX
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useFileStore } from "@/stores/fileStore";
import FilePreview from "@/components/FilePreview.vue";
import {
  Document,
  Suitcase,
  DataAnalysis,
  Fold,
  Expand,
  Close,
  Loading,
  UploadFilled,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const router = useRouter();
const authStore = useAuthStore();
const fileStore = useFileStore();

const isCollapsed = ref(false);
const activeTab = ref("resume");

const uploadDialogVisible = ref(false);
const uploadType = ref<"resume" | "vacancy" | null>(null);

const canPredict = computed(
  () => fileStore.resumeFile && fileStore.vacancyFile,
);

const scoreColors = [
  { color: "#f56c6c", percentage: 40 },
  { color: "#e6a23c", percentage: 70 },
  { color: "#5cb87a", percentage: 100 },
];

const handleMenuSelect = (index: string) => {
  if (fileStore.isPredicting) return;

  if (index === "upload-resume" && !fileStore.resumeFile) {
    uploadType.value = "resume";
    uploadDialogVisible.value = true;
  } else if (index === "upload-vacancy" && !fileStore.vacancyFile) {
    uploadType.value = "vacancy";
    uploadDialogVisible.value = true;
  } else if (index === "predict" && canPredict.value) {
    handlePredict();
  }
};

const handleFileUpload = (file: any) => {
  if (!file || !file.raw) return;

  if (uploadType.value === "resume") {
    fileStore.setResume(file.raw);
    activeTab.value = "resume";
  } else if (uploadType.value === "vacancy") {
    fileStore.setVacancy(file.raw);
    activeTab.value = "vacancy";
  }

  uploadDialogVisible.value = false;
  uploadType.value = null;
};
const clearResume = () => {
  if (!fileStore.isPredicting) fileStore.clearResume();
};
const clearVacancy = () => {
  if (!fileStore.isPredicting) fileStore.clearVacancy();
};
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

const handlePredict = async () => {
  try {
    await fileStore.runPredict();
    ElMessage.success("Prediction complete!");
    activeTab.value = "result";
  } catch (e) {
    ElMessage.error("Error during prediction");
  }
};

const logout = () => {
  authStore.logout();
  router.push("/login");
};
</script>

<style module>
.layoutContainer {
  height: 100vh;
}
.asideMenu {
  background-color: #fff;
  border-right: solid 1px #e6e6e6;
  transition: width 0.3s;
  overflow: hidden;
}
.logoContainer {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #e6e6e6;
  white-space: nowrap;
}
.elMenuVertical {
  border-right: none;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
  background-color: #fff;
}
.headerActions {
  display: flex;
  align-items: center;
}
.userEmail {
  margin-right: 15px;
  color: #606266;
  font-size: 14px;
}
.mainContent {
  background-color: #f3f4f6;
  padding: 20px;
}
.emptyState {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
}
.menuContent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.clearBtn {
  color: #f56c6c;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}
.clearBtn:hover {
  background-color: #fef0f0;
}
.disabledItem {
  color: #a8abb2;
  cursor: default;
}

/* НОВЫЕ СТИЛИ ДЛЯ РЕЗУЛЬТАТОВ */
.resultContainer {
  padding: 10px 0;
}
.resultTitle {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
}
.scoreCard {
  text-align: center;
  height: 100%;
}
.reasoningCard {
  margin-top: 20px;
  background-color: #fafafa;
}
.reasoningText {
  white-space: pre-wrap; /* Сохраняет абзацы от LLM */
  line-height: 1.6;
  color: #303133;
  font-size: 15px;
}
</style>
