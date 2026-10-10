<template>
  <main class="auth-view">
    <section class="auth-view__panel">
      <div class="auth-view__brand">磨小二</div>
      <h1>{{ registering ? '创建老板账号' : '登录工作台' }}</h1>
      <p>{{ registering ? '注册仅创建老板账号，员工账号由老板在工作台内创建。' : '使用用户名和密码登录。' }}</p>
      <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" show-icon />
      <el-form :model="form" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名" :error="fieldErrors.username">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item v-if="registering" label="找回密码邮箱" :error="fieldErrors.email">
          <el-input v-model="form.email" type="email" autocomplete="email" />
        </el-form-item>
        <el-form-item label="密码" :error="fieldErrors.password">
          <el-input v-model="form.password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-button class="auth-view__submit" type="primary" native-type="submit" :loading="submitting">
          {{ registering ? '注册并登录' : '登录' }}
        </el-button>
      </el-form>
      <el-button text @click="registering = !registering">
        {{ registering ? '已有账号，去登录' : '新店铺注册老板账号' }}
      </el-button>
      <el-button v-if="!registering" text @click="router.push('/reset-password')">忘记密码</el-button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError, V1Service } from '../../api/generated'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const registering = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const fieldErrors = reactive<Record<string, string>>({})
const form = reactive({ username: '', email: '', password: '' })

function displayError(error: unknown) {
  errorMessage.value = '请求未完成，请检查输入后重试。'
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  if (error instanceof ApiError && error.body && typeof error.body === 'object') {
    const body = error.body as { message?: string; errors?: Record<string, string[]> }
    const errors = body.errors ?? {}
    Object.entries(errors).forEach(([field, messages]) => {
      fieldErrors[field] = messages.join(' ')
    })
    errorMessage.value = Object.keys(errors).length === 0 ? body.message ?? errorMessage.value : ''
  }
}

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    if (registering.value) await V1Service.v1AuthRegisterCreate({ ...form })
    await auth.login(form.username, form.password)
    await router.replace('/')
  } catch (error) {
    displayError(error)
  } finally {
    submitting.value = false
  }
}
</script>