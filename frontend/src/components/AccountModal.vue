<template>
  <div v-if="modelValue" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h2 class="font-semibold text-lg">{{ editData ? 'Konto bearbeiten' : 'Neues Konto' }}</h2>
        <button type="button" @click="close" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</button>
      </div>
      <form @submit.prevent="save" class="px-6 py-4 space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Kontonummer</label>
            <input v-model="form.number" type="text" required class="input" placeholder="1020" />
          </div>
          <div>
            <label class="label">Typ</label>
            <select v-model="form.type" required class="input">
              <option v-for="t in accountTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
        </div>
        <div>
          <label class="label">Name</label>
          <input v-model="form.name" type="text" required class="input" placeholder="Kasse" />
        </div>
        <div>
          <label class="label">Währung</label>
          <select v-model="form.currency" class="input">
            <option v-for="c in currencies" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Summe in (Gruppennr.)</label>
            <input v-model="form.sum_in" type="text" class="input" placeholder="z.B. 100" list="am-group-list" />
            <datalist id="am-group-list">
              <option v-for="g in groupAccounts" :key="g.number" :value="g.number">{{ g.number }} {{ g.name }}</option>
            </datalist>
          </div>
          <div>
            <label class="label">IBAN</label>
            <input v-model="form.iban" type="text" class="input" placeholder="CH56 0483 5012 3456 7800 9" />
          </div>
        </div>
        <div class="flex gap-6">
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="form.is_group" type="checkbox" class="w-4 h-4 accent-indigo-600" />
            <span class="text-sm">Sammelkonto (keine Buchungen)</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="form.active" type="checkbox" class="w-4 h-4 accent-indigo-600" />
            <span class="text-sm">Aktiv</span>
          </label>
        </div>
        <div v-if="formError" class="text-red-500 text-sm">{{ formError }}</div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" @click="close" class="btn-secondary">Abbrechen</button>
          <button type="submit" :disabled="saving" class="btn-primary">{{ saving ? 'Speichern…' : 'Speichern' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { apiFetch } from '../api.js'

const props = defineProps({
  modelValue: Boolean,
  accounts: { type: Array, default: () => [] },
  editData: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const saving = ref(false)
const formError = ref(null)

const currencies = ['CHF', 'EUR', 'USD', 'GBP']
const accountTypes = [
  { value: 'asset',     label: 'Aktiva' },
  { value: 'liability', label: 'Passiva' },
  { value: 'equity',    label: 'Eigenkapital' },
  { value: 'income',    label: 'Ertrag' },
  { value: 'expense',   label: 'Aufwand' },
]

const groupAccounts = computed(() => props.accounts.filter(a => a.is_group))

const emptyForm = () => ({ number: '', name: '', type: 'expense', currency: 'CHF', sum_in: '', iban: '', is_group: false, active: true })
const form = ref(emptyForm())

watch(() => props.modelValue, (open) => {
  if (!open) return
  formError.value = null
  form.value = props.editData
    ? { ...props.editData, iban: props.editData.iban ?? '', sum_in: props.editData.sum_in ?? '' }
    : emptyForm()
})

function close() { emit('update:modelValue', false) }

async function save() {
  saving.value = true
  formError.value = null
  try {
    const body = { ...form.value, iban: form.value.iban || null, sum_in: form.value.sum_in || null }
    const url = props.editData ? `/api/accounts/${props.editData.id}` : '/api/accounts'
    const method = props.editData ? 'PUT' : 'POST'
    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!res.ok) { const d = await res.json().catch(() => ({})); formError.value = d.detail ?? 'Fehler beim Speichern.'; return }
    const saved = await res.json()
    emit('saved', saved)
    close()
  } finally { saving.value = false }
}
</script>

<style scoped>
.label { @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1; }
.input { @apply w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500; }
.btn-primary { @apply px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
.btn-secondary { @apply px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors; }
</style>
