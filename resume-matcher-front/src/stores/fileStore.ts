import { defineStore } from "pinia";
import { ref } from "vue";
import apiClient from "@/api/client";

export const useFileStore = defineStore("files", () => {
  const resumeFile = ref<File | null>(null);
  const vacancyFile = ref<File | null>(null);
  const isPredicting = ref(false);

  const setResume = (file: File) => (resumeFile.value = file);
  const setVacancy = (file: File) => (vacancyFile.value = file);

  const clearResume = () => (resumeFile.value = null);
  const clearVacancy = () => (vacancyFile.value = null);

  const runPredict = async () => {
    if (!resumeFile.value || !vacancyFile.value) return;

    isPredicting.value = true;
    const formData = new FormData();
    formData.append("resume", resumeFile.value);
    formData.append("vacancy", vacancyFile.value);

    try {
      const response = await apiClient.post("/predict", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return response.data;
    } finally {
      isPredicting.value = false;
    }
  };

  return {
    resumeFile,
    vacancyFile,
    isPredicting,
    setResume,
    setVacancy,
    clearResume,
    clearVacancy,
    runPredict,
  };
});
