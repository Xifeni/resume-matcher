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
          :disabled="fileStore.isPredicting || fileStore.isUploading"
        >
          <el-icon><Document /></el-icon>
          <template #title>
            <div :class="$style.menuContent">
              <span>{{
                fileStore.resumeFiles.length
                  ? `Resumes (${fileStore.resumeFiles.length})`
                  : "Upload Resume"
              }}</span>
              <el-icon
                v-if="fileStore.resumeFiles.length"
                @click.stop="clearAllResumes"
                :class="$style.clearBtn"
                ><Close
              /></el-icon>
            </div>
          </template>
        </el-menu-item>

        <el-menu-item
          index="upload-vacancy"
          :disabled="fileStore.isPredicting || fileStore.isUploading"
        >
          <el-icon><Suitcase /></el-icon>
          <template #title>
            <div :class="$style.menuContent">
              <span>{{
                fileStore.vacancyFiles.length
                  ? `Vacancies (${fileStore.vacancyFiles.length})`
                  : "Upload Vacancy"
              }}</span>
              <el-icon
                v-if="fileStore.vacancyFiles.length"
                @click.stop="clearAllVacancies"
                :class="$style.clearBtn"
                ><Close
              /></el-icon>
            </div>
          </template>
        </el-menu-item>

        <el-menu-item
          index="predict"
          :disabled="fileStore.isPredicting || fileStore.isUploading"
        >
          <el-icon v-if="fileStore.isPredicting" class="is-loading"
            ><Loading
          /></el-icon>
          <el-icon v-else><DataAnalysis /></el-icon>
          <template #title>
            <div :class="$style.menuContent">
              <span>Predict Match</span>
              <el-icon
                v-if="fileStore.batchResults.length"
                @click.stop="clearResults"
                :class="$style.clearBtn"
                ><Close
              /></el-icon>
            </div>
          </template>
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
          v-if="fileStore.resumeFiles.length || fileStore.vacancyFiles.length"
          v-model="activeTab"
          type="card"
          class="custom-tabs"
        >
          <el-tab-pane
            v-if="fileStore.resumeFiles.length"
            label="Resumes"
            name="resume"
          >
            <div
              v-if="fileStore.resumeFiles.length > 1"
              :class="$style.paginationContainer"
            >
              <el-pagination
                v-model:current-page="currentResumePage"
                :page-size="1"
                :total="fileStore.resumeFiles.length"
                layout="prev, pager, next"
                background
              />
              <span :class="$style.activeFileName">
                <el-tag type="info" size="small" class="mr-2"
                  >ID: {{ activeResumeItem?.id }}</el-tag
                >
                {{ activeResumeFile?.name }}
              </span>
              <el-button
                type="danger"
                text
                size="small"
                @click="deleteCurrentResume"
                >Remove</el-button
              >
            </div>
            <div v-else :class="$style.paginationContainer">
              <span :class="$style.activeFileName">
                <el-tag type="info" size="small" class="mr-2"
                  >ID: {{ activeResumeItem?.id }}</el-tag
                >
                {{ activeResumeFile?.name }}
              </span>
              <el-button
                type="danger"
                text
                size="small"
                @click="deleteCurrentResume"
                >Remove</el-button
              >
            </div>

            <FilePreview v-if="activeResumeFile" :file="activeResumeFile" />
          </el-tab-pane>

          <el-tab-pane
            v-if="fileStore.vacancyFiles.length"
            label="Vacancies"
            name="vacancy"
          >
            <div
              v-if="fileStore.vacancyFiles.length > 1"
              :class="$style.paginationContainer"
            >
              <el-pagination
                v-model:current-page="currentVacancyPage"
                :page-size="1"
                :total="fileStore.vacancyFiles.length"
                layout="prev, pager, next"
                background
              />
              <span :class="$style.activeFileName">
                <el-tag type="info" size="small" class="mr-2"
                  >ID: {{ activeVacancyItem?.id }}</el-tag
                >
                {{ activeVacancyFile?.name }}
              </span>
              <el-button
                type="danger"
                text
                size="small"
                @click="deleteCurrentVacancy"
                >Remove</el-button
              >
            </div>
            <div v-else :class="$style.paginationContainer">
              <span :class="$style.activeFileName">
                <el-tag type="info" size="small" class="mr-2"
                  >ID: {{ activeVacancyItem?.id }}</el-tag
                >
                {{ activeVacancyFile?.name }}
              </span>
              <el-button
                type="danger"
                text
                size="small"
                @click="deleteCurrentVacancy"
                >Remove</el-button
              >
            </div>

            <FilePreview v-if="activeVacancyFile" :file="activeVacancyFile" />
          </el-tab-pane>

          <el-tab-pane
            v-if="fileStore.batchResults.length"
            label="Analysis Results"
            name="result"
          >
            <div :class="$style.resultContainer">
              <h2 :class="$style.resultTitle">
                Match Analysis ({{ resultsTableData.length }} combinations)
              </h2>

              <ResultsTable :tableData="resultsTableData" />
            </div>
          </el-tab-pane>
        </el-tabs>

        <div v-else :class="$style.emptyState">
          <h2>Dashboard</h2>
          <p>Please upload resumes and vacancies to start analysis.</p>
        </div>
      </el-main>
    </el-container>

    <el-dialog
      v-model="uploadDialogVisible"
      :title="uploadType === 'resume' ? 'Upload Resumes' : 'Upload Vacancies'"
      width="500px"
      align-center
      @closed="uploadFileList = []"
    >
      <el-upload
        drag
        multiple
        action="#"
        :auto-upload="false"
        v-model:file-list="uploadFileList"
        accept=".pdf,.doc,.docx"
        :disabled="fileStore.isUploading"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          Drop files here or <em>click to upload</em>
        </div>
        <template #tip>
          <div
            class="el-upload__tip"
            style="text-align: center; margin-top: 10px"
          >
            Supported formats: PDF, DOC, DOCX
          </div>
        </template>
      </el-upload>

      <template #footer>
        <span class="dialog-footer">
          <el-button
            @click="uploadDialogVisible = false"
            :disabled="fileStore.isUploading"
            >Cancel</el-button
          >
          <el-button
            type="primary"
            @click="commitUpload"
            :disabled="!uploadFileList.length"
            :loading="fileStore.isUploading"
          >
            Confirm Upload
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      v-model="predictDialogVisible"
      title="Run Prediction"
      width="600px"
      align-center
      @closed="
        selectedResumes = [];
        selectedVacancies = [];
      "
    >
      <div
        v-loading="fileStore.isUploading"
        element-loading-text="Uploading files..."
      >
        <div :class="$style.predictFormGroup">
          <label>Select Resumes</label>
          <div style="display: flex; gap: 10px">
            <el-select
              v-model="selectedResumes"
              multiple
              placeholder="Select resumes"
              style="flex: 1"
              :disabled="fileStore.isUploading"
            >
              <el-option
                v-for="item in fileStore.resumeFiles"
                :key="item.id"
                :label="item.file.name"
                :value="item.id"
                :disabled="isResumeDisabled(item.id)"
              />
            </el-select>
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              accept=".pdf,.doc,.docx"
              :disabled="fileStore.isUploading"
              @change="handleQuickResumeUpload"
            >
              <el-button type="primary" plain>Upload New</el-button>
            </el-upload>
          </div>
        </div>

        <div :class="$style.predictFormGroup" class="mt-5">
          <label>Select Vacancies</label>
          <div style="display: flex; gap: 10px">
            <el-select
              v-model="selectedVacancies"
              multiple
              placeholder="Select vacancies"
              style="flex: 1"
              :disabled="fileStore.isUploading"
            >
              <el-option
                v-for="item in fileStore.vacancyFiles"
                :key="item.id"
                :label="item.file.name"
                :value="item.id"
                :disabled="isVacancyDisabled(item.id)"
              />
            </el-select>
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              accept=".pdf,.doc,.docx"
              :disabled="fileStore.isUploading"
              @change="handleQuickVacancyUpload"
            >
              <el-button type="primary" plain>Upload New</el-button>
            </el-upload>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button
            @click="predictDialogVisible = false"
            :disabled="fileStore.isPredicting || fileStore.isUploading"
            >Cancel</el-button
          >
          <el-button
            type="primary"
            @click="executePredict"
            :loading="fileStore.isPredicting"
            :disabled="
              !selectedResumes.length ||
              !selectedVacancies.length ||
              fileStore.isUploading
            "
          >
            Run Predict
          </el-button>
        </span>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";
