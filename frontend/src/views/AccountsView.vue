<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            v-for="tab in tabs" :key="tab.id"
            @click="activeTab = tab.id"
            class="px-4 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="activeTab === tab.id
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'"
          >{{ tab.label }}</button>
        </div>
        <select
          v-if="activeTab !== 'plan'"
          v-model.number="selectedYear"
          class="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
      <button v-if="activeTab === 'plan'" @click="openCreate" class="btn-primary">+ Neues Konto</button>
    </div>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
      {{ error }}
    </div>

    <!-- ── KONTENPLAN ── -->
    <div v-if="activeTab === 'plan'" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wide">
          <tr>
            <th class="text-left px-4 py-3 w-28">Nummer</th>
            <th class="text-left px-4 py-3">Name</th>
            <th class="text-left px-4 py-3 w-24">Typ</th>
            <th class="text-left px-4 py-3 w-16">Währung</th>
            <th class="text-right px-4 py-3 w-32">Saldo</th>
            <th class="text-center px-4 py-3 w-20">Summe in</th>
            <th class="px-4 py-3 w-28"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
          <tr v-if="sortedAccounts.length === 0">
            <td colspan="7" class="text-center py-10 text-gray-400">Noch keine Konten vorhanden</td>
          </tr>
          <tr
            v-for="row in sortedAccounts" :key="row.id"
            :class="[
              row.is_group ? 'bg-gray-50 dark:bg-gray-700/40' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30',
              !row.active ? 'opacity-50' : ''
            ]"
          >
            <td class="px-4 py-2.5 font-mono text-xs" :class="row.is_group ? 'text-gray-500 dark:text-gray-400' : 'text-gray-400 dark:text-gray-500'">
              {{ row.number }}
            </td>
            <td class="px-4 py-2.5" :class="row.is_group ? 'font-semibold uppercase tracking-wide text-xs text-gray-700 dark:text-gray-200' : ''">
              <RouterLink v-if="!row.is_group" :to="`/konten/${row.id}`"
                :class="['hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors', row.sum_in ? 'pl-3' : '']">
                {{ row.name }}
              </RouterLink>
              <span v-else>{{ row.name }}</span>
            </td>
            <td class="px-4 py-2.5">
              <span v-if="!row.is_group" class="px-2 py-0.5 rounded-full text-xs font-medium" :class="typeClass(row.type)">
                {{ typeLabel(row.type) }}
              </span>
            </td>
            <td class="px-4 py-2.5 text-gray-500 dark:text-gray-400 text-xs">{{ row.is_group ? '' : row.currency }}</td>
            <td class="px-4 py-2.5 text-right font-mono text-sm" :class="row.is_group ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300'">
              {{ fmt(row.balance) }}
            </td>
            <td class="px-4 py-2.5 text-center font-mono text-xs text-gray-400">{{ row.is_group ? '' : (row.sum_in ?? '') }}</td>
            <td class="px-4 py-2.5 text-right whitespace-nowrap">
              <button @click="openEdit(row)" class="text-gray-400 hover:text-indigo-500 mr-3 transition-colors text-xs">Bearb.</button>
              <button @click="confirmDelete(row)" class="text-gray-400 hover:text-red-500 transition-colors text-xs">Löschen</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── BILANZ ── -->
    <div v-if="activeTab === 'bilanz'" class="grid grid-cols-2 gap-4">
      <!-- Aktiven -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-100 dark:border-blue-800">
          <span class="font-semibold text-blue-700 dark:text-blue-300 text-sm uppercase tracking-wide">Aktiven</span>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <template v-for="section in bilanzAktiven" :key="section.key">
              <tr v-if="section.isGroup" class="bg-gray-50 dark:bg-gray-700/30">
                <td class="px-4 py-2 font-semibold text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300" colspan="2">{{ section.name }}</td>
                <td class="px-4 py-2 text-right font-semibold font-mono text-sm">{{ fmt(section.total) }}</td>
              </tr>
              <tr v-else class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                <td class="pl-7 pr-2 py-1.5 text-xs text-gray-400 dark:text-gray-500 font-mono w-20">{{ section.number }}</td>
                <td class="px-2 py-1.5 text-gray-700 dark:text-gray-300">{{ section.name }}</td>
                <td class="px-4 py-1.5 text-right font-mono text-xs text-gray-600 dark:text-gray-400">{{ fmt(section.balance) }}</td>
              </tr>
            </template>
            <tr class="border-t-2 border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20">
              <td class="px-4 py-3 font-bold text-sm uppercase tracking-wide text-blue-700 dark:text-blue-300" colspan="2">Total Aktiven</td>
              <td class="px-4 py-3 text-right font-bold font-mono text-blue-700 dark:text-blue-300">{{ fmt(totalAktiven) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Passiven -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-4 py-3 bg-orange-50 dark:bg-orange-900/20 border-b border-orange-100 dark:border-orange-800">
          <span class="font-semibold text-orange-700 dark:text-orange-300 text-sm uppercase tracking-wide">Passiven</span>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <template v-for="section in bilanzPassiven" :key="section.key">
              <tr v-if="section.isGroup" class="bg-gray-50 dark:bg-gray-700/30">
                <td class="px-4 py-2 font-semibold text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300" colspan="2">{{ section.name }}</td>
                <td class="px-4 py-2 text-right font-semibold font-mono text-sm">{{ fmt(section.total) }}</td>
              </tr>
              <tr v-else class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                <td class="pl-7 pr-2 py-1.5 text-xs text-gray-400 dark:text-gray-500 font-mono w-20">{{ section.number }}</td>
                <td class="px-2 py-1.5 text-gray-700 dark:text-gray-300">{{ section.name }}</td>
                <td class="px-4 py-1.5 text-right font-mono text-xs text-gray-600 dark:text-gray-400">{{ fmt(section.balance) }}</td>
              </tr>
            </template>
            <tr class="bg-purple-50/40 dark:bg-purple-900/10">
              <td class="pl-7 pr-2 py-1.5 text-xs text-gray-400 dark:text-gray-500 font-mono w-20"></td>
              <td class="px-2 py-1.5 text-gray-700 dark:text-gray-300 italic">Jahresergebnis</td>
              <td class="px-4 py-1.5 text-right font-mono text-sm" :class="ergebnis >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'">{{ fmt(ergebnis) }}</td>
            </tr>
            <tr class="border-t-2 border-orange-200 dark:border-orange-700 bg-orange-50 dark:bg-orange-900/20">
              <td class="px-4 py-3 font-bold text-sm uppercase tracking-wide text-orange-700 dark:text-orange-300" colspan="2">Total Passiven</td>
              <td class="px-4 py-3 text-right font-bold font-mono text-orange-700 dark:text-orange-300">{{ fmt(totalPassiven) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── ERFOLGSRECHNUNG ── -->
    <div v-if="activeTab === 'erfolg'" class="grid grid-cols-2 gap-4">
      <!-- Aufwand (links) -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-4 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-100 dark:border-red-800">
          <span class="font-semibold text-red-700 dark:text-red-300 text-sm uppercase tracking-wide">Aufwand</span>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <template v-for="section in erfolgsAufwand" :key="section.key">
              <tr v-if="section.isGroup" class="bg-gray-50 dark:bg-gray-700/30">
                <td class="px-4 py-2 font-semibold text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300" colspan="2">{{ section.name }}</td>
                <td class="px-4 py-2 text-right font-semibold font-mono text-sm">{{ fmt(section.total) }}</td>
              </tr>
              <tr v-else class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                <td class="pl-7 pr-2 py-1.5 text-xs text-gray-400 font-mono w-20">{{ section.number }}</td>
                <td class="px-2 py-1.5 text-gray-700 dark:text-gray-300">{{ section.name }}</td>
                <td class="px-4 py-1.5 text-right font-mono text-xs text-gray-600 dark:text-gray-400">{{ fmt(section.balance) }}</td>
              </tr>
            </template>
            <tr class="border-t-2 border-red-200 dark:border-red-700 bg-red-50 dark:bg-red-900/20">
              <td class="px-4 py-3 font-bold text-sm uppercase tracking-wide text-red-700 dark:text-red-300" colspan="2">Total Aufwand</td>
              <td class="px-4 py-3 text-right font-bold font-mono text-red-700 dark:text-red-300">{{ fmt(totalAufwand) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Ertrag (rechts) -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-4 py-3 bg-green-50 dark:bg-green-900/20 border-b border-green-100 dark:border-green-800">
          <span class="font-semibold text-green-700 dark:text-green-300 text-sm uppercase tracking-wide">Ertrag</span>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <template v-for="section in erfolgsErtrag" :key="section.key">
              <tr v-if="section.isGroup" class="bg-gray-50 dark:bg-gray-700/30">
                <td class="px-4 py-2 font-semibold text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300" colspan="2">{{ section.name }}</td>
                <td class="px-4 py-2 text-right font-semibold font-mono text-sm">{{ fmt(section.total) }}</td>
              </tr>
              <tr v-else class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                <td class="pl-7 pr-2 py-1.5 text-xs text-gray-400 font-mono w-20">{{ section.number }}</td>
                <td class="px-2 py-1.5 text-gray-700 dark:text-gray-300">{{ section.name }}</td>
                <td class="px-4 py-1.5 text-right font-mono text-xs text-gray-600 dark:text-gray-400">{{ fmt(section.balance) }}</td>
              </tr>
            </template>
            <tr class="border-t-2 border-green-200 dark:border-green-700 bg-green-50 dark:bg-green-900/20">
              <td class="px-4 py-3 font-bold text-sm uppercase tracking-wide text-green-700 dark:text-green-300" colspan="2">Total Ertrag</td>
              <td class="px-4 py-3 text-right font-bold font-mono text-green-700 dark:text-green-300">{{ fmt(totalErtrag) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Ergebnis -->
      <div class="col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <span class="font-semibold text-gray-700 dark:text-gray-300">Ergebnis (Ertrag − Aufwand)</span>
        <span class="font-bold text-xl font-mono" :class="ergebnis >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
          {{ fmt(ergebnis) }}
        </span>
      </div>
    </div>

    <AccountModal v-model="showAccountModal" :accounts="accounts" :edit-data="accountEditData" @saved="onAccountSaved" />

    <!-- ── LÖSCH-BESTÄTIGUNG ── -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="deleteTarget = null">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 class="font-semibold text-lg">Konto löschen?</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          <strong>{{ deleteTarget.number }} – {{ deleteTarget.name }}</strong> wird unwiderruflich gelöscht.
        </p>
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
import { RouterLink } from 'vue-router'
import { apiFetch } from '../api.js'
import AccountModal from '../components/AccountModal.vue'

const accounts = ref([])
const transactions = ref([])
const error = ref(null)
const showAccountModal = ref(false)
const accountEditData = ref(null)
const saving = ref(false)
const deleteTarget = ref(null)
const deleteError = ref(null)
const activeTab = ref('plan')

const tabs = [
  { id: 'plan',   label: 'Kontenplan' },
  { id: 'bilanz', label: 'Bilanz' },
  { id: 'erfolg', label: 'Erfolgsrechnung' },
]

const accountTypes = [
  { value: 'asset',     label: 'Aktiva' },
  { value: 'liability', label: 'Passiva' },
  { value: 'equity',    label: 'Eigenkapital' },
  { value: 'income',    label: 'Ertrag' },
  { value: 'expense',   label: 'Aufwand' },
]
const typeLabel = (t) => accountTypes.find(x => x.value === t)?.label ?? t
const typeClass = (t) => ({
  asset:     'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  liability: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  equity:    'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  income:    'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  expense:   'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
}[t] ?? '')

const fmt = (val) =>
  new Intl.NumberFormat('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parseFloat(val) || 0)

// String sort so "30" < "3000" — groups appear right before their members
const sorted = computed(() =>
  [...accounts.value].sort((a, b) => a.number.localeCompare(b.number))
)

const selectedYear = ref(new Date().getFullYear())

const availableYears = computed(() => {
  const years = new Set(transactions.value.map(t => parseInt(t.date.slice(0, 4))))
  years.add(new Date().getFullYear())
  return [...years].sort((a, b) => b - a)
})

function computeRawBalances(txList) {
  const map = {}
  for (const a of accounts.value) map[a.id] = 0
  for (const t of txList) {
    const amt = parseFloat(t.amount) || 0
    if (t.debit_account_id in map)  map[t.debit_account_id]  += amt
    if (t.credit_account_id in map) map[t.credit_account_id] -= amt
  }
  return map
}

function naturalBalanceFrom(acc, rawMap) {
  const raw = rawMap[acc.id] ?? 0
  return ['asset', 'expense'].includes(acc.type) ? raw : -raw
}

// All-time (Kontenplan)
const rawBalances = computed(() => computeRawBalances(transactions.value))
const naturalBalance = (acc) => naturalBalanceFrom(acc, rawBalances.value)

// Bilanz: cumulative up to year-end
const rawBalancesBilanz = computed(() =>
  computeRawBalances(transactions.value.filter(t => t.date <= `${selectedYear.value}-12-31`))
)

// Erfolgsrechnung: only selected year
const rawBalancesErfolg = computed(() =>
  computeRawBalances(transactions.value.filter(t => t.date.startsWith(`${selectedYear.value}`)))
)

function buildBalanceMap(rawMap) {
  const map = {}
  for (const a of accounts.value) map[a.number] = naturalBalanceFrom(a, rawMap)
  for (const a of accounts.value) {
    if (!a.is_group && a.sum_in)
      map[a.sum_in] = (map[a.sum_in] || 0) + naturalBalanceFrom(a, rawMap)
  }
  return map
}

const balanceMap = computed(() => buildBalanceMap(rawBalances.value))

const sortedAccounts = computed(() =>
  sorted.value.map(a => ({ ...a, balance: naturalBalance(a) }))
)

function buildSections(types, rawMap) {
  const bMap = buildBalanceMap(rawMap)
  return sorted.value
    .filter(a => types.includes(a.type))
    .map(a => a.is_group
      ? { key: `g-${a.number}`, isGroup: true, name: a.name, number: a.number, total: bMap[a.number] ?? 0 }
      : { key: `a-${a.id}`, isGroup: false, name: a.name, number: a.number, balance: naturalBalanceFrom(a, rawMap) }
    )
}

const bilanzAktiven  = computed(() => buildSections(['asset'],              rawBalancesBilanz.value))
const bilanzPassiven = computed(() => buildSections(['liability', 'equity'], rawBalancesBilanz.value))
const erfolgsErtrag  = computed(() => buildSections(['income'],             rawBalancesErfolg.value))
const erfolgsAufwand = computed(() => buildSections(['expense'],            rawBalancesErfolg.value))

const totalAktiven  = computed(() => accounts.value.filter(a => a.type === 'asset'                     && !a.is_group).reduce((s, a) => s + naturalBalanceFrom(a, rawBalancesBilanz.value), 0))
const totalPassiven = computed(() => accounts.value.filter(a => ['liability','equity'].includes(a.type) && !a.is_group).reduce((s, a) => s + naturalBalanceFrom(a, rawBalancesBilanz.value), 0) + ergebnis.value)
const totalErtrag   = computed(() => accounts.value.filter(a => a.type === 'income'                    && !a.is_group).reduce((s, a) => s + naturalBalanceFrom(a, rawBalancesErfolg.value), 0))
const totalAufwand  = computed(() => accounts.value.filter(a => a.type === 'expense'                   && !a.is_group).reduce((s, a) => s + naturalBalanceFrom(a, rawBalancesErfolg.value), 0))
const ergebnis      = computed(() => totalErtrag.value - totalAufwand.value)

async function load() {
  try {
    const [aRes, tRes] = await Promise.all([apiFetch('/api/accounts'), apiFetch('/api/transactions')])
    if (!aRes.ok || !tRes.ok) throw new Error()
    accounts.value = await aRes.json()
    transactions.value = await tRes.json()
    error.value = null
  } catch {
    error.value = 'Daten konnten nicht geladen werden.'
  }
}

function openCreate() { accountEditData.value = null; showAccountModal.value = true }
function openEdit(acc) { accountEditData.value = acc; showAccountModal.value = true }
async function onAccountSaved() { await load() }

function confirmDelete(acc) { deleteTarget.value = acc; deleteError.value = null }
async function doDelete() {
  saving.value = true; deleteError.value = null
  try {
    const res = await apiFetch(`/api/accounts/${deleteTarget.value.id}`, { method: 'DELETE' })
    if (!res.ok) { const d = await res.json().catch(() => ({})); deleteError.value = d.detail ?? 'Fehler beim Löschen.'; return }
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
