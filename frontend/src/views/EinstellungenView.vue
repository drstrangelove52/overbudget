<template>
  <div class="space-y-6 max-w-lg">
    <h1 class="text-2xl font-semibold">Einstellungen</h1>

    <!-- Backup -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      <h2 class="font-semibold text-lg">Backup</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Erstellt einen vollständigen Datenbank-Dump, verschlüsselt mit AES-256 (GPG).
      </p>
      <div v-if="backupError" class="text-red-500 text-sm">{{ backupError }}</div>
      <button @click="downloadBackup" :disabled="backupLoading" class="btn-primary">
        {{ backupLoading ? 'Wird erstellt…' : 'Backup herunterladen' }}
      </button>
    </div>

    <!-- Restore -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      <h2 class="font-semibold text-lg">Restore</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Stellt die Datenbank aus einer verschlüsselten Backup-Datei wieder her.
        <strong class="text-red-500">Alle aktuellen Daten werden überschrieben.</strong>
      </p>
      <div v-if="!restoreConfirm">
        <input ref="restoreInput" type="file" accept=".gpg" class="hidden" @change="onRestoreFile" />
        <button @click="restoreInput.click()" class="btn-danger">Backup-Datei auswählen…</button>
      </div>
      <div v-else class="space-y-3">
        <div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
          Datei: <strong>{{ restoreFile.name }}</strong><br>
          Wirklich alle Daten überschreiben?
        </div>
        <div v-if="restoreError" class="text-red-500 text-sm">{{ restoreError }}</div>
        <div class="flex gap-3">
          <button @click="restoreConfirm = false; restoreFile = null" class="btn-secondary">Abbrechen</button>
          <button @click="doRestore" :disabled="restoreLoading" class="btn-danger">
            {{ restoreLoading ? 'Wird wiederhergestellt…' : 'Jetzt wiederherstellen' }}
          </button>
        </div>
      </div>
      <div v-if="restoreSuccess" class="text-green-600 dark:text-green-400 text-sm font-medium">
        Restore erfolgreich. Bitte Seite neu laden.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch } from '../api.js'

const backupLoading = ref(false)
const backupError = ref(null)

const restoreInput = ref(null)
const restoreFile = ref(null)
const restoreConfirm = ref(false)
const restoreLoading = ref(false)
const restoreError = ref(null)
const restoreSuccess = ref(false)

async function downloadBackup() {
  backupLoading.value = true
  backupError.value = null
  try {
    const res = await apiFetch('/api/backup')
    if (!res.ok) {
      const d = await res.json().catch(() => ({}))
      backupError.value = d.detail ?? 'Backup fehlgeschlagen.'
      return
    }
    const blob = await res.blob()
    const cd = res.headers.get('Content-Disposition') ?? ''
    const match = cd.match(/filename="(.+?)"/)
    const filename = match ? match[1] : 'overbudget-backup.sql.gpg'
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  } catch {
    backupError.value = 'Netzwerkfehler.'
  } finally {
    backupLoading.value = false
  }
}

function onRestoreFile(e) {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return
  restoreFile.value = file
  restoreConfirm.value = true
  restoreError.value = null
  restoreSuccess.value = false
}

async function doRestore() {
  restoreLoading.value = true
  restoreError.value = null
  try {
    const form = new FormData()
    form.append('file', restoreFile.value)
    const res = await apiFetch('/api/backup/restore', { method: 'POST', body: form })
    const d = await res.json().catch(() => ({}))
    if (!res.ok) { restoreError.value = d.detail ?? 'Restore fehlgeschlagen.'; return }
    restoreSuccess.value = true
    restoreConfirm.value = false
    restoreFile.value = null
  } catch {
    restoreError.value = 'Netzwerkfehler.'
  } finally {
    restoreLoading.value = false
  }
}
</script>

<style scoped>
.btn-primary { @apply px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
.btn-secondary { @apply px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors; }
.btn-danger { @apply px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
</style>