import { useFileStore } from "@/stores/fileStore";
import FilePreview from "@/components/FilePreview.vue";
import ResultsTable from "@/components/ResultsTable.vue";
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
import type { UploadUserFile } from "element-plus";

const router = useRouter();
const authStore = useAuthStore();
const fileStore = useFileStore();

const isCollapsed = ref(false);
const activeTab = ref("resume");

const uploadDialogVisible = ref(false);
const uploadType = ref<"resume" | "vacancy" | null>(null);
const uploadFileList = ref<UploadUserFile[]>([]);

const currentResumePage = ref(1);
const currentVacancyPage = ref(1);

const activeResumeItem = computed(
  () => fileStore.resumeFiles[currentResumePage.value - 1] || null,
);
const activeResumeFile = computed(() => activeResumeItem.value?.file || null);

const activeVacancyItem = computed(
  () => fileStore.vacancyFiles[currentVacancyPage.value - 1] || null,
);
const activeVacancyFile = computed(() => activeVacancyItem.value?.file || null);

const canPredict = computed(
  () => fileStore.resumeFiles.length > 0 && fileStore.vacancyFiles.length > 0,
);

const scoreColors = [
  { color: "#f56c6c", percentage: 40 },
  { color: "#e6a23c", percentage: 70 },
  { color: "#5cb87a", percentage: 100 },
];

