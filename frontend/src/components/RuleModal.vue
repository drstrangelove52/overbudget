<template>
  <div v-if="modelValue" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-xl">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h2 class="font-semibold text-lg">{{ editData ? 'Regel bearbeiten' : 'Neue Regel' }}</h2>
        <button type="button" @click="close" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</button>
      </div>
      <form @submit.prevent="save" class="px-6 py-4 space-y-4">

        <div>
          <label class="label">Name</label>
          <input v-model="form.name" type="text" required class="input" placeholder="z.B. Tankstelle klein → Smart" />
        </div>

        <!-- Conditions -->
        <div>
          <label class="label">Bedingungen</label>
          <div class="space-y-2">
            <div v-for="(cond, i) in form.conditions" :key="i" class="flex gap-2 items-center">
              <!-- Prefix: "Wenn" or AND/OR chip -->
              <div class="w-14 flex-shrink-0 text-right">
                <span v-if="i === 0" class="text-xs text-gray-400 font-medium">Wenn</span>
                <button v-else type="button" @click="toggleLogic"
                  class="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 hover:opacity-75 transition-opacity cursor-pointer">
                  {{ form.condition_logic === 'and' ? 'UND' : 'ODER' }}
                </button>
              </div>

              <select v-model="cond.field" @change="onFieldChange(cond)" class="input w-36 flex-shrink-0">
                <option value="description">Beschreibung</option>
                <option value="counterparty">Gegenpartei</option>
                <option value="amount">Betrag (CHF)</option>
              </select>

              <select v-model="cond.operator" class="input w-32 flex-shrink-0">
                <template v-if="cond.field === 'amount'">
                  <option value="lt">kleiner als</option>
                  <option value="gt">grösser als</option>
                  <option value="equals">gleich</option>
                </template>
                <template v-else>
                  <option value="contains">enthält</option>
                  <option value="equals">gleich</option>
                  <option value="regex">Regex</option>
                </template>
              </select>

              <input v-model="cond.value" type="text" class="input flex-1 min-w-0"
                :placeholder="cond.field === 'amount' ? '50' : 'z.B. Migros'" />

              <button v-if="form.conditions.length > 1" type="button" @click="removeCond(i)"
                class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 text-lg leading-none">×</button>
            </div>
          </div>
          <button type="button" @click="addCond"
            class="mt-2 text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
            + Bedingung hinzufügen
          </button>
        </div>

        <!-- Accounts -->
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
  name: '',
  priority: 0,
  active: true,
  condition_logic: 'and',
  conditions: [{ field: 'description', operator: 'contains', value: '' }],
  debit_account_id: null,
  credit_account_id: null,
  auto_confirm: false,
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
      condition_logic: props.editData.condition_logic,
      conditions: props.editData.conditions.map(c => ({ field: c.field, operator: c.operator, value: c.value })),
      debit_account_id: props.editData.debit_account_id,
      credit_account_id: props.editData.credit_account_id,
      auto_confirm: props.editData.auto_confirm,
    }
  } else {
    const base = emptyForm()
    if (props.prefill?.conditions) {
      base.conditions = props.prefill.conditions
    }
    form.value = base
  }
})

function addCond() {
  form.value.conditions.push({ field: 'description', operator: 'contains', value: '' })
}

function removeCond(i) {
  form.value.conditions.splice(i, 1)
}

function toggleLogic() {
  form.value.condition_logic = form.value.condition_logic === 'and' ? 'or' : 'and'
}

function onFieldChange(cond) {
  if (cond.field === 'amount') {
    if (!['lt', 'gt', 'equals'].includes(cond.operator)) cond.operator = 'lt'
  } else {
    if (!['contains', 'equals', 'regex'].includes(cond.operator)) cond.operator = 'contains'
  }
}

function close() { emit('update:modelValue', false) }

async function save() {
  formError.value = null
  if (!form.value.conditions.length) {
    formError.value = 'Mindestens eine Bedingung erforderlich.'
    return
  }
  if (form.value.conditions.some(c => !c.value.trim())) {
    formError.value = 'Alle Bedingungswerte ausfüllen.'
    return
  }
  saving.value = true
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
