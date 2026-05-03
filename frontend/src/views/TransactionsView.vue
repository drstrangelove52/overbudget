<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <h1 class="text-2xl font-semibold">Buchungen</h1>
      <div class="flex items-center gap-2">
        <select v-model.number="selectedYear" class="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500">
          <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
        </select>
        <input
          v-model="search"
          type="search"
          placeholder="Suche…"
          class="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-48"
        />
      </div>
    </div>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
      {{ error }}
    </div>

    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wide">
            <th class="text-left px-3 py-2.5 w-32 border-b border-gray-200 dark:border-gray-700">Datum</th>
            <th class="text-left px-3 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Beleg-Nr.</th>
            <th class="text-left px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Beschreibung</th>
            <th class="text-left px-3 py-2.5 w-44 border-b border-gray-200 dark:border-gray-700">Soll</th>
            <th class="text-left px-3 py-2.5 w-44 border-b border-gray-200 dark:border-gray-700">Haben</th>
            <th class="text-right px-3 py-2.5 w-32 border-b border-gray-200 dark:border-gray-700">Betrag</th>
            <th class="w-16 border-b border-gray-200 dark:border-gray-700"></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="row in displayRows" :key="row.key">
            <!-- Split-Gruppe: erste Zeile -->
            <tr v-if="row.type === 'split-first'"
              class="border-b border-gray-100 dark:border-gray-700/50 group bg-violet-50/30 dark:bg-violet-900/10 cursor-pointer"
              @click="openEditSplit(row.t.group_id)"
            >
              <td class="px-3 py-2 font-mono text-xs text-gray-500 dark:text-gray-400 border-l-2 border-violet-400">{{ fmtDate(row.t.date) }}</td>
              <td class="px-3 py-2 text-gray-400 dark:text-gray-500 text-xs">{{ row.t.reference || '—' }}</td>
              <td class="px-3 py-2 text-gray-500 dark:text-gray-400 italic text-xs">
                <span class="inline-flex items-center gap-1">
                  <span class="text-violet-500 font-medium">Split</span>
                  <span>· {{ row.groupSize }} Zeilen</span>
                  <span v-if="row.t.group_description" class="not-italic text-gray-700 dark:text-gray-200 font-medium">· {{ row.t.group_description }}</span>
                </span>
              </td>
              <td class="px-3 py-2 text-gray-400 text-xs">—</td>
              <td class="px-3 py-2">
                <span class="font-mono text-xs text-gray-400 dark:text-gray-500 mr-1">{{ row.t.credit_account?.number }}</span>
                <span class="text-gray-600 dark:text-gray-300 text-xs">{{ row.t.credit_account?.name }}</span>
              </td>
              <td class="px-3 py-2 text-right font-mono font-semibold text-violet-700 dark:text-violet-300">{{ fmt(row.groupTotal) }}</td>
              <td class="px-3 py-2 text-center opacity-0 group-hover:opacity-100 transition-opacity">
                <button @click.stop="confirmDeleteGroup(row.t)" class="text-gray-400 hover:text-red-500 transition-colors" title="Splittbuchung löschen">✕</button>
              </td>
            </tr>

            <!-- Split-Gruppe: Unterzeilen -->
            <tr v-else-if="row.type === 'split-line'"
              class="border-b border-gray-100 dark:border-gray-700/50 bg-violet-50/20 dark:bg-violet-900/5"
            >
              <td class="border-l-2 border-violet-300 dark:border-violet-700"></td>
              <td class="px-3 py-1.5 text-gray-300 dark:text-gray-600 text-xs pl-6">└</td>
              <td class="px-3 py-1.5 text-gray-600 dark:text-gray-300 text-xs">
                <div>{{ row.t.description || '—' }}</div>
                <div v-if="row.t.counterparty" class="text-gray-400 dark:text-gray-500 text-xs mt-0.5">{{ row.t.counterparty }}</div>
              </td>
              <td class="px-3 py-1.5">
                <span class="font-mono text-xs text-gray-400 dark:text-gray-500 mr-1">{{ row.t.debit_account?.number }}</span>
                <span class="text-gray-600 dark:text-gray-300 text-xs">{{ row.t.debit_account?.name }}</span>
              </td>
              <td class="px-3 py-1.5 text-gray-400 text-xs">—</td>
              <td class="px-3 py-1.5 text-right font-mono text-xs text-gray-600 dark:text-gray-300">{{ fmt(row.t.amount) }}</td>
              <td></td>
            </tr>

            <!-- Normale Buchung -->
            <tr v-else
              class="border-b border-gray-100 dark:border-gray-700/50 group"
              :class="editingId === row.t.id ? 'bg-indigo-50/40 dark:bg-indigo-900/10' : 'hover:bg-gray-50/80 dark:hover:bg-gray-700/20'"
            >
              <template v-if="editingId === row.t.id">
                <td class="px-1 py-1"><input :ref="el => { editRefs.date = el }" v-model="editForm.date" type="date" required class="cell-input" @keydown.enter.prevent="editRefs.refNr?.focus()" @keydown.tab.prevent="editRefs.refNr?.focus()" @keydown.escape="cancelEdit" /></td>
                <td class="px-1 py-1"><input :ref="el => { editRefs.refNr = el }" v-model="editForm.reference" type="text" class="cell-input" placeholder="—" @keydown.enter.prevent="editRefs.desc?.focus()" @keydown.tab.prevent="editRefs.desc?.focus()" @keydown.escape="cancelEdit" /></td>
                <td class="px-1 py-1"><input :ref="el => { editRefs.desc = el }" v-model="editForm.description" type="text" required class="cell-input" @keydown.enter.prevent="editRefs.debit?.focus()" @keydown.tab.prevent="editRefs.debit?.focus()" @keydown.escape="cancelEdit" /></td>
                <td class="px-1 py-1"><select :ref="el => { editRefs.debit = el }" v-model="editForm.debit_account_id" required class="cell-input" @keydown.escape="cancelEdit"><option value="">—</option><option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option></select></td>
                <td class="px-1 py-1"><select :ref="el => { editRefs.credit = el }" v-model="editForm.credit_account_id" required class="cell-input" @keydown.escape="cancelEdit"><option value="">—</option><option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option></select></td>
                <td class="px-1 py-1"><input :ref="el => { editRefs.amount = el }" v-model="editForm.amount" type="number" step="0.01" min="0.01" required class="cell-input text-right" @blur="editForm.amount = fmtInput(editForm.amount)" @keydown.enter="saveEdit" @keydown.tab.prevent="saveEdit" @keydown.escape="cancelEdit" /></td>
                <td class="px-1 py-1 text-center">
                  <button @click="saveEdit" class="text-indigo-500 hover:text-indigo-700 font-bold mr-1" title="Speichern">✓</button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600" title="Abbrechen">✕</button>
                </td>
              </template>
              <template v-else>
                <td class="px-3 py-2 font-mono text-xs text-gray-500 dark:text-gray-400 cursor-pointer" @click="startEdit(row.t)">{{ fmtDate(row.t.date) }}</td>
                <td class="px-3 py-2 text-gray-400 dark:text-gray-500 text-xs cursor-pointer" @click="startEdit(row.t)">{{ row.t.reference || '—' }}</td>
                <td class="px-3 py-2 text-gray-700 dark:text-gray-300 cursor-pointer" @click="startEdit(row.t)">
                  <div>{{ row.t.description || '—' }}</div>
                  <div v-if="row.t.counterparty" class="text-gray-400 dark:text-gray-500 text-xs mt-0.5">{{ row.t.counterparty }}</div>
                </td>
                <td class="px-3 py-2 cursor-pointer" @click="startEdit(row.t)">
                  <span class="font-mono text-xs text-gray-400 dark:text-gray-500 mr-1">{{ row.t.debit_account?.number }}</span>
                  <span class="text-gray-600 dark:text-gray-300 text-xs">{{ row.t.debit_account?.name }}</span>
                </td>
                <td class="px-3 py-2 cursor-pointer" @click="startEdit(row.t)">
                  <span class="font-mono text-xs text-gray-400 dark:text-gray-500 mr-1">{{ row.t.credit_account?.number }}</span>
                  <span class="text-gray-600 dark:text-gray-300 text-xs">{{ row.t.credit_account?.name }}</span>
                </td>
                <td class="px-3 py-2 text-right font-mono text-gray-800 dark:text-gray-200 cursor-pointer" @click="startEdit(row.t)">{{ fmt(row.t.amount) }}</td>
                <td class="px-3 py-2 text-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click.stop="confirmDelete(row.t)" class="text-gray-400 hover:text-red-500 transition-colors" title="Löschen">✕</button>
                </td>
              </template>
            </tr>
          </template>

          <!-- Neue Buchung -->
          <tr class="bg-green-50/30 dark:bg-green-900/5">
            <td class="px-1 py-1"><input ref="newDateRef" v-model="newForm.date" type="date" required class="cell-input" @keydown.enter="focusNext($event, 'newRef')" @keydown.tab.prevent="focusNext($event, 'newRef')" @keydown.escape="resetNewForm" /></td>
            <td class="px-1 py-1"><input ref="newRef" v-model="newForm.reference" type="text" class="cell-input" placeholder="—" @keydown.enter="focusNext($event, 'newDescRef')" @keydown.tab.prevent="focusNext($event, 'newDescRef')" @keydown.escape="resetNewForm" /></td>
            <td class="px-1 py-1"><input ref="newDescRef" v-model="newForm.description" type="text" class="cell-input" placeholder="Buchungstext *" @keydown.enter="focusNext($event, 'newDebitRef')" @keydown.tab.prevent="focusNext($event, 'newDebitRef')" @keydown.escape="resetNewForm" /></td>
            <td class="px-1 py-1">
              <select ref="newDebitRef" v-model="newForm.debit_account_id" class="cell-input" @keydown.enter="focusNext($event, 'newCreditRef')" @keydown.escape="resetNewForm">
                <option value="">— Sollkonto —</option>
                <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
              </select>
            </td>
            <td class="px-1 py-1">
              <select ref="newCreditRef" v-model="newForm.credit_account_id" class="cell-input" @keydown.enter="focusNext($event, 'newAmountRef')" @keydown.escape="resetNewForm">
                <option value="">— Habenkonto —</option>
                <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
              </select>
            </td>
            <td class="px-1 py-1">
              <input ref="newAmountRef" v-model="newForm.amount" type="number" step="0.01" min="0.01" class="cell-input text-right" placeholder="0.00" @blur="newForm.amount = fmtInput(newForm.amount)" @keydown.enter="saveNew" @keydown.tab.prevent="saveNew" @keydown.escape="resetNewForm" />
            </td>
            <td class="px-1 py-1 text-center flex items-center justify-center gap-1 h-full">
              <button @click="saveNew" :disabled="savingNew" class="text-green-600 hover:text-green-700 font-bold text-lg leading-none" title="Buchung erfassen">+</button>
              <button @click="openSplit" class="text-violet-500 hover:text-violet-700 font-bold text-xs leading-none border border-violet-300 dark:border-violet-700 rounded px-1 py-0.5" title="Splittbuchung erfassen">Split</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="newError" class="text-red-500 text-sm px-1">{{ newError }}</div>

    <!-- Lösch-Bestätigung (Einzelbuchung) -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="deleteTarget = null">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 class="font-semibold text-lg">Buchung löschen?</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {{ fmtDate(deleteTarget.date) }} —
          <strong>{{ deleteTarget.debit_account?.number }} / {{ deleteTarget.credit_account?.number }}</strong>
          — {{ fmt(deleteTarget.amount) }}
        </p>
        <div v-if="deleteError" class="text-red-500 text-sm">{{ deleteError }}</div>
        <div class="flex justify-end gap-3">
          <button @click="deleteTarget = null" class="btn-secondary">Abbrechen</button>
          <button @click="doDelete" :disabled="saving" class="btn-danger">{{ saving ? 'Löschen…' : 'Löschen' }}</button>
        </div>
      </div>
    </div>

    <!-- Lösch-Bestätigung (Splittbuchung) -->
    <div v-if="deleteGroupTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="deleteGroupTarget = null">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 class="font-semibold text-lg">Splittbuchung löschen?</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Alle {{ deleteGroupSize }} Zeilen dieser Splittbuchung vom {{ fmtDate(deleteGroupTarget.date) }} werden gelöscht.
        </p>
        <div v-if="deleteError" class="text-red-500 text-sm">{{ deleteError }}</div>
        <div class="flex justify-end gap-3">
          <button @click="deleteGroupTarget = null" class="btn-secondary">Abbrechen</button>
          <button @click="doDeleteGroup" :disabled="saving" class="btn-danger">{{ saving ? 'Löschen…' : 'Löschen' }}</button>
        </div>
      </div>
    </div>

    <!-- Splittbuchung Modal -->
    <div v-if="splitModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="splitModal = false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-lg">{{ editingGroupId !== null ? 'Splittbuchung bearbeiten' : 'Splittbuchung erfassen' }}</h2>
          <button @click="splitModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</button>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="label">Datum *</label>
            <input v-model="splitForm.date" type="date" required class="input" />
          </div>
          <div>
            <label class="label">Beleg-Nr.</label>
            <input v-model="splitForm.reference" type="text" class="input" placeholder="—" />
          </div>
          <div>
            <label class="label">Beschreibung</label>
            <input v-model="splitForm.description" type="text" class="input" placeholder="z.B. Coop" />
          </div>
        </div>
        <div>
          <label class="label">Habenkonto (Zahlung) *</label>
          <select v-model="splitForm.credit_account_id" required class="input">
            <option value="">— Konto wählen —</option>
            <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
          </select>
        </div>

        <!-- Zeilen -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Positionen</span>
            <button @click="addSplitLine" class="text-sm text-indigo-600 hover:text-indigo-700 font-medium">+ Zeile</button>
          </div>
          <div class="grid grid-cols-12 gap-2 mb-1 px-0.5">
            <div class="col-span-5 text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Sollkonto *</div>
            <div class="col-span-4 text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Beschreibung *</div>
            <div class="col-span-2 text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide text-right">Betrag *</div>
            <div class="col-span-1"></div>
          </div>
          <div class="space-y-2">
            <div v-for="(line, i) in splitForm.lines" :key="i" class="grid grid-cols-12 gap-2 items-center">
              <div class="col-span-5">
                <select v-model="line.debit_account_id" class="input text-sm">
                  <option value="">— Sollkonto —</option>
                  <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
                </select>
              </div>
              <div class="col-span-4">
                <input v-model="line.description" type="text" class="input text-sm" placeholder="Beschreibung *" />
              </div>
              <div class="col-span-2">
                <input v-model="line.amount" type="number" step="0.01" min="0.01" class="input text-sm text-right" placeholder="0.00" @blur="line.amount = fmtInput(line.amount)" />
              </div>
              <div class="col-span-1 text-center">
                <button v-if="splitForm.lines.length > 2" @click="removeSplitLine(i)" class="text-gray-400 hover:text-red-500">✕</button>
              </div>
            </div>
          </div>

          <!-- Summe -->
          <div class="mt-3 flex justify-end gap-4 text-sm">
            <span class="text-gray-500 dark:text-gray-400">Total:</span>
            <span class="font-mono font-semibold" :class="splitLinesValid ? 'text-green-600 dark:text-green-400' : 'text-gray-700 dark:text-gray-200'">
              {{ fmt(splitTotal) }}
            </span>
          </div>
        </div>

        <div v-if="splitError" class="text-red-500 text-sm">{{ splitError }}</div>

        <div class="flex justify-end gap-3 pt-2">
          <button @click="splitModal = false" class="btn-secondary">Abbrechen</button>
          <button @click="saveSplit" :disabled="savingSplit" class="btn-primary">{{ savingSplit ? 'Speichern…' : 'Speichern' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { apiFetch } from '../api.js'

const transactions = ref([])
const accounts = ref([])
const selectedYear = ref(new Date().getFullYear())
const search = ref('')

const availableYears = computed(() => {
  const years = new Set(transactions.value.map(t => parseInt(t.date.slice(0, 4))))
  years.add(new Date().getFullYear())
  return [...years].sort((a, b) => b - a)
})

const filteredTransactions = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return transactions.value
  return transactions.value.filter(t =>
    t.description?.toLowerCase().includes(q) ||
    t.reference?.toLowerCase().includes(q) ||
    t.counterparty?.toLowerCase().includes(q) ||
    t.debit_account?.name?.toLowerCase().includes(q) ||
    t.debit_account?.number?.includes(q) ||
    t.credit_account?.name?.toLowerCase().includes(q) ||
    t.credit_account?.number?.includes(q) ||
    String(t.amount).includes(q)
  )
})