const predictDialogVisible = ref(false);
const selectedResumes = ref<number[]>([]);
const selectedVacancies = ref<number[]>([]);

const hasPrediction = (vId: number, rId: number) => {
  const batch = fileStore.batchResults.find((b) => b.vacancy_id === vId);
  return batch ? batch.results.some((r) => r.resume_id === rId) : false;
};

const isResumeDisabled = (rId: number) => {
  if (!selectedVacancies.value.length) return false;
  return selectedVacancies.value.every((vId) => hasPrediction(vId, rId));
};

const isVacancyDisabled = (vId: number) => {
  if (!selectedResumes.value.length) return false;
  return selectedResumes.value.every((rId) => hasPrediction(vId, rId));
};

const handleQuickResumeUpload = async (file: any) => {
  if (!file.raw) return;
  try {
    const stats = await fileStore.addResumes([file.raw]);
    if (stats.saved > 0 && stats.results[0]?.id) {
      selectedResumes.value.push(stats.results[0].id);
      ElMessage.success("Resume uploaded and selected");
    } else {
      ElMessage.error("Failed to upload resume");
    }
  } catch (e) {
    ElMessage.error("Error connecting to server");
  }
};

const handleQuickVacancyUpload = async (file: any) => {
  if (!file.raw) return;
  try {
    const stats = await fileStore.addVacancies([file.raw]);
    if (stats.saved > 0 && stats.results[0]?.id) {
      selectedVacancies.value.push(stats.results[0].id);
      ElMessage.success("Vacancy uploaded and selected");
    } else {
      ElMessage.error("Failed to upload vacancy");
    }
  } catch (e) {
    ElMessage.error("Error connecting to server");
  }
};

const executePredict = async () => {
  if (!selectedResumes.value.length || !selectedVacancies.value.length) return;
  try {
    await fileStore.runPredict(selectedResumes.value, selectedVacancies.value);
    ElMessage.success("Prediction complete!");
    predictDialogVisible.value = false;
    activeTab.value = "result";
  } catch (e: any) {
    if (e?.name !== "CanceledError") {
      ElMessage.error("Error during prediction");
    }
  }
};

const removePredictionRow = async (row: any) => {
  await fileStore.removePredictionResult(row.vacancy_id, row.resume_id);
  ElMessage.success("Prediction result removed");
};

const handleMenuSelect = (index: string) => {
  if (fileStore.isPredicting || fileStore.isUploading) return;

  if (index === "upload-resume") {
    uploadType.value = "resume";
    uploadDialogVisible.value = true;
  } else if (index === "upload-vacancy") {
    uploadType.value = "vacancy";
    uploadDialogVisible.value = true;
  } else if (index === "predict") {
    predictDialogVisible.value = true;
  }
};

