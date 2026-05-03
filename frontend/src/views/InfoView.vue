<template>
  <div class="space-y-6 max-w-2xl">
    <div>
      <h1 class="text-2xl font-semibold">Über OverBudget</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        Persönliche Buchhaltung nach dem doppelten Buchführungsprinzip
      </p>
    </div>

    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-2">
      <div class="flex items-baseline gap-3">
        <span class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">OverBudget</span>
        <span class="text-sm text-gray-400 dark:text-gray-500">v0.1.0</span>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-300">
        Self-hosted Finanzsoftware für Privatpersonen. Unterstützt MT940-Import, CSV-Import,
        automatische Buchungsregeln, Budgetverfolgung und verschlüsselte Backups.
      </p>
    </div>

    <!-- Frontend -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="px-5 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
        <span class="font-semibold text-sm text-gray-700 dark:text-gray-200">Frontend</span>
      </div>
      <table class="w-full text-sm">
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
          <tr v-for="lib in frontend" :key="lib.name" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
            <td class="px-5 py-2.5 font-medium text-gray-800 dark:text-gray-200 w-48">{{ lib.name }}</td>
            <td class="px-3 py-2.5 font-mono text-xs text-gray-400 dark:text-gray-500 w-20">{{ lib.version }}</td>
            <td class="px-3 py-2.5 text-gray-500 dark:text-gray-400 flex-1">{{ lib.desc }}</td>
            <td class="px-5 py-2.5 text-right">
              <span class="text-xs bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded-full font-mono">{{ lib.license }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Backend -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="px-5 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
        <span class="font-semibold text-sm text-gray-700 dark:text-gray-200">Backend</span>
      </div>
      <table class="w-full text-sm">
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
          <tr v-for="lib in backend" :key="lib.name" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
            <td class="px-5 py-2.5 font-medium text-gray-800 dark:text-gray-200 w-48">{{ lib.name }}</td>
            <td class="px-3 py-2.5 font-mono text-xs text-gray-400 dark:text-gray-500 w-20">{{ lib.version }}</td>
            <td class="px-3 py-2.5 text-gray-500 dark:text-gray-400 flex-1">{{ lib.desc }}</td>
            <td class="px-5 py-2.5 text-right">
              <span class="text-xs bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded-full font-mono">{{ lib.license }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Infrastruktur -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="px-5 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
        <span class="font-semibold text-sm text-gray-700 dark:text-gray-200">Infrastruktur</span>
      </div>
      <table class="w-full text-sm">
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
          <tr v-for="lib in infra" :key="lib.name" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
            <td class="px-5 py-2.5 font-medium text-gray-800 dark:text-gray-200 w-48">{{ lib.name }}</td>
            <td class="px-3 py-2.5 font-mono text-xs text-gray-400 dark:text-gray-500 w-20">{{ lib.version }}</td>
            <td class="px-3 py-2.5 text-gray-500 dark:text-gray-400 flex-1">{{ lib.desc }}</td>
            <td class="px-5 py-2.5 text-right">
              <span class="text-xs bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded-full font-mono">{{ lib.license }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="text-xs text-gray-400 dark:text-gray-500 text-center pb-2">
      OverBudget verwendet ausschliesslich Open-Source-Software.
    </p>
  </div>
</template>

<script setup>
const frontend = [
  { name: 'Vue 3',        version: '3.5',  license: 'MIT',     desc: 'Reaktives UI-Framework' },
  { name: 'Vue Router',   version: '4.4',  license: 'MIT',     desc: 'Client-seitiges Routing' },
  { name: 'Pinia',        version: '2.2',  license: 'MIT',     desc: 'State Management' },
  { name: 'Vite',         version: '6.0',  license: 'MIT',     desc: 'Build-Tool und Dev-Server' },
  { name: 'Tailwind CSS', version: '3.4',  license: 'MIT',     desc: 'Utility-first CSS-Framework' },
]

const backend = [
  { name: 'FastAPI',            version: '0.115', license: 'MIT',        desc: 'Modernes Python-Web-Framework' },
  { name: 'Uvicorn',            version: '0.30',  license: 'BSD-3',      desc: 'ASGI-Server' },
  { name: 'SQLAlchemy',         version: '2.0',   license: 'MIT',        desc: 'ORM und Datenbankabstraktion' },
  { name: 'Alembic',            version: '1.13',  license: 'MIT',        desc: 'Datenbank-Migrationen' },
  { name: 'PyMySQL',            version: '1.1',   license: 'MIT',        desc: 'MySQL/MariaDB-Treiber' },
  { name: 'Celery',             version: '5.4',   license: 'BSD-3',      desc: 'Asynchrone Task-Queue' },
  { name: 'redis-py',           version: '5.1',   license: 'MIT',        desc: 'Redis-Client' },
  { name: 'python-jose',        version: '3.3',   license: 'MIT',        desc: 'JWT-Authentifizierung' },
  { name: 'passlib',            version: '1.7',   license: 'BSD-2',      desc: 'Passwort-Hashing' },
  { name: 'mt-940',             version: '≥4.30', license: 'MIT',        desc: 'MT940-Kontoauszüge parsen' },
  { name: 'Pillow',             version: '10.4',  license: 'HPND',       desc: 'Bildverarbeitung' },
  { name: 'pytesseract',        version: '0.3',   license: 'Apache 2.0', desc: 'OCR via Tesseract' },
  { name: 'pydantic-settings',  version: '2.5',   license: 'MIT',        desc: 'Konfiguration via Umgebungsvariablen' },
  { name: 'python-multipart',   version: '0.0',   license: 'Apache 2.0', desc: 'Datei-Uploads' },
  { name: 'httpx',              version: '0.27',  license: 'BSD-3',      desc: 'Async HTTP-Client' },
  { name: 'aiofiles',           version: '24.1',  license: 'Apache 2.0', desc: 'Asynchrone Dateioperationen' },
  { name: 'python-dotenv',      version: '1.0',   license: 'BSD-3',      desc: '.env-Dateien laden' },
]

const infra = [
  { name: 'MariaDB',         version: '11.4',  license: 'GPL 2.0',    desc: 'Relationale Datenbank' },
  { name: 'Redis',           version: '7.4',   license: 'RSALv2',     desc: 'In-Memory-Datenspeicher (Task-Queue)' },
  { name: 'Docker',          version: '—',     license: 'Apache 2.0', desc: 'Container-Runtime' },
  { name: 'Docker Compose',  version: '—',     license: 'Apache 2.0', desc: 'Multi-Container-Orchestrierung' },
  { name: 'Caddy',           version: '2',     license: 'Apache 2.0', desc: 'Reverse Proxy mit automatischem HTTPS' },
  { name: 'GnuPG',           version: '—',     license: 'GPL 3.0',    desc: 'Backup-Verschlüsselung (AES-256)' },
  { name: 'Tesseract OCR',   version: '—',     license: 'Apache 2.0', desc: 'OCR-Engine für Belegscans' },
]
</script>
