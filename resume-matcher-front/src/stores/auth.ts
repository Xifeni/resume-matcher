import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const email = ref(localStorage.getItem('user_email') || null)

  const isAuthenticated = computed(() => !!email.value)

  const login = (newEmail: string) => {
    email.value = newEmail
    localStorage.setItem('user_email', newEmail)
  }

  const logout = () => {
    email.value = null
    localStorage.removeItem('user_email')
  }

  return { email, isAuthenticated, login, logout }
})
