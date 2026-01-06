# GraphSQL

<div align="center">

![GraphSQL Logo](https://via.placeholder.com/200x200?text=GraphSQL)

**Automatic REST and GraphQL API generator for any SQL database**

[![CI](https://github.com/afeldman/graphsql/workflows/CI/badge.svg)](https://github.com/afeldman/graphsql/actions)
[![codecov](https://codecov.io/gh/afeldman/graphsql/branch/main/graph/badge.svg)](https://codecov.io/gh/afeldman/graphsql)
[![PyPI version](https://badge.fury.io/py/graphsql.svg)](https://badge.fury.io/py/graphsql)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache](https://img.shields.io/badge/License-Apache-yellow.svg)](https://opensource.org/licenses/MIT)

[Features](#features) •
[Installation](#installation) •
[Quick Start](#quick-start) •
[Documentation](#documentation) •
[Contributing](#contributing)

</div>

---

## ✨ Features

- **🔄 Automatic REST API** — Instant CRUD endpoints for all database tables
- **📊 Automatic GraphQL API** — Full GraphQL schema generation from database
- **🗄️ Multi-Database Support** — PostgreSQL, MySQL, SQLite with seamless switching
- **⚡ Modern Stack** — FastAPI, SQLAlchemy 2.0, Strawberry GraphQL, loguru
- **📖 API Documentation** — Swagger UI and ReDoc automatically generated
- **🎮 GraphQL Playground** — Interactive GraphQL IDE built-in
- **🔒 Security Ready** — Environment-based configuration, non-root containers, CORS support
- **🐳 Docker Ready** — Multi-stage Dockerfile with security best practices
- **☸️ Kubernetes Ready** — Complete Helm chart with HPA, NetworkPolicy, persistence
- **🔧 Environment Configuration** — python-decouple for flexible env handling
- **📝 Comprehensive Logging** — loguru for structured, production-grade logging
- **🧪 Code Quality** — black, ruff, mypy, pytest integration
- **📚 Full Documentation** — Sphinx docs with Google-style docstrings
- **🚀 Easy Startup** — Console script entry points (graphsql, graphsql-start)

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Docker Deployment](#docker-deployment)
- [Kubernetes & Helm](#kubernetes--helm)
- [Environment Variables](#environment-variables)
- [Additional Databases](#additional-databases-hana-redshift-snowflake)
- [Development](#development)
- [Testing](#-testing)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

**[Full Contributing Guide →](CONTRIBUTING.md)**

```bash
# Clone repository
git clone <repository>
cd graphsql

# Create virtual environment with UV
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -e .

# Start server
graphsql-start

# Access API
curl http://localhost:8000/
```

### Using Docker

```bash
# Build image
docker build -t graphsql:latest .

# Run standalone
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///graphql.db" \
  graphsql:latest

# Or with docker-compose
docker-compose up
```

## 📦 Installation

### System Requirements

- **Python:** 3.7 or higher (tested with 3.7, 3.8, 3.9, 3.10, 3.11, 3.12)
- **Database:** PostgreSQL 12+, MySQL 8+, or SQLite 3.9+
- **Docker:** 20.10+ (for containerized deployment)
- **Kubernetes:** 1.20+ (for orchestrated deployment)

### Development Setup

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install with development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify installation
graphsql --version
```

### Production Setup

#### Using UV Package Manager

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y python3.12 python3.12-venv libpq-dev

# Setup
uv venv
source .venv/bin/activate
uv pip install .

# Start server
graphsql-start --host 0.0.0.0 --port 8000
```

#### Using Traditional pip

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install .

# Start
python -m graphsql.main
```

#### Using Docker

```bash
# Build production image
docker build -t graphsql:prod .

# Run with environment file
docker run --env-file .env.prod \
  -p 8000:8000 \
  graphsql:prod
```

## ⚙️ Configuration

### Environment Variables

Create `.env` file or set environment variables. See [Environment Variables](#environment-variables) section for complete reference.

#### SQLite Example

```bash
# .env
DATABASE_URL=sqlite:///graphsql.db
API_HOST=localhost
API_PORT=8000
LOG_LEVEL=INFO
```

#### PostgreSQL Example

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/graphsql
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
ENABLE_AUTH=true
API_KEY=your-secret-key-here
LOG_LEVEL=INFO
```

#### MySQL Example

```bash
# .env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/graphsql
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## Additional Databases (HANA, Redshift, Snowflake)

Install the cloud dialects when needed (use UV):

```bash
uv pip install -e ".[dev,cloud]"
```

#### SAP HANA

```bash
# .env
DATABASE_URL=hana+hdbcli://USER:PASSWORD@hana-host:39015/?encrypt=true&sslValidateCertificate=true
# optional: currentschema=MYSCHEMA
```

#### Amazon Redshift

```bash
# .env (password auth)
DATABASE_URL=redshift+psycopg2://USER:PASSWORD@cluster.region.redshift.amazonaws.com:5439/DBNAME
# if you prefer the AWS driver: redshift+redshift_connector://USER:PASSWORD@cluster.region.redshift.amazonaws.com:5439/DBNAME
```

#### Snowflake

```bash
# .env
DATABASE_URL=snowflake://USER:PASSWORD@ACCOUNT-ID/DB/SCHEMA?warehouse=WH&role=ROLE
```

Notes:
- Provide database and schema for Snowflake; otherwise reflection returns no tables.
- Redshift may not report primary keys—REST works, but GraphQL IDs might need manual PKs.
- HANA often uses composite PKs; ensure tables have a clear primary key for GraphQL.

### Configuration Methods

1. **Environment File (.env)**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Environment Variables**
   ```bash
   export DATABASE_URL=postgresql://...
   export API_PORT=8000
   graphsql-start
   ```

3. **Command-Line Arguments** (planned for v0.2)

## 📖 Usage

### Starting the Server

```bash
# Using console script entry point
graphsql-start

# Or with custom settings
DATABASE_URL=sqlite:///test.db graphsql-start

# With debug logging
LOG_LEVEL=DEBUG graphsql-start

# Custom host/port
API_HOST=127.0.0.1 API_PORT=9000 graphsql-start
```

### REST API Examples

#### List All Tables

```bash
curl http://localhost:8000/api/tables
```

Response:
```json
["users", "posts", "comments"]
```

#### Get Table Schema

```bash
curl http://localhost:8000/api/tables/users/info
```

Response:
```json
{
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "nullable": false,
      "primary_key": true
    },
    {
      "name": "name",
      "type": "VARCHAR(255)",
      "nullable": false,
      "primary_key": false
    }
  ],
  "primary_key": "id"
}
```

#### List Records with Pagination

```bash
# Get first 10 users
curl "http://localhost:8000/api/users?limit=10&offset=0"

# Get next 10
curl "http://localhost:8000/api/users?limit=10&offset=10"
```

Response:
```json
[
  {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  },
  {
    "id": 2,
    "name": "Bob",
    "email": "bob@example.com"
  }
]
```

#### Get Single Record

```bash
curl http://localhost:8000/api/users/1
```

Response:
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
}
```

#### Create Record

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","email":"charlie@example.com"}'
```

Response (201 Created):
```json
{
  "id": 3,
  "name": "Charlie",
  "email": "charlie@example.com"
}
```

#### Update Record (Full)

```bash
curl -X PUT http://localhost:8000/api/users/3 \
  -H "Content-Type: application/json" \
  -d '{"name":"Charles","email":"charles@example.com"}'
```

#### Partial Update

```bash
curl -X PATCH http://localhost:8000/api/users/3 \
  -H "Content-Type: application/json" \
  -d '{"name":"Chuck"}'
```

#### Delete Record

```bash
curl -X DELETE http://localhost:8000/api/users/3
```

Response: 204 No Content

### GraphQL API Examples

#### Access GraphQL Playground

Open browser to: `http://localhost:8000/graphql`

#### List Users (Query)

```graphql
query {
  users(limit: 10, offset: 0) {
    id
    name
    email
  }
}
```

#### Get User by ID

```graphql
query {
  user(id: 1) {
    id
    name
    email
  }
}
```

#### Create User (Mutation)

```graphql
mutation {
  createUser(name: "David", email: "david@example.com") {
    id
    name
    email
  }
}
```

## 🔌 API Endpoints

### REST Endpoints

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|------------|
| GET | `/` | Root info with available endpoints | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/api/tables` | List all tables | 200 |
| GET | `/api/tables/{table}/info` | Get table schema | 200 |
| GET | `/api/{table}` | List records (paginated) | 200 |
| GET | `/api/{table}/{id}` | Get single record | 200 |
| POST | `/api/{table}` | Create record | 201 |
| PUT | `/api/{table}/{id}` | Update record | 200 |
| PATCH | `/api/{table}/{id}` | Partial update | 200 |
| DELETE | `/api/{table}/{id}` | Delete record | 204 |

### GraphQL Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/graphql` | GraphQL API and Playground |
| `/graphql?query=...` | GraphQL queries via GET |

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database_connected": true,
  "tables_count": 5,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🐳 Docker Deployment

### Building the Image

```bash
# Standard build
docker build -t graphsql:latest .

# With specific Python version
docker build --build-arg PYTHON_VERSION=3.12 -t graphsql:3.12 .

# Production build
docker build -t graphsql:prod --target=runtime .
```

### Running Standalone

```bash
# With SQLite
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///graphsql.db" \
  graphsql:latest

# With PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e LOG_LEVEL=DEBUG \
  graphsql:latest

# With volume for SQLite persistence
docker run -p 8000:8000 \
  -v graphsql-data:/app/data \
  -e DATABASE_URL="sqlite:////app/data/graphsql.db" \
  graphsql:latest
```

### Docker Compose

```bash
# Start standalone (SQLite)
docker-compose up

# Start with PostgreSQL
docker-compose --profile with-postgres up

# Logs
docker-compose logs -f graphsql

# Stop
docker-compose down
```

#### docker-compose.yml Structure

```yaml
services:
  graphsql:
    # Main API service
    image: graphsql:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: sqlite:///graphsql.db
    volumes:
      - graphsql-data:/app/data

  postgres:
    # Optional PostgreSQL database
    image: postgres:15
    profiles:
      - with-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: graphsql
      POSTGRES_PASSWORD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

### Production Stack (API + Admin)

Use the production compose to run the API, Redis-backed streaming, PostgreSQL, and the Fresh admin dashboard.

```bash
# Build and start everything
docker compose -f docker-compose.prod.yml up -d --build

# Tail logs
docker compose -f docker-compose.prod.yml logs -f

# Stop and remove
docker compose -f docker-compose.prod.yml down
```

Service endpoints:
- API: http://localhost:8000 (env: `DATABASE_URL`, `REDIS_URL`, `API_HOST`, `API_PORT`, `LOG_LEVEL`, `CORS_ORIGINS`)
- Admin: http://localhost:8001 (env: `GRAPHSQL_URL` pointing at the API base)
- PostgreSQL and Redis use named volumes for persistence (`postgres_data`)

### Health Checks

```bash
# Check container health
docker ps | grep graphsql

# Manual health check
curl http://localhost:8000/health

# Inside container
docker exec graphsql curl http://localhost:8000/health
```

## ☸️ Kubernetes & Helm

### Prerequisites

- Kubernetes cluster (1.20+)
- Helm 3.0+
- kubectl configured
- Container registry (Docker Hub, ECR, etc.)

### Quick Start with Helm

#### 1. Publish Docker Image

```bash
# Tag image
docker build -t myregistry/graphsql:v0.1.0 .
docker push myregistry/graphsql:v0.1.0
```

#### 2. Install Helm Chart

```bash
# With default values
helm install graphsql ./helm \
  --set image.repository=myregistry/graphsql \
  --set image.tag=v0.1.0

# With custom values file
helm install graphsql ./helm \
  -f helm/values-prod.yaml

# With PostgreSQL database
helm install graphsql ./helm \
  --set database.type=postgresql \
  --set database.url=postgresql://user:pass@postgres:5432/graphsql
```

#### 3. Verify Deployment

```bash
# Check deployment
kubectl get deployment graphsql

# Check pods
kubectl get pods -l app=graphsql

# Check service
kubectl get svc graphsql

# Logs
kubectl logs -l app=graphsql -f

# Port forward for local testing
kubectl port-forward svc/graphsql 8000:80
```

### Helm Chart Configuration

#### Key Configuration Values

| Parameter | Default | Description |
|-----------|---------|-------------|
| `image.repository` | `graphsql` | Docker image repository |
| `image.tag` | `latest` | Docker image tag |
| `replicaCount` | `2` | Number of replicas |
| `service.type` | `ClusterIP` | Service type |
| `database.type` | `sqlite` | Database type (sqlite/postgresql/mysql) |
| `database.url` | `sqlite:///data/graphsql.db` | Database connection URL |
| `ingress.enabled` | `false` | Enable ingress |
| `ingress.hosts[0].host` | `graphsql.local` | Ingress hostname |
| `autoscaling.enabled` | `true` | Enable HPA |
| `autoscaling.minReplicas` | `2` | Minimum replicas |
| `autoscaling.maxReplicas` | `5` | Maximum replicas |

#### Custom Values File Example

```yaml
# helm/values-prod.yaml
image:
  repository: myregistry/graphsql
  tag: v0.1.0
  pullPolicy: IfNotPresent

replicaCount: 3

service:
  type: LoadBalancer
  port: 80

database:
  type: postgresql
  url: postgresql://user:password@postgres.default.svc:5432/graphsql

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: graphsql-tls
      hosts:
        - api.example.com

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  capabilities:
    drop:
      - ALL
```

### Helm Operations

#### Update Release

```bash
# Update to new version
helm upgrade graphsql ./helm \
  --set image.tag=v0.2.0

# Rollback to previous version
helm rollback graphsql
```

#### Inspect Release

```bash
# List releases
helm list

# Show chart values
helm show values ./helm

# Show release status
helm status graphsql

# Get release values
helm get values graphsql
```

#### Uninstall

```bash
helm uninstall graphsql
```

### Ingress Configuration

#### NGINX Ingress with TLS

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rewrite-target: /
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: graphsql-tls
      hosts:
        - api.example.com
```

Install and test:

```bash
# Update helm values
helm upgrade graphsql ./helm -f values.yaml

# Check ingress
kubectl get ingress

# Test endpoint
curl https://api.example.com/health
```

### Kubernetes Operations

#### Pod Management

```bash
# Get pods
kubectl get pods -l app=graphsql

# Describe pod
kubectl describe pod <pod-name>

# Pod logs
kubectl logs <pod-name>
kubectl logs -f <pod-name>  # Follow logs

# Port forward
kubectl port-forward pod/<pod-name> 8000:8000
```

#### Exec into Container

```bash
# Open shell
kubectl exec -it <pod-name> -- /bin/bash

# Run command
kubectl exec <pod-name> -- graphsql --version
```

#### Rolling Update

```bash
# Manual update
kubectl set image deployment/graphsql \
  graphsql=myregistry/graphsql:v0.2.0

# Monitor rollout
kubectl rollout status deployment/graphsql

# Rollback if needed
kubectl rollout undo deployment/graphsql
```

#### Scaling

```bash
# Scale replicas
kubectl scale deployment graphsql --replicas=5

# Check HPA status
kubectl get hpa graphsql

# HPA metrics
kubectl top nodes
kubectl top pods -l app=graphsql
```

### Database Persistence

#### SQLite with PersistentVolume

```yaml
persistence:
  enabled: true
  storageClass: standard
  accessMode: ReadWriteOnce
  size: 10Gi
  mountPath: /app/data
```

#### PostgreSQL Setup

```bash
# Option 1: External managed database (recommended for production)
helm install graphsql ./helm \
  --set database.type=postgresql \
  --set database.url=postgresql://user:pass@managed-db.service.com:5432/graphsql

# Option 2: Deploy with bitnami/postgresql chart
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --set auth.username=graphsql \
  --set auth.password=securepass \
  --set auth.database=graphsql

# Then connect
helm install graphsql ./helm \
  --set database.url=postgresql://graphsql:securepass@postgres-postgresql:5432/graphsql
```

### Security

#### Network Policy

```bash
# Enable in values.yaml
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
```

#### Pod Security Policy

```bash
# Apply restricted PSP
kubectl apply -f - <<EOF
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: graphsql-restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - configMap
    - emptyDir
    - projected
    - secret
    - downwardAPI
    - persistentVolumeClaim
  runAsUser:
    rule: MustRunAsNonRoot
  fsGroup:
    rule: RunAsAny
  readOnlyRootFilesystem: true
EOF
```

### Monitoring & Observability

#### Prometheus Integration

```yaml
# helm values
serviceMonitor:
  enabled: true
  interval: 30s
  labels:
    release: prometheus
```

#### Access Metrics

```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus 9090:9090

# Query metrics at http://localhost:9090
# Example: up{job="graphsql"}
```

#### Logging

```bash
# View logs
kubectl logs -f deployment/graphsql

# With timestamps
kubectl logs -f deployment/graphsql --timestamps=true

# Previous logs (if pod crashed)
kubectl logs deployment/graphsql --previous
```

### Troubleshooting Kubernetes

#### Check Pod Status

```bash
# Detailed status
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods
```

#### Debug Running Pod

```bash
# Execute command in pod
kubectl exec -it <pod-name> -- env | grep DATABASE

# Check health
kubectl exec <pod-name> -- curl http://localhost:8000/health
```

#### Common Issues

**Pod CrashLoopBackOff:**
```bash
kubectl logs <pod-name> --previous
# Check database connectivity
kubectl exec <pod-name> -- python -c "import sqlalchemy; print('OK')"
```

**ImagePullBackOff:**
```bash
kubectl describe pod <pod-name>
# Verify image exists in registry
docker image inspect myregistry/graphsql:tag
```

**Database Connection Fails:**
```bash
# Verify database URL
kubectl get configmap graphsql-config -o yaml | grep DATABASE

# Check if database service is accessible
kubectl exec <pod-name> -- ping postgres-service
```

## 🔐 Environment Variables

### Database Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | `sqlite:///graphsql.db` | Database connection URL |

**Format Examples:**
- SQLite: `sqlite:///path/to/db.db` or `sqlite:///:memory:`
- PostgreSQL: `postgresql://user:password@localhost:5432/dbname`
- MySQL: `mysql+pymysql://user:password@localhost:3306/dbname`

### API Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_HOST` | string | `127.0.0.1` | Server host binding |
| `API_PORT` | int | `8000` | Server port |
| `CORS_ORIGINS` | string | `http://localhost:3000` | Comma-separated CORS origins |

### Security

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_AUTH` | bool | `false` | Enable API authentication |
| `API_KEY` | string | (none) | API key for authentication |

### Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |

### Setup Methods

#### Method 1: .env File

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/graphsql
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
LOG_LEVEL=INFO
ENABLE_AUTH=false
```

Load with:
```bash
source .env
graphsql-start
```

#### Method 2: Direct Environment Variables

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/graphsql
export API_PORT=8000
export LOG_LEVEL=DEBUG
graphsql-start
```

#### Method 3: Command Line

```bash
DATABASE_URL=sqlite:///test.db API_PORT=9000 graphsql-start
```

## 👨‍💻 Development

### Setup Development Environment

```bash
# Clone repository
git clone <repo>
cd graphsql

# Create virtual environment
uv venv
source .venv/bin/activate

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality Tools

#### Code Formatting

```bash
# Format with black
black src/

# Format with ruff
ruff check --fix src/
```

#### Linting

```bash
# Lint with ruff
ruff check src/

# Type checking with mypy
mypy src/
```

#### Admin (Fresh) Development

```bash
# Install Deno (1.43+) locally
curl -fsSL https://deno.land/install.sh | sh

# Dev server (watches routes/static)
cd admin && deno task dev

# Build static output
deno task build

# Format / lint (also runs via pre-commit)
deno fmt --check admin
deno lint admin
```

Pre-commit runs `deno fmt`/`deno lint` for the admin folder; ensure Deno is available locally before committing.

#### Testing

See [Testing](#-testing) for the full pytest and behave guide, including quick commands, fixtures, and coverage options.

#### Documentation

```bash
# Build documentation
cd docs
make html

# Open documentation
open _build/html/index.html

# Build and serve (requires sphinx-autobuild)
sphinx-autobuild . _build/html
```

### Project Structure

```
graphsql/
├── src/graphsql/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app factory and entry point
│   ├── config.py                # Configuration management (python-decouple)
│   ├── database.py              # SQLAlchemy setup and utilities
│   ├── rest_routes.py           # REST API endpoints
│   ├── graphql_schema.py        # Dynamic GraphQL schema generation
│   └── utils.py                 # Helper functions (data serialization)
├── tests/                       # Unit and integration tests
├── docs/                        # Sphinx documentation
│   ├── conf.py                  # Sphinx configuration
│   ├── index.rst                # Documentation home
│   ├── overview.rst             # Project overview
│   ├── api.rst                  # API documentation
│   ├── _templates/              # Custom templates
│   └── _static/                 # Static files
├── helm/                        # Kubernetes Helm chart
│   ├── Chart.yaml               # Helm metadata
│   ├── values.yaml              # Default configuration
│   └── templates/               # Helm templates (10 files)
├── Dockerfile                   # Multi-stage production build
├── docker-compose.yml           # Local development compose
├── pyproject.toml               # Project metadata and dependencies
├── README.md                    # This file
├── LICENSE                      # Apache 2.0 license
└── .env.example                 # Environment variables template
```

### Module Documentation

#### config.py
Settings management using python-decouple. Provides `Settings.load()` factory method for loading configuration from environment variables with type conversion.

#### database.py
SQLAlchemy database session management, table reflection via automap, and data serialization utilities. Key functions: `get_session()`, `serialize_model()`, `list_tables()`, `get_table_info()`.

#### main.py
FastAPI application factory with health checks, lifespan events, and root endpoint. Entry point for `graphsql` and `graphsql-start` commands.

#### rest_routes.py
Complete CRUD REST API for dynamic database tables. All endpoints have Google-style docstrings with curl examples.

#### graphql_schema.py
Dynamic Strawberry GraphQL schema generation from database tables. Creates Query and Mutation types at runtime.

#### utils.py
Data serialization utility `clean_dict()` handling datetime, Decimal, bytes, and None value normalization.

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add src/
git commit -m "feat: add your feature"

# Push to remote
git push origin feature/your-feature

# Create pull request on GitHub
```

## 🔐 Authentication (JWT)

### Overview

GraphSQL includes built-in **JWT (JSON Web Token) authentication** for securing your API endpoints. The authentication system is optional but recommended for production deployments.

### Features

- ✅ **JWT-based authentication** — Industry-standard JWT tokens
- ✅ **Password hashing** — Secure bcrypt password storage
- ✅ **Scope-based access control** — Admin, default, and custom scopes
- ✅ **Easy integration** — FastAPI dependency injection
- ✅ **Optional** — Enabled via environment variables

### Quick Start

#### 1. Obtain a Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### 2. Use Token in Requests

```bash
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Configuration

Add to `.env`:

```env
# JWT Settings
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440  # 24 hours

# Rate Limiting
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_TABLES=100/minute
RATE_LIMIT_STORAGE_URI=memory://  # For production use redis://<host>:6379

# Redis Cache & Sessions
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300
CACHE_PREFIX=graphsql:cache:
SESSION_TTL_SECONDS=86400
SESSION_PREFIX=graphsql:session:
```

**Auto-generation:** If `JWT_SECRET_KEY` is not set, it will be automatically generated on startup.

### Default Users (Demo)

For development/testing, default users are available:

| Username | Password | Scope |
|----------|----------|-------|
| `admin` | `admin123` | `admin` |
| `demo` | `demo123` | `default` |

⚠️ **Security Warning:** Change these credentials in production!

### Usage in Code

#### Protecting Endpoints

```python
from fastapi import Depends
from graphsql.auth import get_current_user, TokenData

@app.get("/protected")
async def protected_endpoint(user: TokenData = Depends(get_current_user)):
    return {"message": f"Hello, {user.user_id}"}
```

#### Optional Authentication

```python
from graphsql.auth import get_optional_user

@app.get("/optional-auth")
async def optional_auth(user: Optional[TokenData] = Depends(get_optional_user)):
    if user:
        return {"message": f"Hello, {user.user_id}"}
    return {"message": "Hello, anonymous!"}
```

#### Scope-based Authorization

```python
from graphsql.auth import require_scope

@app.post("/admin-only")
async def admin_endpoint(user: TokenData = Depends(require_scope("admin"))):
    return {"message": "Admin access granted"}
```

### API Endpoints

#### POST /auth/login
Authenticate and receive JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Programmatic Usage

```python
from graphsql.auth import create_access_token, verify_token

# Create token
token_response = create_access_token(user_id="john_doe", scope="admin")
print(token_response.access_token)

# Verify token
token_data = verify_token(token_response.access_token)
print(token_data.user_id)  # "john_doe"
print(token_data.scope)    # "admin"
```

### Error Handling

```python
from fastapi import HTTPException, status

# Missing credentials → 401 Unauthorized
# Invalid token → 401 Unauthorized
# Expired token → 401 Unauthorized
# Insufficient permissions → 403 Forbidden
```

---

## ⚡ Rate Limiting

GraphSQL includes **built-in rate limiting** to protect your API from abuse. All endpoints are rate-limited by default.

### Default Limits

| Endpoint Type | Limit |
|--------------|-------|
| **Global Default** | 60 requests/minute per IP |
| **List Tables** | 100 requests/minute per IP |
| **Table Info** | 100 requests/minute per IP |
| **Auth Login** | 60 requests/minute per IP |

### How It Works

Rate limiting is implemented via `slowapi` middleware, which uses the client's IP address as the key. When a client exceeds the limit, they receive a `429 Too Many Requests` response.

**Response Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704110400
```

### Configuration

Add to `.env`:

```env
# Rate limiting is automatic, no additional configuration needed
# Customize per-endpoint using decorators (see code examples below)
```

### Per-Endpoint Configuration

Endpoints can have custom rate limits:

```python
from fastapi import APIRouter
from graphsql.rate_limit import limiter

@app.get("/api/expensive-operation")
@limiter.limit("10 per minute")  # Stricter limit for expensive operations
async def expensive_operation():
    return {"status": "success"}
```

### Production Setup with Redis

For production, configure Redis storage for distributed rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",  # Redis connection string
)
```

### Error Responses

When rate limit is exceeded:

```json
{
  "detail": "429 Too Many Requests"
}
```

HTTP Status: `429 Too Many Requests`

---

## 🧪 Testing

### Quick Start

```bash
pip install -e ".[dev]"

# Everything
make test           # or: pytest && behave

# Unit tests only
make test-unit

# BDD tests only
make test-bdd
```

- Default test database is `sqlite:///:memory:` for isolation; override with `DATABASE_URL=... pytest` when needed.

### Test Structure

```text
tests/                              # Unit tests
├── __init__.py
├── conftest.py                     # Fixtures
├── test_config.py                  # Configuration tests
├── test_rest_routes.py             # REST API tests
└── test_utils.py                   # Utility tests

features/                           # BDD tests
├── environment.py                  # Setup/teardown
├── health_check.feature            # Health check scenarios
└── steps/                          # Step implementations
    └── common_steps.py
```

### Fixtures

- `test_db` — In-memory SQLite URL
- `db_session` — SQLAlchemy session
- `client` — FastAPI TestClient bound to test DB
- `sample_db` — Pre-populated database

### Unit Tests (pytest)

```bash
# Run all unit tests
pytest

# Verbose / specific selection
pytest -vv
pytest tests/test_config.py
pytest tests/test_config.py::TestSettingsLoading
pytest tests/test_config.py::TestSettingsLoading::test_load_defaults

# Coverage
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=term-missing
```

- `test_config.py` — Settings load, env parsing, database type detection, auth, pagination, CORS
- `test_utils.py` — Data cleaning, datetime/decimal/bytes handling, nested structures
- `test_rest_routes.py` — Health, root info, table listing, docs endpoints

### BDD Tests (behave)

```bash
# Run all scenarios
behave

# Targeted runs
behave -v
behave features/health_check.feature
behave --tags=@important

# Reporting
behave --format=pretty
behave --format=html -o reports/behave_report.html
behave --format=json -o reports/behave_report.json
```

- `health_check.feature` — Health status and root info flows
- Steps live in `features/steps/common_steps.py`; shared environment setup in `features/environment.py`.

### Coverage & CI Commands

```bash
# Local coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html

# CI-friendly
pytest --cov=src --cov-report=xml && behave --format=json -o reports/behave.json
```

### Common Commands

```bash
make test-coverage      # Coverage run
make test-watch         # Watch mode (requires pytest-watch)
make format && make lint && make type-check
```

### Debugging Tests

```bash
pytest -s tests/test_config.py              # Show prints
pytest --pdb tests/test_config.py           # Drop into debugger
pytest -x tests/test_config.py              # Stop at first failure
pytest -vv tests/test_rest_routes.py        # Verbose
```

### Examples

```python
def test_load_defaults(monkeypatch):
    """Load settings with defaults."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    settings = Settings.load()
    assert settings.api_port == 8000
```

```gherkin
Scenario: Create a new record
  Given a database with "users" table
  When I send a POST request to /api/users with user data
  Then the response status should be 201
```

### Best Practices

- **Unit:** Use Arrange-Act-Assert, lean on fixtures for setup, keep assertions focused on one behavior.
- **BDD:** Keep steps business-focused and reusable; stick to clear Given/When/Then phrasing.

### Advanced Tips

- Mock external services (e.g., patch `graphsql.database.create_engine`) to isolate logic.
- Build database fixtures for performance or data-heavy tests; commit after inserts to keep state consistent.
- Light performance checks: time critical endpoints (e.g., `GET /api/users?limit=1000`) and assert reasonable bounds.

### Common Issues

- `ModuleNotFoundError: No module named 'graphsql'` → install in editable mode: `pip install -e .`.
- SQLite locked errors → use in-memory DB for tests: `DATABASE_URL=sqlite:///:memory:`.
- Behave cannot find steps → ensure structure `features/steps/__init__.py` exists and steps are under `features/steps/`.

### Workflow Helpers

```bash
# Pre-commit hook to run tests
echo "pytest && behave" > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

# Watch mode (requires pytest-watch)
ptw

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

### References

- [Pytest Documentation](https://docs.pytest.org/)
- [Behave Documentation](https://behave.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

## 🔍 Troubleshooting

### Database Connection Issues

**Problem: "Can't connect to database"**

```bash
# 1. Verify DATABASE_URL format
echo $DATABASE_URL

# 2. Test database connectivity
python -c "from sqlalchemy import create_engine; \
  engine = create_engine('$DATABASE_URL'); \
  conn = engine.connect(); \
  print('OK')"

# 3. Check credentials
# PostgreSQL: psql -U user -d dbname -h localhost
# MySQL: mysql -u user -p -h localhost

# 4. Verify firewall/network
# PostgreSQL: nc -zv localhost 5432
# MySQL: nc -zv localhost 3306
```

**Problem: "Table not found"**

```bash
# 1. Verify tables exist in database
curl http://localhost:8000/api/tables

# 2. Check database permissions
# Database user must have SELECT on tables

# 3. Restart server after adding tables
graphsql-start
```

### API Startup Issues

**Problem: "Port already in use"**

```bash
# Find process using port
lsof -i :8000

# Use different port
API_PORT=9000 graphsql-start

# Or kill existing process
kill -9 <PID>
```

**Problem: "Module not found"**

```bash
# Verify installation
python -c "import graphsql; print(graphsql.__file__)"

# Reinstall package
uv pip install -e .
```

### Docker Issues

**Problem: "Build fails"**

```bash
# Build with verbose output
docker build -t graphsql:latest . --progress=plain

# Check Dockerfile syntax
docker build -t graphsql:latest . --no-cache
```

**Problem: "Container exits immediately"**

```bash
# Check logs
docker logs <container-id>

# Run with interactive shell
docker run -it graphsql:latest /bin/bash

# Verify environment
docker run -e DATABASE_URL=sqlite:///test.db \
  -it graphsql:latest python -c "from graphsql.config import Settings; print(Settings.load())"
```

### Kubernetes Issues

**Problem: "Pod CrashLoopBackOff"**

```bash
# Check pod logs
kubectl logs <pod-name> --previous

# Describe pod for events
kubectl describe pod <pod-name>

# Check database connectivity from pod
kubectl exec <pod-name> -- curl http://localhost:8000/health
```

**Problem: "ImagePullBackOff"**

```bash
# Verify image exists
docker image ls | grep graphsql

# Check image registry credentials
kubectl get secrets

# Manually pull image
docker pull myregistry/graphsql:latest
```

**Problem: "Cannot reach service"**

```bash
# Check service
kubectl get svc graphsql

# Port forward to test locally
kubectl port-forward svc/graphsql 8000:80

# Verify pod network connectivity
kubectl exec <pod-name> -- curl http://localhost:8000/health
```

## 🏗️ Architecture

### Technology Stack

```
┌─────────────────────────────────────────────────────┐
│ Client Applications (Web, Mobile, CLI)              │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  FastAPI Server │ (Async web framework)
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────┐          ┌────────▼───┐
│REST API │          │ GraphQL API│ (Strawberry)
└────┬────┘          └────────┬───┘
     │                        │
     └────────────┬───────────┘
                  │
         ┌────────▼────────┐
         │ SQLAlchemy ORM  │ (Database abstraction)
         └────────┬────────┘
                  │
         ┌────────▼────────────┐
         │ Automap Reflection  │ (Dynamic schema)
         └────────┬────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐  ┌──────▼──────┐  ┌──▼────┐
│SQLite │  │ PostgreSQL  │  │ MySQL  │
└───────┘  └─────────────┘  └────────┘
```

### Request Flow

```
1. Client Request
   └─> HTTP/GraphQL

2. FastAPI Receives Request
   └─> Route Handler (REST or GraphQL)

3. Database Query
   └─> SQLAlchemy Model
   └─> SQL Execution

4. Result Processing
   └─> clean_dict() serialization (handle types)
   └─> JSON response

5. Client Receives Data
   └─> JSON (REST)
   └─> GraphQL JSON (GraphQL)
```

### Database Reflection

```
1. Application Startup
   └─> Create SQLAlchemy Engine with DATABASE_URL
   └─> Create automap_base()
   └─> reflect() tables and columns

2. Dynamic Schema Generation
   └─> Iterate reflected tables
   └─> Create Strawberry types for each table
   └─> Generate REST routes
   └─> Build GraphQL schema

3. Runtime Operation
   └─> Requests use reflected models
   └─> Changes to database schema reflected on restart
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run code quality checks:
   ```bash
   black src/
   ruff check src/
   mypy src/
   pytest
   ```
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) file for details.

### License Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ⚠️ Trademark
- ⚠️ Liability
- ⚠️ Warranty

## 📞 Support

- **Documentation:** See this README and `/docs` folder
- **Issues:** [GitHub Issues](https://github.com/your-repo/graphsql/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/graphsql/discussions)

## 📊 Changelog

### v0.1.0 (Initial Release)

**Features:**
- Automatic REST API for all database tables
- Automatic GraphQL API with Strawberry
- Support for PostgreSQL, MySQL, SQLite
- Complete CRUD operations
- Pagination support
- API documentation (Swagger/ReDoc)
- GraphQL Playground
- Docker containerization with multi-stage build
- Kubernetes-ready with complete Helm chart
- Comprehensive logging with loguru
- Environment configuration with python-decouple
- Google-style docstrings throughout
- Sphinx documentation with autodoc

**Infrastructure:**
- Docker: Multi-stage build, non-root user, health checks
- Kubernetes: 1.20+ support with Helm 3.0+ chart
- Helm: 10 templates, HPA, NetworkPolicy, persistence, ingress
- Logging: loguru with structured output
- Code Quality: black, ruff, mypy, pytest

**Documentation:**
- Comprehensive README with Quick Start, installation, configuration, usage examples
- Sphinx documentation with Google-style docstring parsing
- Curl examples in REST endpoint docstrings
- Helm chart values documentation
- Docker and kubernetes deployment guides

---

**Made with ❤️ for developers who love APIs**
