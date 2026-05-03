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
- **JWT-Authentifizierung** — Einzelner Benutzer, kein Benutzermanagement nötig
- **HTTPS** — Caddy als Reverse Proxy mit automatischem internem Zertifikat

---

## Schnellstart

### Voraussetzungen

- Docker und Docker Compose
- (optional) Caddy für HTTPS

### Installation

```bash
git clone <repo-url> overbudget
cd overbudget
cp .env.example .env   # Passwörter anpassen!
docker compose up -d
```

Die Anwendung ist danach unter `http://localhost:3000` erreichbar.

### .env konfigurieren

```dotenv
DB_ROOT_PASSWORD=sicheres-root-passwort
DB_PASSWORD=sicheres-db-passwort
APP_USERNAME=admin
APP_PASSWORD=sicheres-passwort          # Login-Passwort
JWT_SECRET=langer-zufaelliger-string    # min. 32 Zeichen
GPG_PASSPHRASE=backup-passphrase        # für verschlüsselte Backups
```

**Wichtig:** `JWT_SECRET` und `GPG_PASSPHRASE` unbedingt ändern. Ohne `GPG_PASSPHRASE` schlägt der Backup fehl.

---

## Architektur

```
Browser
  │
  ▼
Caddy (HTTPS-Reverse-Proxy, Port 80/443)
  ├─► Frontend (Vue 3, Port 3000/80)
  └─► API (FastAPI, Port 8000)
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
| `frontend` | ./frontend       | 3000  | Vue 3 Single Page Application        |
| `caddy`    | caddy:2-alpine   | 80/443| HTTPS, Reverse Proxy                 |

---

## API-Übersicht

Basis-URL: `https://<host>/api` (oder `http://localhost:8000/api`)

Alle Endpunkte ausser `/auth/login` erfordern `Authorization: Bearer <token>`.

### Authentifizierung

| Methode | Pfad              | Beschreibung                  |
|---------|-------------------|-------------------------------|
| POST    | `/auth/login`     | Login, gibt JWT zurück        |

**Request:**
```json
{ "username": "admin", "password": "changeme" }
```
**Response:**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

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

### Mit Caddy (internes Netzwerk)

Das mitgelieferte `Caddyfile` stellt HTTPS für einen lokalen Hostnamen bereit:

```caddy
claudecode01.pe.lan {
    tls internal
    reverse_proxy frontend:80
}
```

`tls internal` erzeugt ein selbstsigniertes Zertifikat. Dem Caddy-Root-CA muss einmalig im Browser vertraut werden.

### Mit Tailscale (empfohlen für Remote-Zugriff)

```bash
# Tailscale installieren und HTTPS aktivieren
tailscale up --advertise-routes=...
tailscale cert <hostname>.ts.net
```

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
DATABASE_URL=mysql+pymysql://... uvicorn app.main:app --reload
```

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
