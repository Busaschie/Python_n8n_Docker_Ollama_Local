# Python_n8n_Docker_Ollama_Local

n8n-Workflows lokal über Docker, gesteuert per Python und angebunden an ein lokales LLM via Ollama.

> **Status:** Work in progress

## Überblick

Das Projekt automatisiert den kompletten Lebenszyklus eines n8n-Workflows mit Python-Skripten: Container starten, Credentials anlegen, Workflow generieren, deployen, aktivieren, ausführen und debuggen. Die KI-Komponenten laufen lokal über [Ollama](https://ollama.com) – ohne Cloud-API.

## Tech-Stack

- Python
- Docker / Docker Compose
- n8n
- Ollama (lokale LLMs, Ollama-API)

## Projektstruktur

```text
├── _01_containerize.py   # n8n-Container bauen/starten
├── _02_add_creds.py      # Credentials in n8n anlegen
├── _03_initialize.py     # n8n initialisieren
├── _04_generator.py      # Workflow generieren
├── _05_deploy.py         # Workflow nach n8n deployen
├── _06_activate.py       # Workflow aktivieren
├── _07_execute.py        # Workflow ausführen
├── _08_debugger.py       # Fehleranalyse
├── __current__.py        # aktuell bearbeiteter Schritt
├── Dockerfile.n8n
├── docker-compose.yml
├── requirements.txt
├── credentials/          # Zugangsdaten (nicht committen!)
├── prompts/              # Prompts für die LLM-Generierung
├── src/                  # Hilfsmodule
└── workflows/            # Workflow-Definitionen
```

## Voraussetzungen

- Python 3.10+
- Docker Desktop
- Ollama (lokal installiert, Modell geladen, z. B. `ollama pull <modell>`)

## Installation

```bash
git clone https://github.com/Busaschie/Python_n8n_Docker_Ollama_Local.git
cd Python_n8n_Docker_Ollama_Local
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Nutzung

Die Skripte sind nummeriert und werden der Reihe nach ausgeführt:

```bash
python _01_containerize.py
python _02_add_creds.py
python _03_initialize.py
python _04_generator.py
python _05_deploy.py
python _06_activate.py
python _07_execute.py
```

Bei Fehlern: `python _08_debugger.py`

## Sicherheit

Der Ordner `credentials/` enthält sensible Daten. Keine echten Schlüssel oder Passwörter ins Repository committen – in `.gitignore` aufnehmen.

## Roadmap

- [ ] Dokumentation der einzelnen Schritte erweitern
- [ ] Beispiel-Workflows ergänzen
