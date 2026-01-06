# Auto API

Automatische REST und GraphQL API für beliebige Datenbanken mit FastAPI, SQLAlchemy und Strawberry GraphQL.

## Features

- ✅ Automatische REST API für alle Datenbanktabellen
- ✅ Automatische GraphQL API
- ✅ Unterstützung für PostgreSQL, MySQL und SQLite
- ✅ CRUD Operationen
- ✅ Pagination
- ✅ Automatische API-Dokumentation (Swagger/ReDoc)
- ✅ GraphQL Playground
- ✅ Konfiguration über .env
- ✅ Modern mit UV und Hatchling

## Installation

### Mit UV (empfohlen)

```bash
# UV installieren
curl -LsSf https://astral.sh/uv/install.sh | sh

# Projekt setup
uv venv
source .venv/bin/activate  # Linux/Mac
# oder
.venv\Scripts\activate  # Windows

# Dependencies installieren
uv pip install -e .

# Für Development
uv pip install -e ".[dev]"
