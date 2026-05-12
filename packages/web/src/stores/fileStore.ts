import { defineStore } from "pinia";
import { ref, toRaw } from "vue";
import apiClient from "@/api/client";
import localforage from "localforage";

export interface BatchResultItem {
  resume_id: number;
  ok: boolean;
  final_score?: number;
  details?: {
    semantic_similarity: number;
    llm_judge_score: number;
    reasoning: string;
  };
  error?: string;
  analysis_id?: number;
  vacancy_id?: number;
}

export interface BatchResponse {
  vacancy_id: number;
  results: BatchResultItem[];
}

export interface StoredFile {
  id: number;
  file: File;
}

localforage.config({
  name: "ResumeMatcherApp",
  storeName: "files_store",
});

export const useFileStore = defineStore("files", () => {
  const resumeFiles = ref<StoredFile[]>([]);
  const vacancyFiles = ref<StoredFile[]>([]);

  const isUploading = ref(false);
  const isPredicting = ref(false);
  const batchResults = ref<BatchResponse[]>([]);
  const isInitializing = ref(true);

  const initStore = async () => {
    try {
      const savedResumes =
        await localforage.getItem<StoredFile[]>("resumeFiles");
      const savedVacancies =
        await localforage.getItem<StoredFile[]>("vacancyFiles");
      const savedBatchResults =
        await localforage.getItem<BatchResponse[]>("batchResults");

      if (savedResumes && savedResumes.length > 0)
        resumeFiles.value = savedResumes;
      if (savedVacancies && savedVacancies.length > 0)
        vacancyFiles.value = savedVacancies;
      if (savedBatchResults && savedBatchResults.length > 0)
        batchResults.value = savedBatchResults;
    } catch (e) {
      console.error("Error loading files from local storage", e);
    } finally {
      isInitializing.value = false;
    }
  };

  initStore();

  const syncStorage = async () => {
    const rawResumes = resumeFiles.value.map((s) => ({
      id: s.id,
      file: toRaw(s.file),
    }));
    const rawVacancies = vacancyFiles.value.map((s) => ({
      id: s.id,
      file: toRaw(s.file),
    }));
    await localforage.setItem("resumeFiles", rawResumes);
    await localforage.setItem("vacancyFiles", rawVacancies);
    await localforage.setItem(
      "batchResults",
      JSON.parse(JSON.stringify(batchResults.value)),
    );
  };

  const addResumes = async (files: File[]) => {
    isUploading.value = true;
    try {
      const formData = new FormData();
      const rawFiles = files.map((f) => toRaw(f));
      rawFiles.forEach((f) => formData.append("files", f));

      const response = await apiClient.post("/resumes/batch", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const results = response.data.results || [];
      const newStored: StoredFile[] = [];

      results.forEach((res: any, index: number) => {
        if (res.ok && res.id) {
          newStored.push({ id: res.id, file: rawFiles[index] });
        }
      });

      resumeFiles.value.push(...newStored);
      batchResults.value = [];
      await syncStorage();

      return response.data;
    } finally {
      isUploading.value = false;
    }
  };

  const addVacancies = async (files: File[]) => {
    isUploading.value = true;
    try {
      const formData = new FormData();
      const rawFiles = files.map((f) => toRaw(f));
      rawFiles.forEach((f) => formData.append("files", f));

      const response = await apiClient.post("/vacancies/batch", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const results = response.data.results || [];
      const newStored: StoredFile[] = [];

      results.forEach((res: any, index: number) => {
        if (res.ok && res.id) {
          newStored.push({ id: res.id, file: rawFiles[index] });
        }
      });

      vacancyFiles.value.push(...newStored);
      batchResults.value = [];
      await syncStorage();

      return response.data;
    } finally {
      isUploading.value = false;
    }
  };

  const removeResume = async (index: number) => {
    const item = resumeFiles.value[index];
    if (!item) throw new Error("Resume not found");
    if (item.id) {
      await apiClient.delete(`/resumes/${item.id}`);
    }
    resumeFiles.value.splice(index, 1);
    batchResults.value = [];
    await syncStorage();
  };

  const removeVacancy = async (index: number) => {
    const item = vacancyFiles.value[index];
    if (!item) throw new Error("Vacancy not found");
    if (item.id) {
      await apiClient.delete(`/vacancies/${item.id}`);
    }
    vacancyFiles.value.splice(index, 1);
    batchResults.value = [];
    await syncStorage();
  };

  const clearAllResumes = async () => {
    await apiClient.delete("/resumes");
    resumeFiles.value = [];
    batchResults.value = [];
    await syncStorage();
  };

  const clearAllVacancies = async () => {
    await apiClient.delete("/vacancies");
    vacancyFiles.value = [];
    batchResults.value = [];
    await syncStorage();
  };

  const clearBatchResults = async () => {
    batchResults.value = [];
    await syncStorage();
  };

  const predictAbortController = ref<AbortController | null>(null);

  const abortPrediction = () => {
    if (predictAbortController.value) {
      predictAbortController.value.abort();
      predictAbortController.value = null;
    }
    isPredicting.value = false;
  };

  const removePredictionResult = async (
    vacancyId: number,
    resumeId: number,
  ) => {
    const batchIndex = batchResults.value.findIndex(
      (b) => b.vacancy_id === vacancyId,
    );
    if (batchIndex !== -1) {
      const batch = batchResults.value[batchIndex];
      batch.results = batch.results.filter((r) => r.resume_id !== resumeId);
      if (batch.results.length === 0) {
        batchResults.value.splice(batchIndex, 1);
      }
      await syncStorage();
    }
  };

  const runPredict = async (resumeIds: number[], vacancyIds: number[]) => {
    isPredicting.value = true;
    predictAbortController.value = new AbortController();

    try {
      if (resumeIds.length === 0 || vacancyIds.length === 0) {
        throw new Error("No files to predict");
      }

      for (const vId of vacancyIds) {
        const existingBatch = batchResults.value.find(
          (b) => b.vacancy_id === vId,
        );
        const predictedResumeIds = existingBatch
          ? existingBatch.results.map((r) => r.resume_id)
          : [];

        const resumesToRun = resumeIds.filter(
          (rId) => !predictedResumeIds.includes(rId),
        );

        if (resumesToRun.length > 0) {
          const response = await apiClient.post<BatchResponse>(
            "/predict/batch",
            {
              vacancy_id: vId,
              resume_ids: resumesToRun,
            },
            {
              signal: predictAbortController.value.signal,
            },
          );

          if (existingBatch) {
            existingBatch.results.push(...response.data.results);
          } else {
            batchResults.value.push(response.data);
          }
        }
      }

      await syncStorage();
      return batchResults.value;
    } catch (e) {
      throw e;
    } finally {
      isPredicting.value = false;
      predictAbortController.value = null;
    }
  };

  return {
    resumeFiles,
    vacancyFiles,
    isUploading,
    isPredicting,
    batchResults,
    isInitializing,
    addResumes,
    addVacancies,
    removeResume,
    removeVacancy,
    clearAllResumes,
    clearAllVacancies,
    clearBatchResults,
    removePredictionResult,
    abortPrediction,
    runPredict,
  };
});
