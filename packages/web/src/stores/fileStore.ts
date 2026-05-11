import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api/client';
import localforage from 'localforage';

export interface PredictionResult {
  final_score: number;
  details: {
    semantic_similarity: number;
    llm_judge_score: number;
    reasoning: string;
  };
  analysis_id?: number;
  resume_id?: number;
  vacancy_id?: number;
}

localforage.config({
  name: 'ResumeMatcherApp',
  storeName: 'files_store'
});

export const useFileStore = defineStore('files', () => {
  const resumeFile = ref<File | null>(null);
  const vacancyFile = ref<File | null>(null);
  const isPredicting = ref(false);
  const predictionResult = ref<PredictionResult | null>(null);
  const isInitializing = ref(true);

  const initStore = async () => {
    try {
      const savedResume = await localforage.getItem<File>('resumeFile');
      const savedVacancy = await localforage.getItem<File>('vacancyFile');

      if (savedResume) resumeFile.value = savedResume;
      if (savedVacancy) vacancyFile.value = savedVacancy;
    } catch (e) {
      console.error('Error loading files from local storage', e);
    } finally {
      isInitializing.value = false;
    }
  };

  initStore();

  const setResume = async (file: File) => {
    resumeFile.value = file;
    predictionResult.value = null;
    await localforage.setItem('resumeFile', file);
  };

  const setVacancy = async (file: File) => {
    vacancyFile.value = file;
    predictionResult.value = null;
    await localforage.setItem('vacancyFile', file);
  };

  const clearResume = async () => {
    resumeFile.value = null;
    predictionResult.value = null;
    await localforage.removeItem('resumeFile');
  };

  const clearVacancy = async () => {
    vacancyFile.value = null;
    predictionResult.value = null;
    await localforage.removeItem('vacancyFile');
  };

  const runPredict = async () => {
    if (!resumeFile.value || !vacancyFile.value) return;

    isPredicting.value = true;
    predictionResult.value = null;

    const formData = new FormData();
    formData.append('resume', resumeFile.value);
    formData.append('vacancy', vacancyFile.value);

    try {
      const response = await apiClient.post<PredictionResult>('/predict', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      predictionResult.value = response.data;
      return response.data;
    } finally {
      isPredicting.value = false;
    }
  };

  return {
    resumeFile,
    vacancyFile,
    isPredicting,
    predictionResult,
    isInitializing,
    setResume,
    setVacancy,
    clearResume,
    clearVacancy,
    runPredict
  };
});
