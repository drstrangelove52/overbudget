<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Buchungsregeln</h1>
      <div class="flex gap-2">
        <button @click="applyRules" :disabled="applying" class="btn-secondary text-sm">
          {{ applying ? 'Wird angewendet…' : 'Regeln anwenden' }}
        </button>
        <button @click="openCreate" class="btn-primary text-sm">+ Neue Regel</button>
      </div>
    </div>

    <div v-if="applyResult" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-300 rounded-lg px-4 py-2 text-sm">
      {{ applyResult.matched }} von {{ applyResult.total }} Vorschlägen zugeordnet.
    </div>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
      {{ error }}
    </div>

    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wide">
            <th class="text-left px-4 py-2.5 border-b border-gray-200 dark:border-gray-700">Name</th>
            <th class="text-left px-4 py-2.5 border-b border-gray-200 dark:border-gray-700">Bedingung</th>
            <th class="text-left px-4 py-2.5 w-40 border-b border-gray-200 dark:border-gray-700">Soll</th>
            <th class="text-left px-4 py-2.5 w-40 border-b border-gray-200 dark:border-gray-700">Haben</th>
            <th class="text-center px-3 py-2.5 w-16 border-b border-gray-200 dark:border-gray-700">Prio</th>
            <th class="text-center px-3 py-2.5 w-20 border-b border-gray-200 dark:border-gray-700">Status</th>
            <th class="w-24 border-b border-gray-200 dark:border-gray-700"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="rules.length === 0">
            <td colspan="7" class="text-center py-10 text-gray-400 text-sm">Noch keine Regeln vorhanden</td>
          </tr>
          <tr
            v-for="r in rules" :key="r.id"
            class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/20"
            :class="!r.active ? 'opacity-50' : ''"
          >
            <td class="px-4 py-2.5 text-gray-700 dark:text-gray-300 font-medium">{{ r.name }}</td>
            <td class="px-4 py-2.5 text-gray-600 dark:text-gray-400 text-xs font-mono">
              {{ fmtCondition(r) }}
            </td>
            <td class="px-4 py-2.5 text-xs">
              <span v-if="r.debit_account" class="text-gray-500 dark:text-gray-400">
                <span class="font-mono text-gray-400">{{ r.debit_account.number }}</span> {{ r.debit_account.name }}
              </span>
              <span v-else class="text-gray-300 dark:text-gray-600">—</span>
            </td>
            <td class="px-4 py-2.5 text-xs">
              <span v-if="r.credit_account" class="text-gray-500 dark:text-gray-400">
                <span class="font-mono text-gray-400">{{ r.credit_account.number }}</span> {{ r.credit_account.name }}
              </span>
              <span v-else class="text-gray-300 dark:text-gray-600">—</span>
            </td>
            <td class="px-3 py-2.5 text-center text-xs text-gray-400">{{ r.priority }}</td>
            <td class="px-3 py-2.5 text-center">
              <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                :class="r.auto_confirm
                  ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                  : r.active
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500'">
                {{ r.auto_confirm ? 'auto' : r.active ? 'aktiv' : 'inaktiv' }}
              </span>
            </td>
            <td class="px-4 py-2.5 text-right whitespace-nowrap">
              <button @click="openEdit(r)" class="text-gray-400 hover:text-indigo-500 mr-3 text-xs transition-colors">Bearb.</button>
              <button @click="confirmDelete(r)" class="text-gray-400 hover:text-red-500 text-xs transition-colors">Löschen</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <RuleModal v-model="showRuleModal" :accounts="accounts" :edit-data="ruleEditData" @saved="onRuleSaved" />

    <!-- Delete confirm -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="deleteTarget = null">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 class="font-semibold text-lg">Regel löschen?</h2>
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
import RuleModal from '../components/RuleModal.vue'

const rules = ref([])
const accounts = ref([])
const error = ref(null)
const showRuleModal = ref(false)
const ruleEditData = ref(null)
const saving = ref(false)
const applying = ref(false)
const applyResult = ref(null)
const deleteTarget = ref(null)
const deleteError = ref(null)

const fieldLabels = { description: 'Beschreibung', counterparty: 'Gegenpartei', amount: 'Betrag' }
const opLabels = { contains: 'enthält', equals: '=', lt: '<', gt: '>', regex: '~' }
const logicLabels = { and: 'UND', or: 'ODER' }

const fmtCondition = (r) => {
  const sep = ' ' + (logicLabels[r.condition_logic] ?? 'UND') + ' '
  return (r.conditions ?? []).map(c =>
    `${fieldLabels[c.field] ?? c.field} ${opLabels[c.operator] ?? c.operator} "${c.value}"`
  ).join(sep)
}

const bookableAccounts = computed(() =>
  [...accounts.value]
    .filter(a => !a.is_group && a.active)
    .sort((a, b) => a.number.localeCompare(b.number))
)

async function load() {
  try {
    const [rRes, aRes] = await Promise.all([apiFetch('/api/rules'), apiFetch('/api/accounts')])
    if (!rRes.ok || !aRes.ok) throw new Error()
    rules.value = await rRes.json()
    accounts.value = await aRes.json()
    error.value = null
  } catch {
    error.value = 'Daten konnten nicht geladen werden.'
  }
}

function openCreate() { ruleEditData.value = null; showRuleModal.value = true }
function openEdit(r) { ruleEditData.value = r; showRuleModal.value = true }
async function onRuleSaved() {
  await apiFetch('/api/rules/apply', { method: 'POST' })
  await load()
}

function confirmDelete(r) { deleteTarget.value = r; deleteError.value = null }
async function doDelete() {
  saving.value = true; deleteError.value = null
  try {
    const res = await apiFetch(`/api/rules/${deleteTarget.value.id}`, { method: 'DELETE' })
    if (!res.ok) { const d = await res.json().catch(() => ({})); deleteError.value = d.detail ?? 'Fehler.'; return }
    await load(); deleteTarget.value = null
  } finally { saving.value = false }
}

async function applyRules() {
  applying.value = true; applyResult.value = null
  try {
    const res = await apiFetch('/api/rules/apply', { method: 'POST' })
    if (res.ok) applyResult.value = await res.json()
  } finally { applying.value = false }
}

onMounted(load)
</script>

<style scoped>
.label { @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1; }
.input { @apply w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500; }
.btn-primary { @apply px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
.btn-secondary { @apply px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50; }
.btn-danger { @apply px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
</style>
