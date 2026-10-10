<template>
  <main class="auth-view">
    <section class="auth-view__panel">
      <div class="auth-view__brand">磨小二</div>
      <h1>重置密码</h1>
      <p v-if="!isConfirmation">输入已绑定邮箱后，系统会发送重置链接。</p>
      <p v-else>设置新的登录密码。</p>
      <el-alert v-if="message" :type="isError ? 'error' : 'success'" :title="message" :closable="false" show-icon />
      <el-form @submit.prevent="submit">
        <el-form-item v-if="!isConfirmation" label="邮箱"><el-input v-model="email" type="email" autocomplete="email" /></el-form-item>
        <el-form-item v-else label="新密码"><el-input v-model="password" type="password" show-password autocomplete="new-password" /></el-form-item>
        <el-button class="auth-view__submit" type="primary" native-type="submit" :loading="submitting">{{ isConfirmation ? '保存新密码' : '发送重置链接' }}</el-button>
      </el-form>
      <el-button text @click="router.push('/auth')">返回登录</el-button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { confirmPasswordReset, requestPasswordReset } from '../../api/account'

const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const message = ref('')
const isError = ref(false)
const submitting = ref(false)
const uid = computed(() => typeof route.query.uid === 'string' ? route.query.uid : '')
const token = computed(() => typeof route.query.token === 'string' ? route.query.token : '')
const isConfirmation = computed(() => Boolean(uid.value && token.value))

async function submit() {
  submitting.value = true
  message.value = ''
  try {
    if (isConfirmation.value) {
      await confirmPasswordReset(uid.value, token.value, password.value)
      message.value = '密码已更新，请使用新密码登录。'
    } else {
      await requestPasswordReset(email.value)
      message.value = '如该邮箱已绑定账号，重置链接已发送。'
    }
    isError.value = false
  } catch {
    isError.value = true
    message.value = '请求未完成，请检查输入后重试。'
  } finally {
    submitting.value = false
  }
}
</script>