// Build display rows: group split transactions, keep normal ones flat
const displayRows = computed(() => {
  const rows = []
  const seen = new Set()

  for (const t of filteredTransactions.value) {
    if (t.group_id == null) {
      rows.push({ key: `t-${t.id}`, type: 'normal', t })
      continue
    }
    if (seen.has(t.group_id)) {
      rows.push({ key: `t-${t.id}`, type: 'split-line', t })
      continue
    }
    // First occurrence of this group_id
    seen.add(t.group_id)
    const groupLines = filteredTransactions.value.filter(x => x.group_id === t.group_id)
    const groupTotal = groupLines.reduce((s, x) => s + parseFloat(x.amount), 0)
    rows.push({ key: `g-${t.group_id}`, type: 'split-first', t, groupSize: groupLines.length, groupTotal })
    rows.push({ key: `t-${t.id}`, type: 'split-line', t })
  }
  return rows
})

const error = ref(null)
const newError = ref(null)
const saving = ref(false)
const savingNew = ref(false)
const deleteTarget = ref(null)
const deleteGroupTarget = ref(null)
const deleteGroupSize = ref(0)
const deleteError = ref(null)

const editingId = ref(null)
const editForm = ref({})
const editRefs = { date: null, refNr: null, desc: null, debit: null, credit: null, amount: null }

