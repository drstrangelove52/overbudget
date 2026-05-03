<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Budgets</h1>
      <button @click="openCreate" class="btn-primary text-sm">+ Neues Budget</button>
    </div>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
      {{ error }}
    </div>

    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wide">
            <th class="text-left px-4 py-2.5 border-b border-gray-200 dark:border-gray-700">Konto</th>
            <th class="text-left px-4 py-2.5 border-b border-gray-200 dark:border-gray-700">Bezeichnung</th>
            <th class="text-center px-4 py-2.5 w-24 border-b border-gray-200 dark:border-gray-700">Zeitraum</th>
            <th class="text-right px-4 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Budget</th>
            <th class="text-right px-4 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Aktuell</th>
            <th class="text-right px-4 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Differenz</th>
            <th class="px-4 py-2.5 w-40 border-b border-gray-200 dark:border-gray-700"></th>
            <th class="w-24 border-b border-gray-200 dark:border-gray-700"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="budgets.length === 0">
            <td colspan="8" class="text-center py-10 text-gray-400 text-sm">Noch keine Budgets vorhanden</td>
          </tr>
          <tr
            v-for="b in budgetsWithActual" :key="b.id"
            class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/20"
            :class="!b.active ? 'opacity-50' : ''"
          >
            <td class="px-4 py-2.5 text-xs">
              <span class="font-mono text-gray-400 dark:text-gray-500 mr-1">{{ b.account.number }}</span>
              <span class="text-gray-600 dark:text-gray-300">{{ b.account.name }}</span>
            </td>
            <td class="px-4 py-2.5 text-gray-700 dark:text-gray-300">{{ b.name }}</td>
            <td class="px-4 py-2.5 text-center">
              <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                :class="b.period === 'monthly'
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'">
                {{ b.period === 'monthly' ? 'Monat' : 'Jahr' }}
              </span>
            </td>
            <td class="px-4 py-2.5 text-right font-mono text-gray-700 dark:text-gray-300">{{ fmt(b.amount) }}</td>
            <td class="px-4 py-2.5 text-right font-mono"
              :class="b.actual > parseFloat(b.amount) ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300'">
              {{ fmt(b.actual) }}
            </td>
            <td class="px-4 py-2.5 text-right font-mono"
              :class="b.diff >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ fmt(b.diff) }}
            </td>
            <td class="px-4 py-2.5">
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <div
                  class="h-2 rounded-full transition-all"
                  :class="b.pct > 100 ? 'bg-red-500' : b.pct > 80 ? 'bg-yellow-400' : 'bg-green-500'"
                  :style="{ width: Math.min(b.pct, 100) + '%' }"
                ></div>
              </div>
              <div class="text-right text-xs text-gray-400 mt-0.5">{{ Math.round(b.pct) }}%</div>
            </td>
            <td class="px-4 py-2.5 text-right whitespace-nowrap">
              <button @click="openEdit(b)" class="text-gray-400 hover:text-indigo-500 mr-3 text-xs transition-colors">Bearb.</button>
              <button @click="confirmDelete(b)" class="text-gray-400 hover:text-red-500 text-xs transition-colors">Löschen</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="closeModal">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 class="font-semibold text-lg">{{ modal === 'create' ? 'Neues Budget' : 'Budget bearbeiten' }}</h2>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        <form @submit.prevent="save" class="px-6 py-4 space-y-4">
          <div>
            <label class="label">Konto</label>
            <select v-model.number="form.account_id" required class="input">
              <option :value="null" disabled>— Konto wählen —</option>
              <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">Bezeichnung</label>
            <input v-model="form.name" type="text" required class="input" placeholder="z.B. Lebensmittel" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Zeitraum</label>
              <select v-model="form.period" required class="input">
                <option value="monthly">Monatlich</option>
                <option value="yearly">Jährlich</option>
              </select>
            </div>
            <div>
              <label class="label">Betrag</label>
              <input v-model.number="form.amount" type="number" step="0.01" min="0.01" required class="input" placeholder="500.00" />
            </div>
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="form.active" type="checkbox" class="w-4 h-4 accent-indigo-600" />
            <span class="text-sm">Aktiv</span>
          </label>
          <div v-if="formError" class="text-red-500 text-sm">{{ formError }}</div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="closeModal" class="btn-secondary">Abbrechen</button>
            <button type="submit" :disabled="saving" class="btn-primary">{{ saving ? 'Speichern…' : 'Speichern' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="deleteTarget = null">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 class="font-semibold text-lg">Budget löschen?</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400"><strong>{{ deleteTarget.name }}</strong> wird gelöscht.</p>
        <div v-if="deleteError" class="text-red-500 text-sm">{{ deleteError }}</div>
        <div class="flex justify-end gap-3">
          <button @click="deleteTarget = null" class="btn-secondary">Abbrechen</button>
          <button @click="doDelete" :disabled="saving" class="btn-danger">{{ saving ? 'Löschen…' : 'Löschen' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetch } from '../api.js'

const budgets = ref([])
const accounts = ref([])
const transactions = ref([])
const error = ref(null)
const modal = ref(null)
const saving = ref(false)
const formError = ref(null)
const deleteTarget = ref(null)
const deleteError = ref(null)
const editId = ref(null)

const fmt = (val) =>
  new Intl.NumberFormat('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parseFloat(val) || 0)

const bookableAccounts = computed(() =>
  [...accounts.value]
    .filter(a => !a.is_group && a.active)
    .sort((a, b) => a.number.localeCompare(b.number))
)

const now = new Date()
const currentYearMonth = now.toISOString().slice(0, 7)
const currentYear = now.toISOString().slice(0, 4)

function actualForBudget(b) {
  const acc = accounts.value.find(a => a.id === b.account_id)
  if (!acc) return 0
  const prefix = b.period === 'monthly' ? currentYearMonth : currentYear
  let raw = 0
  for (const t of transactions.value) {
    if (!t.date.startsWith(prefix)) continue
    const amt = parseFloat(t.amount) || 0
    if (t.debit_account_id  === acc.id) raw += amt
    if (t.credit_account_id === acc.id) raw -= amt
  }
  return ['asset', 'expense'].includes(acc.type) ? raw : -raw
}

const budgetsWithActual = computed(() =>
  budgets.value.map(b => {
    const actual = actualForBudget(b)
    const budget = parseFloat(b.amount) || 0
    const diff = budget - actual
    const pct = budget > 0 ? (actual / budget) * 100 : 0
    return { ...b, actual, diff, pct }
  })
)

const emptyForm = () => ({ account_id: null, name: '', amount: '', period: 'monthly', active: true })
const form = ref(emptyForm())

async function load() {
  try {
    const [bRes, aRes, tRes] = await Promise.all([
      apiFetch('/api/budgets'),
      apiFetch('/api/accounts'),
      apiFetch('/api/transactions'),
    ])
    if (!bRes.ok || !aRes.ok || !tRes.ok) throw new Error()
    budgets.value = await bRes.json()
    accounts.value = await aRes.json()
    transactions.value = await tRes.json()
    error.value = null
  } catch {
    error.value = 'Daten konnten nicht geladen werden.'
  }
}

function openCreate() { editId.value = null; form.value = emptyForm(); formError.value = null; modal.value = 'create' }
function openEdit(b) {
  editId.value = b.id
  form.value = { account_id: b.account_id, name: b.name, amount: b.amount, period: b.period, active: b.active }
  formError.value = null; modal.value = 'edit'
}
function closeModal() { modal.value = null }

async function save() {
  saving.value = true; formError.value = null
  try {
    const url = modal.value === 'create' ? '/api/budgets' : `/api/budgets/${editId.value}`
    const res = await apiFetch(url, { method: modal.value === 'create' ? 'POST' : 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form.value) })
    if (!res.ok) { const d = await res.json().catch(() => ({})); formError.value = d.detail ?? 'Fehler.'; return }
    await load(); closeModal()
  } finally { saving.value = false }
}

function confirmDelete(b) { deleteTarget.value = b; deleteError.value = null }
async function doDelete() {
  saving.value = true; deleteError.value = null
  try {
    const res = await apiFetch(`/api/budgets/${deleteTarget.value.id}`, { method: 'DELETE' })
    if (!res.ok) { const d = await res.json().catch(() => ({})); deleteError.value = d.detail ?? 'Fehler.'; return }
    await load(); deleteTarget.value = null
  } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.label { @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1; }
.input { @apply w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500; }
.btn-primary { @apply px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
.btn-secondary { @apply px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors; }
.btn-danger { @apply px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
</style>
