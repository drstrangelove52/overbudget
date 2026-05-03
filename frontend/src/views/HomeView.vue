<template>
  <div class="space-y-6">
    <div v-if="error" class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
      {{ error }}
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-5 py-4">
        <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Nettovermögen</div>
        <div class="text-2xl font-bold font-mono" :class="nettovermoegen >= 0 ? 'text-blue-700 dark:text-blue-300' : 'text-red-600 dark:text-red-400'">
          {{ fmt(nettovermoegen) }}
        </div>
        <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">Aktiven − Fremdkapital</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-5 py-4">
        <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Jahresergebnis</div>
        <div class="text-2xl font-bold font-mono" :class="ergebnis >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
          {{ fmt(ergebnis) }}
        </div>
        <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">Ertrag − Aufwand</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-5 py-4">
        <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Einnahmen {{ monthLabel }}</div>
        <div class="text-2xl font-bold font-mono text-green-600 dark:text-green-400">{{ fmt(monatEinnahmen) }}</div>
        <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">Gutschriften lfd. Monat</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-5 py-4">
        <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Ausgaben {{ monthLabel }}</div>
        <div class="text-2xl font-bold font-mono text-red-600 dark:text-red-400">{{ fmt(monatAusgaben) }}</div>
        <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">Belastungen lfd. Monat</div>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <!-- Account balances -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
          <span class="font-semibold text-sm text-gray-700 dark:text-gray-200">Kontosalden</span>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-if="bankAccounts.length === 0">
              <td colspan="2" class="px-4 py-6 text-center text-gray-400 text-xs">Keine Konten</td>
            </tr>
            <tr v-for="a in bankAccounts" :key="a.id" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
              <td class="px-4 py-2.5">
                <span class="font-mono text-xs text-gray-400 dark:text-gray-500 mr-2">{{ a.number }}</span>
                <span class="text-gray-700 dark:text-gray-300">{{ a.name }}</span>
              </td>
              <td class="px-4 py-2.5 text-right font-mono font-medium"
                :class="accountBalance(a) >= 0 ? 'text-gray-800 dark:text-gray-200' : 'text-red-600 dark:text-red-400'">
                {{ fmt(accountBalance(a)) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Recent transactions -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <span class="font-semibold text-sm text-gray-700 dark:text-gray-200">Letzte Buchungen</span>
          <span v-if="openSuggestions > 0" class="text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded-full">
            {{ openSuggestions }} offene Vorschläge
          </span>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-if="recentTransactions.length === 0">
              <td colspan="3" class="px-4 py-6 text-center text-gray-400 text-xs">Keine Buchungen</td>
            </tr>
            <tr v-for="t in recentTransactions" :key="t.id" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
              <td class="px-4 py-2 font-mono text-xs text-gray-400 dark:text-gray-500 w-24">{{ fmtDate(t.date) }}</td>
              <td class="px-2 py-2 text-gray-700 dark:text-gray-300 text-xs truncate max-w-0 w-full">{{ t.description || '—' }}</td>
              <td class="px-4 py-2 text-right font-mono text-xs text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ fmt(t.amount) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetch } from '../api.js'

const accounts = ref([])
const transactions = ref([])
const documents = ref([])
const error = ref(null)

const fmt = (val) =>
  new Intl.NumberFormat('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parseFloat(val) || 0)

const fmtDate = (d) => {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${(day ?? '').padStart(2, '0')}.${(m ?? '').padStart(2, '0')}.${y}`
}

const monthLabel = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('de-CH', { month: 'short', year: '2-digit' })
})

const currentMonth = new Date().toISOString().slice(0, 7)

const acctById = computed(() => {
  const m = {}
  for (const a of accounts.value) m[a.id] = a
  return m
})

const rawBalances = computed(() => {
  const map = {}
  for (const a of accounts.value) map[a.id] = 0
  for (const t of transactions.value) {
    const amt = parseFloat(t.amount) || 0
    if (t.debit_account_id in map)  map[t.debit_account_id]  += amt
    if (t.credit_account_id in map) map[t.credit_account_id] -= amt
  }
  return map
})

function naturalBalance(acc) {
  const raw = rawBalances.value[acc.id] ?? 0
  return ['asset', 'expense'].includes(acc.type) ? raw : -raw
}

function accountBalance(acc) {
  return naturalBalance(acc)
}

const bankAccounts = computed(() =>
  accounts.value
    .filter(a => !a.is_group && a.active && ['asset', 'liability'].includes(a.type))
    .sort((a, b) => a.number.localeCompare(b.number))
)

const nettovermoegen = computed(() => {
  const assets = accounts.value.filter(a => a.type === 'asset' && !a.is_group).reduce((s, a) => s + naturalBalance(a), 0)
  const liabilities = accounts.value.filter(a => a.type === 'liability' && !a.is_group).reduce((s, a) => s + naturalBalance(a), 0)
  return assets - liabilities
})

const ergebnis = computed(() => {
  const ertrag  = accounts.value.filter(a => a.type === 'income'  && !a.is_group).reduce((s, a) => s + naturalBalance(a), 0)
  const aufwand = accounts.value.filter(a => a.type === 'expense' && !a.is_group).reduce((s, a) => s + naturalBalance(a), 0)
  return ertrag - aufwand
})

const monatEinnahmen = computed(() =>
  transactions.value
    .filter(t => t.date.startsWith(currentMonth) && acctById.value[t.credit_account_id]?.type === 'income')
    .reduce((s, t) => s + parseFloat(t.amount), 0)
)

const monatAusgaben = computed(() =>
  transactions.value
    .filter(t => t.date.startsWith(currentMonth) && acctById.value[t.debit_account_id]?.type === 'expense')
    .reduce((s, t) => s + parseFloat(t.amount), 0)
)

const recentTransactions = computed(() =>
  [...transactions.value].reverse().slice(0, 8)
)

const openSuggestions = computed(() =>
  documents.value.reduce((s, d) => s + (d.suggested_count || 0), 0)
)

async function load() {
  try {
    const [aRes, tRes, dRes] = await Promise.all([
      apiFetch('/api/accounts'),
      apiFetch('/api/transactions'),
      apiFetch('/api/documents'),
    ])
    if (!aRes.ok || !tRes.ok) throw new Error()
    accounts.value = await aRes.json()
    transactions.value = await tRes.json()
    if (dRes.ok) documents.value = await dRes.json()
    error.value = null
  } catch {
    error.value = 'Daten konnten nicht geladen werden.'
  }
}

onMounted(load)
</script>
