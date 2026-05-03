<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 w-full max-w-sm space-y-6">
      <div class="text-center">
        <h1 class="text-2xl font-bold text-indigo-600 dark:text-indigo-400 tracking-tight">OverBudget</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Bitte anmelden</p>
      </div>
      <form @submit.prevent="login" class="space-y-4">
        <div>
          <label class="label">Benutzername</label>
          <input
            v-model="username" type="text" class="input"
            autocomplete="username" required autofocus
          />
        </div>
        <div>
          <label class="label">Passwort</label>
          <input
            v-model="password" type="password" class="input"
            autocomplete="current-password" required
          />
        </div>
        <div v-if="error" class="text-red-500 text-sm text-center">{{ error }}</div>
        <button type="submit" :disabled="loading" class="w-full btn-primary py-2.5">
          {{ loading ? 'Anmelden…' : 'Anmelden' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { setToken } from '../api.js'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref(null)
const loading = ref(false)

async function login() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) { error.value = data.detail ?? 'Anmeldung fehlgeschlagen.'; return }
    setToken(data.access_token)
    router.push('/')
  } catch {
    error.value = 'Netzwerkfehler.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.label { @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1; }
.input { @apply w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500; }
.btn-primary { @apply px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
</style>