const newDateRef = ref(null)
const newRef = ref(null)
const newDescRef = ref(null)
const newDebitRef = ref(null)
const newCreditRef = ref(null)
const newAmountRef = ref(null)

const today = new Date().toISOString().slice(0, 10)
const emptyNew = () => ({ date: today, reference: '', description: '', debit_account_id: '', credit_account_id: '', amount: '' })
const newForm = ref(emptyNew())

// Split modal
const splitModal = ref(false)
const savingSplit = ref(false)
const splitError = ref(null)
const editingGroupId = ref(null)
const emptySplitForm = () => ({
  date: today,
  reference: '',
  description: '',
  credit_account_id: '',
  lines: [
    { debit_account_id: '', description: '', amount: '' },
    { debit_account_id: '', description: '', amount: '' },
  ]
})
const splitForm = ref(emptySplitForm())
const splitTotal = computed(() => splitForm.value.lines.reduce((s, l) => s + (parseFloat(l.amount) || 0), 0))
const splitLinesValid = computed(() => splitForm.value.lines.length >= 2 && splitTotal.value > 0)

function openSplit() {
  editingGroupId.value = null
  splitForm.value = emptySplitForm()
  splitForm.value.date = newForm.value.date || today
  splitForm.value.reference = newForm.value.reference || ''
  splitError.value = null
  splitModal.value = true
}

