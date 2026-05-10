<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-semibold">Import</h1>

    <!-- Tab switcher -->
    <div class="flex gap-1 border-b border-gray-200 dark:border-gray-700">
      <button
        v-for="t in tabs" :key="t.id"
        @click="switchTab(t.id)"
        class="px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px"
        :class="activeTab === t.id
          ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
      >{{ t.label }}</button>
    </div>

    <!-- MT940 tab -->
    <template v-if="activeTab === 'mt940'">
      <div
        class="border-2 border-dashed rounded-xl p-8 text-center transition-colors"
        :class="dragging
          ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-600'"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
      >
        <input ref="mt940Input" type="file" accept=".sta,.mt940,.txt" class="hidden" @change="onMt940Selected" />
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-3">MT940-Datei hier ablegen oder</p>
        <button @click="mt940Input.click()" class="btn-primary" :disabled="uploading">
          {{ uploading ? 'Wird importiert…' : 'Datei auswählen' }}
        </button>
      </div>
    </template>

    <!-- CAMT.053 tab -->
    <template v-if="activeTab === 'camt053'">
      <div
        class="border-2 border-dashed rounded-xl p-8 text-center transition-colors"
        :class="camt053Dragging
          ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-600'"
        @dragover.prevent="camt053Dragging = true"
        @dragleave.prevent="camt053Dragging = false"
        @drop.prevent="onCamt053Drop"
      >
        <input ref="camt053Input" type="file" accept=".xml,.camt,.camt053" class="hidden" @change="onCamt053Selected" />
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-3">CAMT.053-Datei (XML) hier ablegen oder</p>
        <button @click="camt053Input.click()" class="btn-primary" :disabled="uploading">
          {{ uploading ? 'Wird importiert…' : 'Datei auswählen' }}
        </button>
      </div>
    </template>

    <!-- CSV tab -->
    <template v-if="activeTab === 'csv'">
      <!-- Step 1: file selection -->
      <div v-if="!csvPreview"
        class="border-2 border-dashed rounded-xl p-8 text-center transition-colors border-gray-300 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-600"
      >
        <input ref="csvInput" type="file" accept=".csv,.txt" class="hidden" @change="onCsvSelected" />
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-3">CSV-Datei auswählen</p>
        <button @click="csvInput.click()" class="btn-primary">Datei auswählen</button>
      </div>

      <!-- Step 2: column mapping -->
      <div v-else class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Spalten zuordnen</h2>
          <button @click="resetCsv" class="text-xs text-gray-400 hover:text-gray-600">Andere Datei</button>
        </div>

        <!-- Preview table -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
          <table class="text-xs border-collapse">
            <thead>
              <tr>
                <th v-for="(h, i) in csvPreview.headers" :key="i"
                  class="px-3 py-2 text-left font-mono text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 whitespace-nowrap">
                  <span class="text-gray-400">#{{ i }}</span> {{ h }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in csvPreview.rows" :key="ri"
                class="border-b border-gray-100 dark:border-gray-700/50">
                <td v-for="(cell, ci) in row" :key="ci"
                  class="px-3 py-1.5 text-gray-600 dark:text-gray-300 whitespace-nowrap max-w-xs truncate"
                  :class="{
                    'bg-blue-50 dark:bg-blue-900/20': csvMapping.date_col === ci,
                    'bg-green-50 dark:bg-green-900/20': csvMapping.amount_col === ci,
                    'bg-purple-50 dark:bg-purple-900/20': csvMapping.description_col === ci,
                  }">
                  {{ cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mapping controls -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label class="label"><span class="inline-block w-3 h-3 bg-blue-200 dark:bg-blue-800 rounded-sm mr-1"></span>Datum</label>
              <select v-model.number="csvMapping.date_col" class="input text-sm">
                <option v-for="(h, i) in csvPreview.headers" :key="i" :value="i">#{{ i }} {{ h }}</option>
              </select>
            </div>
            <div>
              <label class="label"><span class="inline-block w-3 h-3 bg-green-200 dark:bg-green-800 rounded-sm mr-1"></span>Betrag</label>
              <select v-model.number="csvMapping.amount_col" class="input text-sm">
                <option v-for="(h, i) in csvPreview.headers" :key="i" :value="i">#{{ i }} {{ h }}</option>
              </select>
            </div>
            <div>
              <label class="label"><span class="inline-block w-3 h-3 bg-purple-200 dark:bg-purple-800 rounded-sm mr-1"></span>Beschreibung</label>
              <select v-model="csvMapping.description_col" class="input text-sm">
                <option :value="null">— keine —</option>
                <option v-for="(h, i) in csvPreview.headers" :key="i" :value="i">#{{ i }} {{ h }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 border-t border-gray-100 dark:border-gray-700">
            <div>
              <label class="label">Festkonto (optional)</label>
              <select v-model="csvMapping.account_id" class="input text-sm">
                <option :value="null">— kein Festkonto —</option>
                <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
              </select>
            </div>
            <div v-if="csvMapping.account_id" class="flex items-end pb-1">
              <label class="flex items-center gap-2 cursor-pointer text-sm">
                <input v-model="csvMapping.account_on_credit_side" type="checkbox" class="w-4 h-4 accent-indigo-600" />
                <span>Positiver Betrag = Habenkonto<br><span class="text-xs text-gray-400">(z.B. Kreditkarte)</span></span>
              </label>
            </div>
          </div>

          <div class="flex justify-end pt-1">
            <button @click="uploadCsv" :disabled="uploading" class="btn-primary">
              {{ uploading ? 'Wird importiert…' : 'Importieren' }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Error / result (common) -->
    <div v-if="uploadError" class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
      {{ uploadError }}
    </div>

    <div v-if="importResult && importResult.created === 0"
      class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg px-4 py-3 text-sm text-yellow-800 dark:text-yellow-300">
      <span class="font-semibold">Keine Buchungen gefunden.</span>
      <template v-if="importResult.skipped"> {{ importResult.skipped }} bereits importierte Buchungen übersprungen.</template>
    </div>
    <div v-else-if="importResult" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-4 py-3 text-sm text-green-800 dark:text-green-300">
      <span class="font-semibold">Import erfolgreich:</span>
      {{ importResult.created }} neue Buchungen
      <template v-if="importResult.skipped"> · {{ importResult.skipped }} Duplikate übersprungen</template>
      <template v-if="importResult.bank_account_name"> · Konto: {{ importResult.bank_account_name }}</template>
      <template v-else-if="importResult.account_name"> · Konto: {{ importResult.account_name }}</template>
      <template v-else-if="importResult.iban"> · IBAN {{ importResult.iban }} nicht gefunden — bitte IBAN im Kontenplan hinterlegen</template>
    </div>

    <!-- Suggested transactions (common) -->
    <template v-if="currentDocId">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-lg">{{ pendingCount > 0 ? 'Vorschläge zuweisen' : 'Buchungen' }}</h2>
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ pendingCount }} von {{ suggestions.length }} noch offen
          </span>
          <button
            v-if="suggestions.some(t => t.status === 'suggested')"
            @click="bookAll"
            :disabled="pendingCount > 0 || booking"
            class="btn-primary text-sm"
          >
            {{ booking ? 'Wird gebucht…' : 'Alle buchen' }}
          </button>
        </div>
      </div>

      <div v-if="bookError" class="text-red-500 text-sm">{{ bookError }}</div>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
        <table class="w-full text-sm border-collapse">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wide">
              <th class="text-left px-3 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Datum</th>
              <th class="text-left px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Beschreibung</th>
              <th class="text-left px-3 py-2.5 w-52 border-b border-gray-200 dark:border-gray-700">Soll</th>
              <th class="text-left px-3 py-2.5 w-52 border-b border-gray-200 dark:border-gray-700">Haben</th>
              <th class="text-right px-3 py-2.5 w-28 border-b border-gray-200 dark:border-gray-700">Betrag</th>
              <th class="w-8 border-b border-gray-200 dark:border-gray-700"></th>
              <th class="w-16 border-b border-gray-200 dark:border-gray-700"></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="row in displayRows" :key="row.type === 'normal' ? `t-${row.tx.id}` : row.type === 'split-header' ? `gh-${row.group_id}` : `gl-${row.tx.id}`">
              <!-- Normal transaction -->
              <tr v-if="row.type === 'normal'"
                class="border-b border-gray-100 dark:border-gray-700/50"
                :class="isComplete(row.tx) ? '' : 'bg-amber-50/40 dark:bg-amber-900/10'"
              >
                <td class="px-3 py-2 font-mono text-xs text-gray-500 dark:text-gray-400">{{ fmtDate(row.tx.date) }}</td>
                <td class="px-3 py-2 text-gray-700 dark:text-gray-300 text-xs">
                  <div>{{ row.tx.description || row.tx.reference || '—' }}</div>
                  <div v-if="row.tx.counterparty" class="text-gray-400 mt-0.5">{{ row.tx.counterparty }}</div>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span v-if="row.tx.rule" class="inline-flex items-center gap-1 text-violet-600 dark:text-violet-400">
                      <svg class="w-3 h-3 flex-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                      {{ row.tx.rule.name }}
                    </span>
                    <button v-if="row.tx.description" type="button" @click="openRuleModal(row.tx)"
                      class="text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-300 transition-colors">
                      + Regel
                    </button>
                  </div>
                </td>
                <td class="px-2 py-1">
                  <div class="flex items-center gap-0.5">
                    <select v-model="row.tx.debit_account_id" @change="saveAccount(row.tx, 'debit')" class="cell-input text-xs flex-1">
                      <option value="">— Sollkonto —</option>
                      <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
                    </select>
                    <button type="button" @click="openAccountModal(row.tx, 'debit')"
                      class="flex-none text-gray-400 hover:text-indigo-500 transition-colors px-1 text-base leading-none" title="Neues Konto anlegen">+</button>
                  </div>
                </td>
                <td class="px-2 py-1">
                  <div class="flex items-center gap-0.5">
                    <select v-model="row.tx.credit_account_id" @change="saveAccount(row.tx, 'credit')" class="cell-input text-xs flex-1">
                      <option value="">— Habenkonto —</option>
                      <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
                    </select>
                    <button type="button" @click="openAccountModal(row.tx, 'credit')"
                      class="flex-none text-gray-400 hover:text-indigo-500 transition-colors px-1 text-base leading-none" title="Neues Konto anlegen">+</button>
                  </div>
                </td>
                <td class="px-3 py-2 text-right font-mono text-gray-800 dark:text-gray-200">{{ fmt(row.tx.amount) }}</td>
                <td class="px-2 py-1 text-center">
                  <span v-if="isComplete(row.tx)" class="text-green-500 text-xs">✓</span>
                  <span v-else class="text-amber-400 text-xs">○</span>
                </td>
                <td class="px-2 py-1 text-center">
                  <button @click="openImportSplit(row.tx)" class="text-violet-500 hover:text-violet-700 text-xs border border-violet-300 dark:border-violet-700 rounded px-1 py-0.5" title="Als Splittbuchung erfassen">Split</button>
                </td>
              </tr>

              <!-- Split group header -->
              <tr v-else-if="row.type === 'split-header'"
                class="border-b border-gray-100 dark:border-gray-700/50 bg-violet-50/30 dark:bg-violet-900/10"
              >
                <td class="px-3 py-2 font-mono text-xs text-gray-500 dark:text-gray-400">{{ fmtDate(row.date) }}</td>
                <td class="px-3 py-2 text-xs text-violet-700 dark:text-violet-400 font-medium">
                  Split · {{ row.lines_count }} Zeilen<template v-if="row.group_description"> · {{ row.group_description }}</template>
                </td>
                <td class="px-3 py-2 text-xs text-gray-400">—</td>
                <td class="px-2 py-1">
                  <div class="flex items-center gap-0.5">
                    <select :value="row.credit_account_id" @change="updateSplitCreditAccount(row.group_id, $event.target.value)" class="cell-input text-xs flex-1">
                      <option value="">— Habenkonto —</option>
                      <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
                    </select>
                    <button type="button" @click="accountModalOpen = true; modalContext = null"
                      class="flex-none text-gray-400 hover:text-indigo-500 transition-colors px-1 text-base leading-none" title="Neues Konto anlegen">+</button>
                  </div>
                </td>
                <td class="px-3 py-2 text-right font-mono font-semibold text-gray-700 dark:text-gray-300">{{ fmt(row.total) }}</td>
                <td class="px-2 py-1 text-center">
                  <span v-if="row.all_complete" class="text-green-500 text-xs">✓</span>
                  <span v-else class="text-amber-400 text-xs">○</span>
                </td>
                <td></td>
              </tr>

              <!-- Split line -->
              <tr v-else-if="row.type === 'split-line'"
                class="border-b border-gray-100 dark:border-gray-700/50 bg-violet-50/10 dark:bg-violet-900/5"
              >
                <td class="px-3 py-2 text-xs text-gray-400 pl-8">└</td>
                <td class="px-3 py-2 text-gray-600 dark:text-gray-400 text-xs">{{ row.tx.description || '—' }}</td>
                <td class="px-2 py-1">
                  <select v-model="row.tx.debit_account_id" @change="saveAccount(row.tx, 'debit')" class="cell-input text-xs">
                    <option value="">— Sollkonto —</option>
                    <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
                  </select>
                </td>
                <td class="px-3 py-2 text-xs text-gray-400">—</td>
                <td class="px-3 py-2 text-right font-mono text-gray-600 dark:text-gray-300">{{ fmt(row.tx.amount) }}</td>
                <td class="px-2 py-1 text-center">
                  <span v-if="isComplete(row.tx)" class="text-green-500 text-xs">✓</span>
                  <span v-else class="text-amber-400 text-xs">○</span>
                </td>
                <td></td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Past documents -->
    <template v-if="documents.length">
      <h2 class="font-semibold text-lg pt-2">Frühere Importe</h2>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <table class="w-full text-sm border-collapse">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wide">
              <th class="text-left px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Datum</th>
              <th class="text-left px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Datei</th>
              <th class="text-left px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Status</th>
              <th class="text-right px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Buchungen</th>
              <th class="text-right px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">Summe</th>
              <th class="w-24 border-b border-gray-200 dark:border-gray-700"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in documents" :key="doc.id" class="border-b border-gray-100 dark:border-gray-700/50">
              <td class="px-3 py-2 text-gray-500 dark:text-gray-400 text-xs font-mono">{{ fmtDateTime(doc.received_at) }}</td>
              <td class="px-3 py-2 text-gray-600 dark:text-gray-300 text-xs">
                <span v-if="doc.original_file" class="font-medium">{{ doc.original_file }}</span>
                <span v-else class="uppercase text-gray-400">{{ sourceLabel(doc.source) }}</span>
              </td>
              <td class="px-3 py-2">
                <span
                  class="px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="{
                    'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400': doc.status === 'pending',
                    'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400': doc.status === 'booked',
                    'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400': doc.status === 'error',
                  }"
                >{{ doc.status }}</span>
              </td>
              <td class="px-3 py-2 text-right text-gray-500 dark:text-gray-400 text-xs">
                {{ doc.transaction_count }}
                <span v-if="doc.suggested_count" class="text-amber-500"> ({{ doc.suggested_count }} offen)</span>
              </td>
              <td class="px-3 py-2 text-right font-mono text-xs text-gray-600 dark:text-gray-300">{{ fmt(doc.total_amount) }}</td>
              <td class="px-3 py-2 text-center flex items-center justify-center gap-3">
                <button
                  @click="loadDocument(doc.id)"
                  class="text-xs underline"
                  :class="doc.suggested_count > 0 ? 'text-indigo-500 hover:text-indigo-700' : 'text-gray-400 hover:text-gray-600'"
                >{{ doc.suggested_count > 0 ? 'Bearbeiten' : 'Anzeigen' }}</button>
                <button
                  v-if="doc.status !== 'booked'"
                  @click="confirmDeleteDoc(doc)"
                  class="text-xs text-red-400 hover:text-red-600"
                  title="Import löschen"
                >Löschen</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  <!-- Lösch-Bestätigung Import -->
  <div v-if="deleteDocTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="deleteDocTarget = null">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
      <h2 class="font-semibold text-lg">Import löschen?</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        <strong>{{ deleteDocTarget.original_file || deleteDocTarget.source.toUpperCase() }}</strong> vom {{ fmtDateTime(deleteDocTarget.received_at) }} und alle {{ deleteDocTarget.transaction_count }} zugehörigen Buchungen werden gelöscht.
      </p>
      <div v-if="deleteDocError" class="text-red-500 text-sm">{{ deleteDocError }}</div>
      <div class="flex justify-end gap-3">
        <button @click="deleteDocTarget = null" class="btn-secondary">Abbrechen</button>
        <button @click="doDeleteDoc" :disabled="deletingDoc" class="btn-danger">{{ deletingDoc ? 'Löschen…' : 'Löschen' }}</button>
      </div>
    </div>
  </div>

  <!-- Account / Rule Modals -->
  <AccountModal v-model="accountModalOpen" :accounts="accounts" @saved="onAccountSaved" />
  <RuleModal v-model="ruleModalOpen" :accounts="accounts" :prefill="rulePrefill" @saved="onRuleSaved" />

  <!-- Import Split Modal -->
  <div v-if="importSplitModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="importSplitModal = false">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl p-6 space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-lg">Splittbuchung erfassen</h2>
        <button @click="importSplitModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</button>
      </div>

      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="label">Datum</label>
          <input v-model="importSplitForm.date" type="date" class="input" />
        </div>
        <div>
          <label class="label">Beleg-Nr.</label>
          <input v-model="importSplitForm.reference" type="text" class="input" placeholder="—" />
        </div>
        <div>
          <label class="label">Beschreibung</label>
          <input v-model="importSplitForm.description" type="text" class="input" placeholder="z.B. Coop" />
        </div>
      </div>
      <div>
        <label class="label">Habenkonto (Zahlung) *</label>
        <select v-model="importSplitForm.credit_account_id" class="input">
          <option value="">— Konto wählen —</option>
          <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
        </select>
      </div>

      <div>
        <div class="flex items-center justify-between mb-1">
          <div class="grid grid-cols-12 gap-2 w-full px-0.5">
            <div class="col-span-5 text-xs text-gray-400 uppercase tracking-wide">Sollkonto *</div>
            <div class="col-span-4 text-xs text-gray-400 uppercase tracking-wide">Beschreibung *</div>
            <div class="col-span-2 text-xs text-gray-400 uppercase tracking-wide text-right">Betrag *</div>
            <div class="col-span-1"></div>
          </div>
        </div>
        <div class="space-y-2">
          <div v-for="(line, i) in importSplitForm.lines" :key="i" class="grid grid-cols-12 gap-2 items-center">
            <div class="col-span-5">
              <div class="flex items-center gap-0.5">
                <select v-model="line.debit_account_id" class="input text-sm flex-1">
                  <option value="">— Sollkonto —</option>
                  <option v-for="a in bookableAccounts" :key="a.id" :value="a.id">{{ a.number }} {{ a.name }}</option>
                </select>
                <button type="button" @click="accountModalOpen = true; modalContext = null"
                  class="flex-none text-gray-400 hover:text-indigo-500 transition-colors px-1.5 text-base" title="Neues Konto anlegen">+</button>
              </div>
            </div>
            <div class="col-span-4">
              <input v-model="line.description" type="text" class="input text-sm" placeholder="Beschreibung *" />
            </div>
            <div class="col-span-2">
              <input v-model="line.amount" type="number" step="0.01" min="0.01" class="input text-sm text-right" placeholder="0.00" @blur="line.amount = fmtInput(line.amount)" />
            </div>
            <div class="col-span-1 text-center">
              <button v-if="importSplitForm.lines.length > 2" @click="importSplitForm.lines.splice(i,1)" class="text-gray-400 hover:text-red-500">✕</button>
            </div>
          </div>
        </div>
        <div class="mt-2 flex items-center justify-between text-sm">
          <button @click="importSplitForm.lines.push({ debit_account_id: '', description: '', amount: '' })" class="text-indigo-600 hover:text-indigo-700 font-medium">+ Zeile</button>
          <div class="flex gap-4">
            <span class="text-gray-400">Original: <span class="font-mono">{{ fmt(importSplitOriginalAmount) }}</span></span>
            <span class="text-gray-500">Total: <span class="font-mono font-semibold" :class="importSplitTotal === importSplitOriginalAmount ? 'text-green-600 dark:text-green-400' : 'text-gray-700'">{{ fmt(importSplitTotal) }}</span></span>
          </div>
        </div>
      </div>

      <div v-if="importSplitError" class="text-red-500 text-sm">{{ importSplitError }}</div>

      <div class="flex justify-end gap-3 pt-2">
        <button @click="importSplitModal = false" class="btn-secondary">Abbrechen</button>
        <button @click="saveImportSplit" :disabled="savingImportSplit" class="btn-primary">{{ savingImportSplit ? 'Speichern…' : 'Speichern' }}</button>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetch } from '../api.js'
