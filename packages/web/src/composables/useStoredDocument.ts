import { computed, ref, watch } from "vue";
import { isAxiosError } from "axios";
import { useFileStore, type StoredDocument } from "@/stores/fileStore";

type DocumentKind = "resume" | "vacancy";

export function useStoredDocument(
  docId: number,
  kind: DocumentKind,
  notFoundLabel: string,
) {
  const fileStore = useFileStore();
  const loading = ref(false);
  const loadError = ref<string | null>(null);
  const remoteDoc = ref<StoredDocument | null>(null);

  const fileObject = computed(() => {
    const list =
      kind === "resume" ? fileStore.resumeFiles : fileStore.vacancyFiles;
    const entry = list.find((item) => Number(item.id) === docId);
    const file = entry?.file;
    return file instanceof File ? file : null;
  });

  const title = computed(
    () =>
      fileObject.value?.name ||
      remoteDoc.value?.original_filename ||
      notFoundLabel,
  );

  const loadRemote = async () => {
    if (Number.isNaN(docId)) {
      loadError.value = `Invalid ${kind} id.`;
      return;
    }

    loading.value = true;
    loadError.value = null;
    remoteDoc.value = null;

    try {
      remoteDoc.value =
        kind === "resume"
          ? await fileStore.fetchResume(docId)
          : await fileStore.fetchVacancy(docId);
    } catch (e) {
      if (isAxiosError(e) && e.response?.status === 404) {
        loadError.value = `${notFoundLabel} not found on the server.`;
      } else {
        loadError.value = `Failed to load ${kind} from the server.`;
      }
    } finally {
      loading.value = false;
    }
  };

  watch(
    [() => fileStore.isInitializing, fileObject],
    ([initializing, file]) => {
      if (initializing) {
        return;
      }
      if (file) {
        loadError.value = null;
        remoteDoc.value = null;
        return;
      }
      void loadRemote();
    },
    { immediate: true },
  );

  return { fileObject, remoteDoc, loading, loadError, title };
}
