<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center gap-3 flex-wrap">
      <RouterLink to="/konten" class="text-sm text-gray-400 hover:text-indigo-500 transition-colors">← Konten</RouterLink>
      <div class="flex items-center gap-2 flex-1">
        <span class="font-mono text-sm text-gray-400">{{ account?.number }}</span>
        <h1 class="text-2xl font-semibold">{{ account?.name }}</h1>
        <span v-if="account" class="px-2 py-0.5 rounded-full text-xs font-medium" :class="typeClass(account.type)">
          {{ typeLabel(account.type) }}
        </span>
      </div>
      <select v-model.number="selectedYear"
        class="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        <option value="">Alle Jahre</option>
        <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
      </select>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-3 gap-3">
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-3">
        <div class="text-xs text-gray-400 uppercase tracking-wide mb-1">Soll</div>
        <div class="font-mono font-semibold text-gray-800 dark:text-gray-200">{{ fmt(totalDebit) }}</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-3">
        <div class="text-xs text-gray-400 uppercase tracking-wide mb-1">Haben</div>
        <div class="font-mono font-semibold text-gray-800 dark:text-gray-200">{{ fmt(totalCredit) }}</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-3">
        <div class="text-xs text-gray-400 uppercase tracking-wide mb-1">Saldo (Soll − Haben)</div>
        <div class="font-mono font-semibold" :class="netBalance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
          {{ fmt(netBalance) }}
        </div>
      </div>
    </div>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
      {{ error }}
    </div>

    <!-- Ledger table -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wide">
            <th class="text-left px-3 py-2.5 w-24 border-b border-gray-200 dark:border-gray-700">Datum</th>
            <th class="text-left px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Beschreibung</th>
            <th class="text-left px-3 py-2.5 w-40 border-b border-gray-200 dark:border-gray-700">Gegenkonto</th>
            <th class="text-right px-3 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Soll</th>
            <th class="text-right px-3 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Haben</th>
            <th class="text-right px-3 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Saldo</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="text-center py-10 text-gray-400 text-sm">Wird geladen…</td>
          </tr>
          <tr v-else-if="rows.length === 0">
            <td colspan="6" class="text-center py-10 text-gray-400 text-sm">Keine Buchungen</td>
          </tr>
          <tr v-for="row in rows" :key="row.id"
            class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/20">
            <td class="px-3 py-2 font-mono text-xs text-gray-500 dark:text-gray-400">{{ fmtDate(row.date) }}</td>
            <td class="px-3 py-2 text-xs text-gray-700 dark:text-gray-300">
              <div>{{ row.description || row.reference || '—' }}</div>
              <div v-if="row.counterparty" class="text-gray-400">{{ row.counterparty }}</div>
            </td>
            <td class="px-3 py-2 text-xs text-gray-500 dark:text-gray-400">
              <span v-if="row.debit_account_id === accountId">
                <span class="font-mono text-gray-400">{{ row.credit_account?.number }}</span> {{ row.credit_account?.name }}
              </span>
              <span v-else>
                <span class="font-mono text-gray-400">{{ row.debit_account?.number }}</span> {{ row.debit_account?.name }}
              </span>
            </td>
            <td class="px-3 py-2 text-right font-mono text-xs">
              <span v-if="row.debit_account_id === accountId" class="text-gray-800 dark:text-gray-200">{{ fmt(row.amount) }}</span>
              <span v-else class="text-gray-300 dark:text-gray-600">—</span>
            </td>
            <td class="px-3 py-2 text-right font-mono text-xs">
              <span v-if="row.credit_account_id === accountId" class="text-gray-800 dark:text-gray-200">{{ fmt(row.amount) }}</span>
              <span v-else class="text-gray-300 dark:text-gray-600">—</span>
            </td>
            <td class="px-3 py-2 text-right font-mono text-xs font-medium"
              :class="row.runningBalance >= 0 ? 'text-gray-700 dark:text-gray-300' : 'text-red-600 dark:text-red-400'">
              {{ fmt(row.runningBalance) }}
            </td>
          </tr>
        </tbody>
        <tfoot v-if="rows.length > 0">
          <tr class="bg-gray-50 dark:bg-gray-700/50 font-semibold text-sm">
            <td colspan="3" class="px-3 py-2.5 text-gray-500 dark:text-gray-400 text-xs uppercase tracking-wide">Total</td>
            <td class="px-3 py-2.5 text-right font-mono text-gray-800 dark:text-gray-200">{{ fmt(totalDebit) }}</td>
            <td class="px-3 py-2.5 text-right font-mono text-gray-800 dark:text-gray-200">{{ fmt(totalCredit) }}</td>
            <td class="px-3 py-2.5 text-right font-mono" :class="netBalance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ fmt(netBalance) }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { apiFetch } from '../api.js'

const route = useRoute()
const accountId = computed(() => parseInt(route.params.id))

const account = ref(null)
const transactions = ref([])
const selectedYear = ref(new Date().getFullYear())
const loading = ref(false)
const error = ref(null)

const availableYears = computed(() => {
  const years = new Set(transactions.value.map(t => parseInt(t.date.slice(0, 4))))
  years.add(new Date().getFullYear())
  return [...years].sort((a, b) => b - a)
})

const rows = computed(() => {
  let balance = 0
  return transactions.value.map(t => {
    const amt = parseFloat(t.amount)
    if (t.debit_account_id === accountId.value) balance += amt
    else balance -= amt
    return { ...t, runningBalance: balance }
  })
})

const totalDebit = computed(() =>
  transactions.value.filter(t => t.debit_account_id === accountId.value)
    .reduce((s, t) => s + parseFloat(t.amount), 0)
)
const totalCredit = computed(() =>
  transactions.value.filter(t => t.credit_account_id === accountId.value)
    .reduce((s, t) => s + parseFloat(t.amount), 0)
)
const netBalance = computed(() => totalDebit.value - totalCredit.value)

const accountTypes = {
  asset: 'Aktiva', liability: 'Passiva', equity: 'Eigenkapital',
  income: 'Ertrag', expense: 'Aufwand',
}
const typeLabel = (t) => accountTypes[t] ?? t
const typeClass = (t) => ({
  asset:     'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  liability: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  equity:    'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  income:    'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  expense:   'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
}[t] ?? '')

const fmt = (val) =>
  new Intl.NumberFormat('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val || 0)

const fmtDate = (d) => {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${(day ?? '').padStart(2, '0')}.${(m ?? '').padStart(2, '0')}.${y}`
}

async function loadTransactions() {
  loading.value = true
  error.value = null
  try {
    const year = selectedYear.value ? `?year=${selectedYear.value}` : ''
    const res = await apiFetch(`/api/accounts/${accountId.value}/transactions${year}`)
    if (!res.ok) throw new Error()
    transactions.value = await res.json()
  } catch {
    error.value = 'Buchungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function loadAccount() {
  try {
    const res = await apiFetch(`/api/accounts/${accountId.value}`)
    if (res.ok) account.value = await res.json()
  } catch { /* silent */ }
}

watch(selectedYear, loadTransactions)
watch(accountId, () => { loadAccount(); loadTransactions() })
onMounted(() => { loadAccount(); loadTransactions() })
</script>