function openEditSplit(groupId) {
  const lines = transactions.value.filter(t => t.group_id === groupId)
  if (!lines.length) return
  editingGroupId.value = groupId
  splitForm.value = {
    date: lines[0].date,
    reference: lines[0].reference || '',
    description: lines[0].group_description || '',
    credit_account_id: lines[0].credit_account_id,
    lines: lines.map(t => ({
      debit_account_id: t.debit_account_id,
      description: t.description || '',
      amount: parseFloat(t.amount).toFixed(2),
    }))
  }
  splitError.value = null
  splitModal.value = true
}
function addSplitLine() {
  splitForm.value.lines.push({ debit_account_id: '', description: '', amount: '' })
}
function removeSplitLine(i) {
  splitForm.value.lines.splice(i, 1)
}
async function saveSplit() {
  splitError.value = null
  const f = splitForm.value
  if (!f.date) { splitError.value = 'Datum fehlt.'; return }
  if (!f.credit_account_id) { splitError.value = 'Habenkonto fehlt.'; return }
  for (const l of f.lines) {
    if (!l.debit_account_id) { splitError.value = 'Alle Sollkonten ausfüllen.'; return }
    if (!l.description) { splitError.value = 'Alle Beschreibungen ausfüllen.'; return }
    if (!l.amount || parseFloat(l.amount) <= 0) { splitError.value = 'Alle Beträge ausfüllen.'; return }
  }
  savingSplit.value = true
  try {
    const body = {
      date: f.date,
      reference: f.reference || null,
      description: f.description || null,
      credit_account_id: f.credit_account_id,
      lines: f.lines.map(l => ({ debit_account_id: l.debit_account_id, description: l.description, amount: parseFloat(l.amount) }))
    }
    const url = editingGroupId.value !== null
      ? `/api/transactions/split/${editingGroupId.value}`
      : '/api/transactions/split'
    const method = editingGroupId.value !== null ? 'PUT' : 'POST'
    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!res.ok) { const d = await res.json().catch(() => ({})); splitError.value = d.detail ?? 'Fehler.'; return }
    await load()
    splitModal.value = false
    if (!editingGroupId.value) resetNewForm()
  } finally { savingSplit.value = false }
}

