<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">Sign In</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.email"
            placeholder="Email"
            type="email"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.password"
            placeholder="Password"
            type="password"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            class="submit-btn"
            :loading="isLoading"
          >
            Log In
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage } from "element-plus";

const router = useRouter();
const authStore = useAuthStore();
const isLoading = ref(false);

const form = reactive({
  email: "",
  password: "",
});

const handleLogin = async () => {
  if (!form.email || !form.password) {
    ElMessage.warning("Please fill in both fields");
    return;
  }

  isLoading.value = true;

  await new Promise((resolve) => setTimeout(resolve, 500));

  authStore.login(form.email);

  ElMessage.success("Login successful");
  isLoading.value = false;

  router.push("/");
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f3f4f6;
}
.login-card {
  width: 100%;
  max-width: 400px;
}
.login-title {
  text-align: center;
  margin-bottom: 20px;
}
.submit-btn {
  width: 100%;
}
</style>
