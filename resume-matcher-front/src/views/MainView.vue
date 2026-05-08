<template>
  <el-container :class="$style.layoutContainer">
    <!-- Боковое меню -->
    <el-aside :width="isCollapsed ? '64px' : '250px'" :class="$style.asideMenu">
      <div :class="$style.logoContainer">
        <h3 v-if="!isCollapsed">My Application</h3>
        <h3 v-else>App</h3>
      </div>

      <el-menu
        default-active="1"
        :class="$style.elMenuVertical"
        :collapse="isCollapsed"
        @select="handleMenuSelect"
      >
        <!-- Upload Resume -->
        <el-menu-item
          index="upload-resume"
          :class="{ [$style.disabledItem]: fileStore.resumeFile || fileStore.isPredicting }"
        >
          <el-icon><Document /></el-icon>
          <template #title>
            <div :class="$style.menuContent">
              <span>{{ fileStore.resumeFile ? 'Resume Loaded' : 'Upload Resume' }}</span>
              <el-icon
                v-if="fileStore.resumeFile"
                @click.stop="clearResume"
                :class="$style.clearBtn"
              >
                <Close />
              </el-icon>
            </div>
          </template>
        </el-menu-item>

        <!-- Upload Vacancy -->
        <el-menu-item
          index="upload-vacancy"
          :class="{ [$style.disabledItem]: fileStore.vacancyFile || fileStore.isPredicting }"
        >
          <el-icon><Suitcase /></el-icon>
          <template #title>
            <div :class="$style.menuContent">
              <span>{{ fileStore.vacancyFile ? 'Vacancy Loaded' : 'Upload Vacancy' }}</span>
              <el-icon
                v-if="fileStore.vacancyFile"
                @click.stop="clearVacancy"
                :class="$style.clearBtn"
              >
                <Close />
              </el-icon>
            </div>
          </template>
        </el-menu-item>

        <!-- Predict -->
        <el-menu-item
          index="predict"
          :disabled="!canPredict || fileStore.isPredicting"
        >
          <el-icon v-if="fileStore.isPredicting" class="is-loading"><Loading /></el-icon>
          <el-icon v-else><DataAnalysis /></el-icon>
          <template #title>Predict</template>
        </el-menu-item>
      </el-menu>

      <!-- Скрытые элементы для выбора файлов -->
      <input type="file" ref="resumeInput" accept=".pdf,.docx" style="display: none" @change="onResumeChange" />
      <input type="file" ref="vacancyInput" accept=".pdf,.docx" style="display: none" @change="onVacancyChange" />
    </el-aside>

    <!-- Основной контент -->
    <el-container>
      <!-- Верхний тулбар возвращен -->
      <el-header :class="$style.header">
        <el-button
          @click="toggleSidebar"
          :icon="isCollapsed ? Expand : Fold"
          text
        />
        <div :class="$style.headerActions">
          <span :class="$style.userEmail" v-if="authStore.email">{{ authStore.email }}</span>
          <el-button type="danger" text @click="logout">Log Out</el-button>
        </div>
      </el-header>

      <el-main :class="$style.mainContent">
        <!-- Вкладки с превью файлов -->
        <el-tabs
          v-if="fileStore.resumeFile || fileStore.vacancyFile"
          v-model="activeTab"
          type="card"
        >
          <el-tab-pane v-if="fileStore.resumeFile" label="Resume" name="resume">
            <FilePreview :file="fileStore.resumeFile" />
          </el-tab-pane>
          <el-tab-pane v-if="fileStore.vacancyFile" label="Vacancy" name="vacancy">
            <FilePreview :file="fileStore.vacancyFile" />
          </el-tab-pane>
        </el-tabs>

        <!-- Состояние по умолчанию -->
        <div v-else>
          <h2>Dashboard</h2>
          <p>Please upload a resume and a vacancy to start analysis.</p>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useFileStore } from '@/stores/fileStore';
import FilePreview from '@/components/FilePreview.vue';
import {
  Document, Suitcase, DataAnalysis,
  Fold, Expand, Close, Loading
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const router = useRouter();
const authStore = useAuthStore();
const fileStore = useFileStore();

const isCollapsed = ref(false);
const activeTab = ref('resume');

const resumeInput = ref<HTMLInputElement | null>(null);
const vacancyInput = ref<HTMLInputElement | null>(null);

const canPredict = computed(() => fileStore.resumeFile && fileStore.vacancyFile);

// Переключение табов при загрузке файлов
watch(() => fileStore.resumeFile, (val) => { if (val) activeTab.value = 'resume'; });
watch(() => fileStore.vacancyFile, (val) => { if (val && !fileStore.resumeFile) activeTab.value = 'vacancy'; });

// Управление меню и загрузкой
const handleMenuSelect = (index: string) => {
  if (fileStore.isPredicting) return;

  if (index === 'upload-resume') {
    if (!fileStore.resumeFile) resumeInput.value?.click();
  } else if (index === 'upload-vacancy') {
    if (!fileStore.vacancyFile) vacancyInput.value?.click();
  } else if (index === 'predict') {
    if (canPredict.value) handlePredict();
  }
};

const onResumeChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    fileStore.setResume(target.files[0]);
    target.value = ''; // Очищаем input, чтобы можно было загрузить тот же файл заново
  }
};

const onVacancyChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    fileStore.setVacancy(target.files[0]);
    target.value = '';
  }
};

const clearResume = () => {
  if (fileStore.isPredicting) return;
  fileStore.clearResume();
};

const clearVacancy = () => {
  if (fileStore.isPredicting) return;
  fileStore.clearVacancy();
};

// Экшены
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

const handlePredict = async () => {
  try {
    await fileStore.runPredict();
    ElMessage.success('Prediction complete!');
  } catch (e) {
    ElMessage.error('Error during prediction');
  }
};

const logout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style module>
/* Оригинальные стили с поддержкой CSS Modules */
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

/* Новые классы для логики загрузки внутри меню */
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
</style>