import AccountModal from '../components/AccountModal.vue'
import RuleModal from '../components/RuleModal.vue'

const tabs = [
  { id: 'mt940', label: 'MT940' },
  { id: 'camt053', label: 'CAMT.053' },
  { id: 'csv', label: 'CSV' },
]
const activeTab = ref('mt940')

// MT940
const mt940Input = ref(null)
const dragging = ref(false)

// CAMT.053
const camt053Input = ref(null)
const camt053Dragging = ref(false)

// CSV
const csvInput = ref(null)
const csvPreview = ref(null)
const csvFile = ref(null)
const csvMapping = ref({ date_col: 0, amount_col: 1, description_col: null, account_id: null, account_on_credit_side: false })

// Common
const uploading = ref(false)
const uploadError = ref(null)
const importResult = ref(null)
const accounts = ref([])
const suggestions = ref([])
const documents = ref([])
const currentDocId = ref(null)
const booking = ref(false)
const bookError = ref(null)

// Account & Rule modals
const accountModalOpen = ref(false)
const ruleModalOpen = ref(false)
const modalContext = ref(null)
const rulePrefill = ref(null)

function openAccountModal(tx, side) {
  modalContext.value = { tx, side }
  accountModalOpen.value = true
}

function openRuleModal(tx) {
  rulePrefill.value = tx.description
    ? { conditions: [{ field: 'description', operator: 'contains', value: tx.description }] }
    : null
  ruleModalOpen.value = true
}