const fmt = (val) =>
  new Intl.NumberFormat('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parseFloat(val) || 0)

const fmtInput = (val) => val && !isNaN(parseFloat(val)) ? parseFloat(val).toFixed(2) : val

const fmtDate = (d) => {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${(day ?? '').padStart(2, '0')}.${(m ?? '').padStart(2, '0')}.${y}`
}

const bookableAccounts = computed(() =>
  [...accounts.value]
    .filter(a => !a.is_group && a.active)
    .sort((a, b) => a.number.localeCompare(b.number))
)

async function load() {
  try {
    const [tRes, aRes] = await Promise.all([apiFetch(`/api/transactions?year=${selectedYear.value}`), apiFetch('/api/accounts')])
    if (!tRes.ok || !aRes.ok) throw new Error()
    transactions.value = await tRes.json()
    accounts.value = await aRes.json()
    error.value = null
  } catch {
    error.value = 'Daten konnten nicht geladen werden.'
  }
}

async function startEdit(t) {
  editingId.value = t.id
  editForm.value = {
    date: t.date,
    reference: t.reference ?? '',
    description: t.description ?? '',
    debit_account_id: t.debit_account_id,
    credit_account_id: t.credit_account_id,
    amount: parseFloat(t.amount).toFixed(2),
  }
  await nextTick()
  editRefs.date?.focus()
}

function cancelEdit() {
  editingId.value = null
  editForm.value = {}
}

async function saveEdit() {
  if (!editForm.value.date || !editForm.value.description || !editForm.value.debit_account_id || !editForm.value.credit_account_id || !editForm.value.amount) return
  if (editForm.value.debit_account_id === editForm.value.credit_account_id) return
  saving.value = true
  try {
    const body = { ...editForm.value, reference: editForm.value.reference || null, description: editForm.value.description || null, amount: parseFloat(editForm.value.amount) }
    const res = await apiFetch(`/api/transactions/${editingId.value}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!res.ok) return
    await load()
    cancelEdit()
  } finally { saving.value = false }
}

