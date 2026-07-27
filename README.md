# OverBudget

Self-hosted persönliche Buchhaltungssoftware nach dem Prinzip der doppelten Buchführung. Läuft vollständig lokal via Docker Compose.

## Features

- **Doppelte Buchführung** — Jede Transaktion hat ein Soll- und ein Habenkonto
- **MT940-Import** — Kontoauszüge im SWIFT-Format direkt importieren
- **CSV-Import** — Kreditkartenabrechnung und beliebige CSV-Dateien importieren
- **Automatische Regeln** — Buchungen nach Beschreibung/IBAN automatisch zuordnen
- **Budgets** — Monatliche Limits pro Konto verfolgen
- **Verschlüsselte Backups** — AES-256 via GPG, im Browser herunterladbar
- **Dark Mode** — Hell/Dunkel umschaltbar
- **Session-Cookie-Authentifizierung** — Einzelner Benutzer, kein Benutzermanagement nötig
- **HTTPS** — Caddy als Reverse Proxy mit automatischem internem Zertifikat

---

## Schnellstart

### Auf einer VM installieren (automatisiert)

```bash
git clone https://github.com/drstrangelove52/overbudget.git
cd overbudget
./install.sh
```

Installiert Docker + Tailscale, generiert `.env` mit zufälligen Secrets (DB-Passwörter,
Admin-Passwort, GPG-Passphrase), baut und startet den Stack und richtet Tailscale-HTTPS
ein. Siehe Kommentar am Kopf von `install.sh` für optionale Umgebungsvariablen
(`TAILSCALE_AUTHKEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `LAN_IP`, …). Idempotent —
`git pull && ./install.sh` ist auch der Update-Workflow.

### Lokal starten (manuell)

```bash
cp .env.example .env
# .env anpassen (DB-Passwörter, APP_USERNAME/APP_PASSWORD, GPG_PASSPHRASE, LAN_IP, CADDY_PORT)
docker compose up --build -d
```

Frontend: `https://<LAN_IP>:<CADDY_PORT>` (selbstsigniertes Zertifikat, Browser-Warnung beim ersten Aufruf bestätigen — `CADDY_PORT` ist overbudgets feste Zuteilung aus dem Port-Schema für mehrere Apps auf einer VM, siehe Docker App Standard)
Backend-API: `https://<LAN_IP>:<CADDY_PORT>/api` (via Caddy/Nginx-Proxy)

**Wichtig:** `GPG_PASSPHRASE` unbedingt ändern, sonst schlägt der Backup fehl.

---

## Architektur

```
Browser
  │
  ▼
Caddy (HTTPS-Reverse-Proxy, Port <CADDY_PORT> auf LAN-IP)
  ├─► Frontend (Vue 3, intern Port 80)
  └─► API (FastAPI, intern Port 8000)
        ├─► MariaDB (doppelte Buchführung)
        └─► Redis ──► Celery Worker (OCR, async Tasks)
```

### Dienste (docker-compose.yml)

| Dienst     | Image / Build    | Port  | Aufgabe                              |
|------------|------------------|-------|--------------------------------------|
| `db`       | mariadb:11.4     | —     | Persistente Datenbank                |
| `redis`    | redis:7.4-alpine | —     | Task-Queue für Celery                |
| `api`      | ./backend        | 8000  | REST-API, Alembic-Migrationen        |
| `worker`   | ./backend        | —     | Celery-Worker (OCR, async Tasks)     |
| `frontend` | ./frontend       | 80 (intern) | Vue 3 Single Page Application   |
| `caddy`    | caddy:2-alpine   | `<CADDY_PORT>` (LAN-IP) | HTTPS, Reverse Proxy |

---

## API-Übersicht

Basis-URL: `https://<host>/api` (oder `http://localhost:8000/api`)

Alle Endpunkte ausser `/auth/login` erfordern ein gültiges Session-Cookie (`session`, httpOnly, wird beim Login gesetzt).

### Authentifizierung

| Methode | Pfad              | Beschreibung                          |
|---------|-------------------|----------------------------------------|
| POST    | `/auth/login`     | Login, setzt das Session-Cookie        |
| POST    | `/auth/logout`    | Logout, invalidiert die Session serverseitig |

**Request:**
```json
{ "username": "admin", "password": "changeme" }
```
**Response:** `{ "detail": "ok" }` — das Session-Cookie kommt über den `Set-Cookie`-Header, nicht im Body.

### Konten (`/accounts`)

| Methode | Pfad                | Beschreibung                   |
|---------|---------------------|--------------------------------|
| GET     | `/accounts`         | Alle Konten (mit Gruppen)      |
| POST    | `/accounts`         | Konto anlegen                  |
| PUT     | `/accounts/{id}`    | Konto bearbeiten               |
| DELETE  | `/accounts/{id}`    | Konto löschen                  |

**Kontotypen:** `asset` (Aktiven), `liability` (Passiven), `income` (Ertrag), `expense` (Aufwand), `equity` (Eigenkapital)

**Konto anlegen (Beispiel):**
```json
{
  "number": "1020",
  "name": "Bankkonto UBS",
  "type": "asset",
  "is_group": false,
  "parent_id": null,
  "active": true
}
```

### Buchungen (`/transactions`)

| Methode | Pfad                  | Beschreibung                        |
|---------|-----------------------|-------------------------------------|
| GET     | `/transactions`       | Alle Buchungen                      |
| POST    | `/transactions`       | Buchung manuell erfassen            |
| PUT     | `/transactions/{id}`  | Buchung bearbeiten                  |
| DELETE  | `/transactions/{id}`  | Buchung löschen                     |

**Buchung anlegen (Beispiel):**
```json
{
  "date": "2025-01-15",
  "description": "Migros Einkauf",
  "amount": "45.80",
  "debit_account_id": 42,
  "credit_account_id": 10,
  "document_id": null
}
```

### Importe (`/documents`)

| Methode | Pfad                          | Beschreibung                          |
|---------|-------------------------------|---------------------------------------|
| GET     | `/documents`                  | Alle Importe                          |
| POST    | `/documents/mt940`            | MT940-Datei importieren               |
| POST    | `/documents/csv`              | CSV-Datei importieren                 |
| GET     | `/documents/{id}/transactions`| Buchungen eines Imports               |
| POST    | `/documents/{id}/book`        | Vorschläge als gebucht markieren      |
| DELETE  | `/documents/{id}`             | Import und zugehörige Buchungen löschen|

**CSV-Import (multipart/form-data):**
```
file              Datei (.csv)
date_col          0-basierter Spaltenindex für Datum
amount_col        0-basierter Spaltenindex für Betrag
description_col   0-basierter Spaltenindex für Beschreibung (optional)
account_id        ID des Festkontos (optional)
account_on_credit_side  true = Kreditkarte, false = Bankkonto
```

### Regeln (`/rules`)

| Methode | Pfad           | Beschreibung              |
|---------|----------------|---------------------------|
| GET     | `/rules`        | Alle Regeln               |
| POST    | `/rules`        | Regel anlegen             |
| PUT     | `/rules/{id}`   | Regel bearbeiten          |
| DELETE  | `/rules/{id}`   | Regel löschen             |
| POST    | `/rules/apply`  | Alle Regeln neu anwenden  |

**Regel anlegen (Beispiel):**
```json
{
  "name": "Migros → Lebensmittel",
  "match_field": "description",
  "match_value": "migros",
  "debit_account_id": 42,
  "credit_account_id": null,
  "priority": 10
}
```

### Budgets (`/budgets`)

| Methode | Pfad              | Beschreibung         |
|---------|-------------------|----------------------|
| GET     | `/budgets`        | Alle Budgets         |
| POST    | `/budgets`        | Budget anlegen       |
| PUT     | `/budgets/{id}`   | Budget bearbeiten    |
| DELETE  | `/budgets/{id}`   | Budget löschen       |

**Budget anlegen (Beispiel):**
```json
{
  "account_id": 42,
  "monthly_limit": "500.00",
  "name": "Lebensmittel"
}
```

### Backup (`/backup`)

| Methode | Pfad               | Beschreibung                          |
|---------|--------------------|---------------------------------------|
| GET     | `/backup`          | Backup als `.sql.gpg` herunterladen   |
| POST    | `/backup/restore`  | Backup wiederherstellen (multipart)   |

---

## Datenmodell

### Kontenplan (Accounts)

```
Account
├── id          INT (PK)
├── number      VARCHAR (z.B. "1020")
├── name        VARCHAR (z.B. "Bankkonto UBS")
├── type        ENUM: asset | liability | income | expense | equity
├── is_group    BOOL
├── parent_id   FK → Account.id (optional)
└── active      BOOL
```

### Buchungen (Transactions)

```
Transaction
├── id                INT (PK)
├── date              DATE
├── description       TEXT (optional)
├── amount            DECIMAL(15,2)
├── debit_account_id  FK → Account.id
├── credit_account_id FK → Account.id
├── document_id       FK → Document.id (optional)
├── status            ENUM: booked | suggested
└── created_at        DATETIME
```

### Importe (Documents)

```
Document
├── id            INT (PK)
├── source        ENUM: mt940 | csv
├── status        ENUM: pending | partial | booked
├── received_at   DATETIME
└── original_file VARCHAR (optional)
```

### Regeln (Rules)

```
Rule
├── id                INT (PK)
├── name              VARCHAR
├── match_field       ENUM: description | iban | amount
├── match_value       VARCHAR (Substring-Match, case-insensitive)
├── debit_account_id  FK → Account.id (optional)
├── credit_account_id FK → Account.id (optional)
└── priority          INT (höhere Zahl = höhere Priorität)
```

---

## CSV-Import erklärt

### Spalten-Mapping

Im Import-Dialog werden die CSV-Spalten auf drei Felder gemappt:

| Feld          | Pflicht | Beschreibung                                    |
|---------------|---------|-------------------------------------------------|
| Datum         | Ja      | Datum der Transaktion                           |
| Betrag        | Ja      | Positiver oder negativer Betrag                 |
| Beschreibung  | Nein    | Buchungstext / Verwendungszweck                 |

Unterstützte Datumsformate: `DD.MM.YYYY`, `YYYY-MM-DD`, `DD/MM/YYYY`, `MM/DD/YYYY`, `DDMMYYYY`, `YYYYMMDD`

Unterstützte Betragsformate: `1.234,56` (CH/DE), `1,234.56` (US/UK), `(123.45)` (negativ in Klammern)

### Festkonto

Das **Festkonto** ist das Konto, das bei jeder Buchung im Import auf einer Seite steht — typischerweise die Kreditkarte oder das Bankkonto selbst.

**Beispiel Kreditkarte:**
- Festkonto: `2000 Kreditkarte Visa` (Passivkonto)
- "Positiver Betrag = Habenkonto" ☑ (Ausgaben belasten die Kreditkarte)
- Importierte Buchungen: Soll = Ausgabenkonto (wird vorgeschlagen), Haben = Kreditkarte

**Beispiel Bankkonto:**
- Festkonto: `1020 Bankkonto UBS` (Aktivkonto)
- "Positiver Betrag = Habenkonto" ☐ (Eingang belastet das Bankkonto)
- Importierte Buchungen: Soll = Bankkonto, Haben = Ertragskonto (wird vorgeschlagen)

---

## HTTPS einrichten

### Mit Caddy (LAN-Direktzugriff)

Das mitgelieferte `Caddyfile` terminiert HTTPS für die per `LAN_IP` übergebene Adresse
(Caddys native `{$VAR}`-Interpolation, von `install.sh`/`.env` automatisch gesetzt —
kein manueller Hostname-Eintrag nötig):

```caddy
{
	default_sni {$LAN_IP}
}

https://{$LAN_IP}:{$CADDY_PORT} {
    tls internal
    reverse_proxy frontend:80
}
```

`CADDY_PORT` ist overbudgets feste Zuteilung aus dem Port-Schema für mehrere Apps auf
einer VM (`8082`, siehe Docker App Standard) — auf einer geteilten VM kann nicht jede App
Port 443 exklusiv beanspruchen, deshalb kein `:80`-Redirect-Block mehr wie bei einer
einzelnen App auf eigener VM.

**Zwei Gotchas, live auf overbudget01 gefunden:**
1. Ein reiner Port-Block ohne Hostnamen (`:443 { tls internal }`) funktioniert *nicht* —
   Caddy kann dann keinem Zertifikat eine Adresse zuordnen und bricht den TLS-Handshake
   mit einem `internal_error`-Alert ab. Ein konkreter Hostname oder eine IP im Site-Block
   ist zwingend, damit Caddy weiss, für welchen Namen es das self-signed Zertifikat
   ausstellen soll.
2. Selbst mit `https://{$LAN_IP}` als Site-Adresse schlägt der Handshake noch fehl,
   sobald der Client **kein SNI sendet** — und genau das tun curl, die meisten
   RFC-konformen HTTP-Clients (inkl. Tailscale) und teils Browser bei einer nackten
   IP-Adresse, da SNI laut RFC 6066 nur für DNS-Hostnamen vorgesehen ist. Ohne SNI fällt
   Caddy auf die lokale Socket-Adresse zurück — innerhalb des Docker-Containers ist das
   die interne Bridge-IP (z.B. `172.18.0.6`), nie die echte `LAN_IP` — und findet dafür
   kein passendes Zertifikat. Der globale `default_sni {$LAN_IP}`-Eintrag oben behebt
   das: Caddy nimmt bei fehlendem SNI automatisch `{$LAN_IP}` an.

`tls internal` erzeugt ein selbstsigniertes Zertifikat. Reicht zum normalen Browsen
(Warnung im Browser einmalig wegklicken), aber Browser vertrauen diesem Zertifikat nie
wirklich — für sicherheitsrelevante Nutzung (z.B. Zugriff von unterwegs) siehe Tailscale
unten.

### Mit Tailscale (empfohlen, macht `install.sh` automatisch)

`install.sh` installiert Tailscale, verbindet die VM mit dem Tailnet und richtet
`tailscale serve` ein, das ein echtes, öffentlich vertrauenswürdiges Zertifikat fürs
Tailnet bereitstellt und den Traffic intern an Caddy weiterreicht:

```bash
sudo tailscale serve --bg --https=8444 "https+insecure://${LAN_IP}:8082"
```

Port `8444` statt des Tailscale-Default-443, weil sich mehrere Apps denselben
Tailscale-Node (die VM) teilen — jede bekommt ihren eigenen externen Port (Port-Schema
siehe Docker App Standard). Die App ist danach unter
`https://<tailscale-hostname>.tailXXXX.ts.net:8444` ohne Zertifikatswarnung erreichbar —
auch von ausserhalb des LANs, sofern das Gerät im selben Tailnet ist. **Wichtig:** Docker
published Ports standardmässig auf alle
Host-Interfaces inkl. `tailscale0` — `docker-compose.yml` bindet Caddys Ports deshalb
explizit auf `${LAN_IP}` statt `0.0.0.0`, sonst würde Tailscale Caddys self-signed statt
seinem eigenen echten Zertifikat sehen.

---

## Backup und Restore

### Backup erstellen

Über die Einstellungsseite (Zahnrad-Icon) → **Backup herunterladen**.

Die Datei `overbudget-backup-YYYY-MM-DD.sql.gpg` enthält einen vollständigen MariaDB-Dump, verschlüsselt mit AES-256 via GPG.

### Backup wiederherstellen

1. Einstellungen → **Backup-Datei auswählen…**
2. `.gpg`-Datei auswählen
3. Bestätigen → **Jetzt wiederherstellen**

**Achtung:** Alle aktuellen Daten werden überschrieben.

### Manuelles Backup (CLI)

```bash
# Backup erstellen
docker compose exec api sh -c \
  "mysqldump -h db -u overbudget -p'$DB_PASSWORD' overbudget \
   | gpg --batch --yes --passphrase '$GPG_PASSPHRASE' \
         --symmetric --cipher-algo AES256 \
   > /tmp/backup.sql.gpg"

# Backup wiederherstellen
docker compose exec api sh -c \
  "gpg --batch --yes --passphrase '$GPG_PASSPHRASE' \
       --decrypt /tmp/backup.sql.gpg \
   | mysql -h db -u overbudget -p'$DB_PASSWORD' overbudget"
```

---

## Entwicklung

### Backend lokal starten

```bash
cd backend
pip install -r requirements.txt
DATABASE_URL=mysql+pymysql://... SESSION_COOKIE_SECURE=false uvicorn app.main:app --reload
```

`SESSION_COOKIE_SECURE=false` ist hier nötig, weil `uvicorn --reload` Klartext-HTTP spricht
und Browser ein `Secure`-Cookie über HTTP grundsätzlich verwerfen — sonst schlägt der
Login lokal fehl. In Produktion (hinter Caddy/Tailscale, immer HTTPS) bleibt es beim
Default `true`.

API-Dokumentation (Swagger): `http://localhost:8000/docs`

### Frontend lokal starten

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Vite proxied `/api` auf `http://localhost:8000` (siehe `vite.config.js`).

### Datenbank-Migrationen

```bash
# Neue Migration erzeugen
docker compose exec api alembic revision --autogenerate -m "beschreibung"

# Migrationen anwenden
docker compose exec api alembic upgrade head
```

---

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

Eine vollständige Liste der verwendeten Open-Source-Bibliotheken und deren Lizenzen ist in der Anwendung unter **Info** (ⓘ-Icon) abrufbar.
