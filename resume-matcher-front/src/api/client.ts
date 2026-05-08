import axios from "axios";

const baseURL = window.__ENV__?.VITE_API_URL || import.meta.env.VITE_API_URL;

const apiClient = axios.create({
  baseURL: baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

export default apiClient;