async function onRuleSaved() {
  await apiFetch('/api/rules/apply', { method: 'POST' })
  if (currentDocId.value) await loadDocument(currentDocId.value)
}

async function onAccountSaved(newAccount) {
  accounts.value = [...accounts.value, newAccount]
  if (modalContext.value) {
    const { tx, side } = modalContext.value
    tx[side + '_account_id'] = newAccount.id
    await saveAccount(tx, side)
    modalContext.value = null
  }
}

// Delete document
const deleteDocTarget = ref(null)
const deleteDocError = ref(null)
const deletingDoc = ref(false)

function confirmDeleteDoc(doc) { deleteDocTarget.value = doc; deleteDocError.value = null }
async function doDeleteDoc() {
  deletingDoc.value = true; deleteDocError.value = null
  try {
    const res = await apiFetch(`/api/documents/${deleteDocTarget.value.id}`, { method: 'DELETE' })
    if (!res.ok) { const d = await res.json().catch(() => ({})); deleteDocError.value = d.detail ?? 'Fehler.'; return }
    if (currentDocId.value === deleteDocTarget.value.id) { currentDocId.value = null; suggestions.value = [] }
    deleteDocTarget.value = null
    await loadDocuments()
  } finally { deletingDoc.value = false }
}

// Import Split
const importSplitModal = ref(false)
const savingImportSplit = ref(false)
const importSplitError = ref(null)
const importSplitSourceId = ref(null)
const importSplitOriginalAmount = ref(0)
const importSplitForm = ref({ date: '', reference: '', description: '', credit_account_id: '', lines: [] })
const importSplitTotal = computed(() => importSplitForm.value.lines.reduce((s, l) => s + (parseFloat(l.amount) || 0), 0))

