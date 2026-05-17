import { createApp } from "vue";
import Vue3Toastify, { type ToastContainerOptions } from "vue3-toastify";
import router from "./router";
import ElementPlus from "element-plus";
import { createPinia } from "pinia";
import "./styles/index.css";

import "vue3-toastify/dist/index.css";
import "element-plus/dist/index.css";

import App from "./App.vue";

createApp(App)
  .use(router)
  .use(ElementPlus)
  .use(createPinia())
  .use(Vue3Toastify, {
    autoClose: 3000,
  } as ToastContainerOptions)
  .mount("#app");
