import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import LoginView from "@/views/LoginView.vue";
import MainView from "@/views/MainView.vue";
import ResumeView from "@/views/ResumeView.vue";
import VacancyView from "@/views/VacancyView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { requiresGuest: true },
    },
    {
      path: "/",
      name: "home",
      component: MainView,
      meta: { requiresAuth: true },
    },
    {
      path: "/resumes/:id",
      name: "resume-view",
      component: ResumeView,
      meta: { requiresAuth: true },
    },
    {
      path: "/vacancies/:id",
      name: "vacancy-view",
      component: VacancyView,
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: "login" });
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: "home" });
  } else {
    next();
  }
});

export default router;