function focusNext(event, refName) {
  event.preventDefault()
  const refs = { newRef, newDescRef, newDebitRef, newCreditRef, newAmountRef }
  refs[refName]?.value?.focus()
}

function resetNewForm() {
  newForm.value = emptyNew()
  newError.value = null
  nextTick(() => newDateRef.value?.focus())
}

async function saveNew() {
  newError.value = null
  const f = newForm.value
  if (!f.date) { newError.value = 'Datum fehlt.'; return }
  if (!f.description) { newError.value = 'Beschreibung fehlt.'; return }
  if (!f.debit_account_id) { newError.value = 'Sollkonto fehlt.'; return }
  if (!f.credit_account_id) { newError.value = 'Habenkonto fehlt.'; return }
  if (!f.amount || parseFloat(f.amount) <= 0) { newError.value = 'Betrag fehlt.'; return }
  if (f.debit_account_id === f.credit_account_id) { newError.value = 'Soll- und Habenkonto müssen unterschiedlich sein.'; return }

  savingNew.value = true
  try {
    const body = { date: f.date, reference: f.reference || null, description: f.description, debit_account_id: f.debit_account_id, credit_account_id: f.credit_account_id, amount: parseFloat(f.amount) }
    const res = await apiFetch('/api/transactions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!res.ok) { const d = await res.json().catch(() => ({})); newError.value = d.detail ?? 'Fehler.'; return }
    await load()
    newForm.value = emptyNew()
    await nextTick()
    newDateRef.value?.focus()
  } finally { savingNew.value = false }
}

function confirmDelete(t) { deleteTarget.value = t; deleteError.value = null }
async function doDelete() {
  saving.value = true; deleteError.value = null
  try {
    const res = await apiFetch(`/api/transactions/${deleteTarget.value.id}`, { method: 'DELETE' })
    if (!res.ok) { const d = await res.json().catch(() => ({})); deleteError.value = d.detail ?? 'Fehler.'; return }
    await load(); deleteTarget.value = null
  } finally { saving.value = false }
}

function confirmDeleteGroup(t) {
  const size = transactions.value.filter(x => x.group_id === t.group_id).length
  deleteGroupTarget.value = t
  deleteGroupSize.value = size
  deleteError.value = null
}
async function doDeleteGroup() {
  saving.value = true; deleteError.value = null
  try {
    const res = await apiFetch(`/api/transactions/${deleteGroupTarget.value.id}`, { method: 'DELETE' })
    if (!res.ok) { const d = await res.json().catch(() => ({})); deleteError.value = d.detail ?? 'Fehler.'; return }
    await load(); deleteGroupTarget.value = null
  } finally { saving.value = false }
}

watch(selectedYear, () => { search.value = ''; load() })
onMounted(load)
</script>

<style scoped>
.cell-input {
  @apply w-full bg-transparent border border-transparent rounded px-2 py-1 text-sm
    focus:outline-none focus:border-indigo-400 focus:bg-white dark:focus:bg-gray-700
    hover:border-gray-300 dark:hover:border-gray-500
    transition-colors;
}
.label { @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1; }
.input { @apply w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500; }
.btn-primary { @apply px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
.btn-secondary { @apply px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors; }
.btn-danger { @apply px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
</style>