const bookableAccounts = computed(() =>
  [...accounts.value]
    .filter(a => !a.is_group && a.active)
    .sort((a, b) => a.number.localeCompare(b.number))
)

const pendingCount = computed(() => suggestions.value.filter(t => !isComplete(t)).length)

const displayRows = computed(() => {
  const rows = []
  const handled = new Set()
  for (const t of suggestions.value) {
    if (t.group_id != null) {
      if (!handled.has(t.group_id)) {
        handled.add(t.group_id)
        const group = suggestions.value.filter(s => s.group_id === t.group_id)
        rows.push({
          type: 'split-header',
          group_id: t.group_id,
          date: t.date,
          group_description: t.group_description,
          credit_account_id: t.credit_account_id,
          total: group.reduce((s, l) => s + parseFloat(l.amount), 0),
          lines_count: group.length,
          all_complete: group.every(s => isComplete(s)),
        })
        group.forEach(line => rows.push({ type: 'split-line', tx: line }))
      }
    } else {
      rows.push({ type: 'normal', tx: t })
    }
  }
  return rows
})

const fmt = (val) =>
  new Intl.NumberFormat('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parseFloat(val) || 0)

const fmtDate = (d) => {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${(day ?? '').padStart(2, '0')}.${(m ?? '').padStart(2, '0')}.${y}`
}

const fmtDateTime = (s) => {
  if (!s) return ''
  const d = new Date(s)
  return `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const sourceLabel = (s) => ({ mt940: 'MT940', camt053: 'CAMT.053', csv: 'CSV' }[s] ?? s.toUpperCase())

function isComplete(t) {
  return !!(t.debit_account_id && t.credit_account_id)
}

const fmtInput = (val) => val && !isNaN(parseFloat(val)) ? parseFloat(val).toFixed(2) : val

async function updateSplitCreditAccount(groupId, accountIdStr) {
  const accountId = accountIdStr ? parseInt(accountIdStr) : null
  const lines = suggestions.value.filter(t => t.group_id === groupId)
  for (const t of lines) {
    t.credit_account_id = accountId
    await apiFetch(`/api/transactions/${t.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_account_id: accountId }),
    })
  }
}

function openImportSplit(t) {
  importSplitSourceId.value = t.id
  importSplitOriginalAmount.value = parseFloat(t.amount)
  importSplitForm.value = {
    date: t.date,
    reference: t.reference || '',
    description: t.description || '',
    credit_account_id: t.credit_account_id || '',
    lines: [
      { debit_account_id: t.debit_account_id || '', description: '', amount: '' },
      { debit_account_id: '', description: '', amount: '' },
    ]
  }
  importSplitError.value = null
  importSplitModal.value = true
}

async function saveImportSplit() {
  importSplitError.value = null
  const f = importSplitForm.value
  if (!f.date) { importSplitError.value = 'Datum fehlt.'; return }
  if (!f.credit_account_id) { importSplitError.value = 'Habenkonto fehlt.'; return }
  for (const l of f.lines) {
    if (!l.debit_account_id) { importSplitError.value = 'Alle Sollkonten ausfüllen.'; return }
    if (!l.description) { importSplitError.value = 'Alle Beschreibungen ausfüllen.'; return }
    if (!l.amount || parseFloat(l.amount) <= 0) { importSplitError.value = 'Alle Beträge ausfüllen.'; return }
  }
  if (Math.abs(importSplitTotal.value - importSplitOriginalAmount.value) > 0.005) {
    importSplitError.value = `Summe (${fmt(importSplitTotal.value)}) muss dem Originalbetrag (${fmt(importSplitOriginalAmount.value)}) entsprechen.`
    return
  }
  savingImportSplit.value = true
  try {
    const body = {
      date: f.date,
      reference: f.reference || null,
      description: f.description || null,
      credit_account_id: f.credit_account_id,
      lines: f.lines.map(l => ({ debit_account_id: l.debit_account_id, description: l.description, amount: parseFloat(l.amount) }))
    }
    const res = await apiFetch(`/api/transactions/${importSplitSourceId.value}/split`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!res.ok) { const d = await res.json().catch(() => ({})); importSplitError.value = d.detail ?? 'Fehler.'; return }
    importSplitModal.value = false
    await loadDocument(currentDocId.value)
  } finally { savingImportSplit.value = false }
}

function switchTab(tab) {
  activeTab.value = tab
  uploadError.value = null
  importResult.value = null
}

// --- CSV preview parsing ---
function detectDelimiter(text) {
  const first = text.split('\n')[0]
  const scores = { ';': (first.match(/;/g) || []).length, ',': (first.match(/,/g) || []).length, '\t': (first.match(/\t/g) || []).length }
  return Object.entries(scores).sort((a, b) => b[1] - a[1])[0][0]
}

function parseCsvLine(line, delim) {
  const result = []
  let inQuote = false, current = ''
  for (const ch of line) {
    if (ch === '"') { inQuote = !inQuote }
    else if (ch === delim && !inQuote) { result.push(current.trim()); current = '' }
    else { current += ch }
  }
  result.push(current.trim())
  return result
}

function guessColumns(headers) {
  const lower = headers.map(h => h.toLowerCase())
  const find = (...keys) => {
    for (const key of keys) {
      const i = lower.findIndex(h => h.includes(key))
      if (i !== -1) return i
    }
    return null
  }
  return {
    date_col: find('datum', 'date', 'dat', 'buchungsdatum') ?? 0,
    amount_col: find('betrag', 'amount', 'chf', 'eur', 'usd', 'summe') ?? 1,
    description_col: find('beschreibung', 'text', 'zweck', 'verwendung', 'name', 'merchant', 'detail') ?? null,
  }
}

function onCsvSelected(e) {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return
  csvFile.value = file
  uploadError.value = null
  const reader = new FileReader()
  reader.onload = (ev) => {
    const text = ev.target.result
    const delim = detectDelimiter(text)
    const lines = text.split(/\r?\n/).filter(l => l.trim())
    if (lines.length < 2) { uploadError.value = 'CSV hat keine Daten.'; return }
    const headers = parseCsvLine(lines[0], delim)
    const rows = lines.slice(1, 5).map(l => parseCsvLine(l, delim))
    csvPreview.value = { headers, rows, delimiter: delim }
    const guessed = guessColumns(headers)
    csvMapping.value = { ...csvMapping.value, ...guessed }
  }
  reader.readAsText(file, 'utf-8')
}

function resetCsv() {
  csvPreview.value = null
  csvFile.value = null
  uploadError.value = null
  importResult.value = null
}

function resetCsvPreview() {
  csvPreview.value = null
  csvFile.value = null
}

async function uploadCsv() {
  if (!csvFile.value) return
  uploading.value = true
  uploadError.value = null
  importResult.value = null
  try {
    const form = new FormData()
    form.append('file', csvFile.value)
    form.append('date_col', csvMapping.value.date_col)
    form.append('amount_col', csvMapping.value.amount_col)
    if (csvMapping.value.description_col !== null) form.append('description_col', csvMapping.value.description_col)
    if (csvMapping.value.account_id) form.append('account_id', csvMapping.value.account_id)
    form.append('account_on_credit_side', csvMapping.value.account_on_credit_side)
    const res = await apiFetch('/api/documents/csv', { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok) { uploadError.value = data.detail ?? 'Import fehlgeschlagen.'; return }
    importResult.value = data
    resetCsvPreview()
    if (data.document_id) {
      await loadDocument(data.document_id)
      await loadDocuments()
    }
  } catch {
    uploadError.value = 'Netzwerkfehler.'
  } finally {
    uploading.value = false
  }
}

// --- CAMT.053 ---
async function processCamt053(file) {
  if (!file) return
  uploading.value = true
  uploadError.value = null
  importResult.value = null
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await apiFetch('/api/documents/camt053', { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok) { uploadError.value = data.detail ?? 'Import fehlgeschlagen.'; return }
    importResult.value = data
    if (data.document_id) {
      await loadDocument(data.document_id)
      await loadDocuments()
    }
  } catch {
    uploadError.value = 'Netzwerkfehler.'
  } finally {
    uploading.value = false
  }
}

function onCamt053Drop(e) {
  camt053Dragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) processCamt053(file)
}

function onCamt053Selected(e) {
  const file = e.target.files[0]
  if (file) processCamt053(file)
  e.target.value = ''
}

// --- MT940 ---
async function processMt940(file) {
  if (!file) return
  uploading.value = true
  uploadError.value = null
  importResult.value = null
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await apiFetch('/api/documents/mt940', { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok) { uploadError.value = data.detail ?? 'Import fehlgeschlagen.'; return }
    importResult.value = data
    if (data.document_id) {
      await loadDocument(data.document_id)
      await loadDocuments()
    }
  } catch {
    uploadError.value = 'Netzwerkfehler.'
  } finally {
    uploading.value = false
  }
}

function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) processMt940(file)
}

function onMt940Selected(e) {
  const file = e.target.files[0]
  if (file) processMt940(file)
  e.target.value = ''
}

// --- Common ---
async function loadAccounts() {
  const res = await apiFetch('/api/accounts')
  if (res.ok) accounts.value = await res.json()
}

async function loadDocuments() {
  const res = await apiFetch('/api/documents')
  if (res.ok) documents.value = await res.json()
}

async function loadDocument(docId) {
  currentDocId.value = docId
  bookError.value = null
  const res = await apiFetch(`/api/documents/${docId}/transactions`)
  if (res.ok) suggestions.value = await res.json()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function saveAccount(t, side) {
  const body = side === 'debit'
    ? { debit_account_id: t.debit_account_id || null }
    : { credit_account_id: t.credit_account_id || null }
  const res = await apiFetch(`/api/transactions/${t.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (res.ok) {
    const updated = await res.json()
    const idx = suggestions.value.findIndex(s => s.id === t.id)
    if (idx !== -1) suggestions.value[idx] = updated
  }
}

async function bookAll() {
  booking.value = true
  bookError.value = null
  try {
    const res = await apiFetch(`/api/documents/${currentDocId.value}/book`, { method: 'POST' })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) { bookError.value = data.detail ?? 'Fehler beim Buchen.'; return }
    importResult.value = null
    currentDocId.value = null
    suggestions.value = []
    await loadDocuments()
  } finally {
    booking.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadAccounts(), loadDocuments()])
})
</script>

<style scoped>
.label { @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1; }
.input { @apply w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500; }
.cell-input {
  @apply w-full bg-transparent border border-gray-200 dark:border-gray-600 rounded px-2 py-1
    focus:outline-none focus:border-indigo-400 focus:bg-white dark:focus:bg-gray-700
    hover:border-gray-300 dark:hover:border-gray-500
    transition-colors;
}
.btn-primary {
  @apply px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn-secondary { @apply px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors; }
.btn-danger { @apply px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors disabled:opacity-50; }
</style>