const resultsTableData = computed(() => {
  const data: any[] = [];
  for (const batch of fileStore.batchResults) {
    const vacancy = fileStore.vacancyFiles.find(
      (v) => v.id === batch.vacancy_id,
    );
    for (const res of batch.results) {
      const resume = fileStore.resumeFiles.find((r) => r.id === res.resume_id);
      data.push({
        id: `${batch.vacancy_id}_${res.resume_id}`,
        vacancyName: vacancy?.file.name || `Vacancy ID: ${batch.vacancy_id}`,
        resumeName: resume?.file.name || `Resume ID: ${res.resume_id}`,
        ...res,
      });
    }
  }
  return data;
});

const clearResults = async () => {
  if (!fileStore.isPredicting) {
    await fileStore.clearBatchResults();
    if (activeTab.value === "result") {
      activeTab.value = fileStore.resumeFiles.length ? "resume" : "vacancy";
    }
  }
};

const commitUpload = async () => {
  const filesToCommit = uploadFileList.value
    .map((f) => f.raw)
    .filter(Boolean) as File[];

  try {
    if (uploadType.value === "resume") {
      const stats = await fileStore.addResumes(filesToCommit);
      if (stats.saved < stats.total) {
        ElMessage.warning(
          `Saved ${stats.saved} of ${stats.total} resumes. Check errors.`,
        );
      } else {
        ElMessage.success("Resumes uploaded successfully");
      }
      activeTab.value = "resume";
      currentResumePage.value = fileStore.resumeFiles.length;
    } else if (uploadType.value === "vacancy") {
      const stats = await fileStore.addVacancies(filesToCommit);
      if (stats.saved < stats.total) {
        ElMessage.warning(
          `Saved ${stats.saved} of ${stats.total} vacancies. Check errors.`,
        );
      } else {
        ElMessage.success("Vacancies uploaded successfully");
      }
      activeTab.value = "vacancy";
      currentVacancyPage.value = fileStore.vacancyFiles.length;
    }
  } catch (error) {
    ElMessage.error("Error connecting to server during upload");
  } finally {
    uploadDialogVisible.value = false;
    uploadType.value = null;
    uploadFileList.value = [];
  }
};

const clearAllResumes = async () => {
  if (!fileStore.isPredicting && !fileStore.isUploading) {
    try {
      await fileStore.clearAllResumes();
      currentResumePage.value = 1;
      ElMessage.success("All resumes deleted successfully.");
    } catch (e) {
      ElMessage.error("Failed to clear resumes on the server.");
    }
  }
};

const clearAllVacancies = async () => {
  if (!fileStore.isPredicting && !fileStore.isUploading) {
    try {
      await fileStore.clearAllVacancies();
      currentVacancyPage.value = 1;
      ElMessage.success("All vacancies deleted successfully.");
    } catch (e) {
      ElMessage.error("Failed to clear vacancies on the server.");
    }
  }
};

const deleteCurrentResume = async () => {
  const idx = currentResumePage.value - 1;
  try {
    await fileStore.removeResume(idx);
    if (currentResumePage.value > fileStore.resumeFiles.length) {
      currentResumePage.value = Math.max(1, fileStore.resumeFiles.length);
    }
    ElMessage.success("Resume deleted successfully.");
  } catch (e) {
    ElMessage.error("Failed to delete resume from the server.");
  }
};

const deleteCurrentVacancy = async () => {
  const idx = currentVacancyPage.value - 1;
  try {
    await fileStore.removeVacancy(idx);
    if (currentVacancyPage.value > fileStore.vacancyFiles.length) {
      currentVacancyPage.value = Math.max(1, fileStore.vacancyFiles.length);
    }
    ElMessage.success("Vacancy deleted successfully.");
  } catch (e) {
    ElMessage.error("Failed to delete vacancy from the server.");
  }
};

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

const logout = () => {
  fileStore.abortPrediction();
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
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  overflow: hidden;
  box-sizing: border-box;
}
:global(.custom-tabs) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
}

:global(.custom-tabs .el-tabs__content) {
  flex: 1;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

:global(.custom-tabs .el-tab-pane) {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
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

.paginationContainer {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.activeFileName {
  display: flex;
  align-items: center;
  font-weight: 500;
  color: #303133;
  margin-left: auto;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.resultContainer {
  padding: 10px 0;
}

.resultTitle {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
}
</style>
