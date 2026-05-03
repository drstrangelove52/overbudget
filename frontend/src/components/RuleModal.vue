<template>
  <div v-if="modelValue" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h2 class="font-semibold text-lg">{{ editData ? 'Regel bearbeiten' : 'Neue Regel' }}</h2>
        <button type="button" @click="close" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</button>
      </div>
      <form @submit.prevent="save" class="px-6 py-4 space-y-4">
        <div>
          <label class="label">Name</label>
          <input v-model="form.name" type="text" required class="input" placeholder="z.B. Migros → Nahrungsmittel" />
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="label">Feld</label>
            <select v-model="form.condition_field" required class="input">
              <option value="description">Beschreibung</option>
              <option value="counterparty">Gegenseite</option>
              <option value="amount">Betrag</option>
            </select>
          </div>
          <div>
            <label class="label">Operator</label>
            <select v-model="form.condition_operator" required class="input">
              <option value="contains">enthält</option>
              <option value="equals">gleich</option>
              <option value="lt">kleiner als</option>
              <option value="gt">grösser als</option>
              <option value="regex">Regex</option>
            </select>
          </div>
          <div>
            <label class="label">Wert</label>
            <input v-model="form.condition_value" type="text" required class="input" placeholder="Migros" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Sollkonto (optional)</label>
            <select v-model="form.debit_account_id" class="input">
              <option :value="null">— kein —</option>
              <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">Habenkonto (optional)</label>
            <select v-model="form.credit_account_id" class="input">
              <option :value="null">— kein —</option>
              <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Priorität</label>
            <input v-model.number="form.priority" type="number" class="input" placeholder="0" />
          </div>
        </div>
        <div class="flex gap-6">
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="form.active" type="checkbox" class="w-4 h-4 accent-indigo-600" />
            <span class="text-sm">Aktiv</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="form.auto_confirm" type="checkbox" class="w-4 h-4 accent-indigo-600" />
            <span class="text-sm">Automatisch buchen</span>
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
  prefill: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const saving = ref(false)
const formError = ref(null)

const bookableAccounts = computed(() =>
  [...props.accounts]
    .filter(a => !a.is_group && a.active)
    .sort((a, b) => a.number.localeCompare(b.number))
)

const emptyForm = () => ({
  name: '', priority: 0, active: true,
  condition_field: 'description', condition_operator: 'contains', condition_value: '',
  debit_account_id: null, credit_account_id: null, auto_confirm: false,
})

const form = ref(emptyForm())

watch(() => props.modelValue, (open) => {
  if (!open) return
  formError.value = null
  if (props.editData) {
    form.value = {
      name: props.editData.name,
      priority: props.editData.priority,
      active: props.editData.active,
      condition_field: props.editData.condition_field,
      condition_operator: props.editData.condition_operator,
      condition_value: props.editData.condition_value,
      debit_account_id: props.editData.debit_account_id,
      credit_account_id: props.editData.credit_account_id,
      auto_confirm: props.editData.auto_confirm,
    }
  } else {
    const base = emptyForm()
    if (props.prefill) Object.assign(base, props.prefill)
    form.value = base
  }
})

function close() { emit('update:modelValue', false) }

async function save() {
  saving.value = true
  formError.value = null
  try {
    const url = props.editData ? `/api/rules/${props.editData.id}` : '/api/rules'
    const method = props.editData ? 'PUT' : 'POST'
    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form.value) })
    if (!res.ok) { const d = await res.json().catch(() => ({})); formError.value = d.detail ?? 'Fehler.'; return }
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
