# Kubernetes and Helm Deployment

This project is containerized and ready for Kubernetes deployment using Helm.

## Docker

### Build image locally

```bash
docker build -t graphsql:0.1.0 .
```

### Run with docker-compose

```bash
# Standalone mode (SQLite)
docker-compose up graphsql-standalone

# With PostgreSQL
docker-compose --profile with-db up
```

## Kubernetes

### Prerequisites

- Kubernetes cluster (1.20+)
- `kubectl` configured
- Helm 3.0+

### Quick start with Helm

1. **Add Helm chart repository** (if publishing to a repo):

```bash
helm repo add graphsql https://charts.example.com
helm repo update
```

2. **Install the chart**:

```bash
helm install graphsql ./helm \
  --namespace graphsql \
  --create-namespace \
  --values helm/values.yaml
```

3. **With custom database**:

```bash
helm install graphsql ./helm \
  --namespace graphsql \
  --create-namespace \
  --set database.host=postgres.example.com \
  --set database.port=5432 \
  --set database.name=graphsql \
  --set database.user=graphsql \
  --set database.password=secret123
```

### Configuration

Key Helm values (see `helm/values.yaml` for complete reference):

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | 2 | Number of deployment replicas |
| `image.repository` | `afeldman/graphsql` | Container image |
| `image.tag` | `0.1.0` | Image tag |
| `config.logLevel` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `config.corsOrigins` | `*` | Allowed CORS origins |
| `database.url` | `` | External database URL (overrides host/port/name) |
| `database.host` | `` | Database hostname |
| `database.port` | `5432` | Database port |
| `database.name` | `graphsql` | Database name |
| `autoscaling.enabled` | `true` | Enable HPA |
| `autoscaling.minReplicas` | 2 | Minimum pods |
| `autoscaling.maxReplicas` | 5 | Maximum pods |
| `ingress.enabled` | `false` | Enable Ingress |

### Enable Ingress

```bash
helm install graphsql ./helm \
  --namespace graphsql \
  --create-namespace \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=api.example.com \
  --set ingress.tls[0].hosts[0]=api.example.com \
  --set ingress.tls[0].secretName=graphsql-tls
```

### View Helm values

```bash
helm show values ./helm
```

### Upgrade deployment

```bash
helm upgrade graphsql ./helm \
  --namespace graphsql \
  --values custom-values.yaml
```

### Uninstall

```bash
helm uninstall graphsql --namespace graphsql
```

## Kubernetes Manifests

Raw Kubernetes manifests are generated from the Helm chart. To deploy without Helm:

```bash
helm template graphsql ./helm > manifests.yaml
kubectl apply -f manifests.yaml
```

## Security

- **Non-root user**: Runs as UID 1000
- **Read-only filesystem**: Can be enabled for additional hardening
- **Network Policy**: Available for cluster-level traffic control
- **Pod Security Context**: Enforced to prevent privilege escalation
- **Health checks**: Liveness and readiness probes configured
- **Resource limits**: CPU and memory limits enforced

## Monitoring

Optional Prometheus integration via ServiceMonitor:

```bash
helm install graphsql ./helm \
  --set serviceMonitor.enabled=true
```

## Persistence

To persist data (e.g., for SQLite):

```bash
helm install graphsql ./helm \
  --set persistence.enabled=true \
  --set persistence.storageClassName=standard \
  --set persistence.size=10Gi
```

## Environment Variables

All configuration is passed via environment variables (python-decouple):

- `DATABASE_URL`: Full database connection string
- `API_HOST`: Bind address (default: 0.0.0.0)
- `API_PORT`: Bind port (default: 8000)
- `CORS_ORIGINS`: Comma-separated origins (default: *)
- `LOG_LEVEL`: Log verbosity (default: INFO)
- `DEFAULT_PAGE_SIZE`: REST/GraphQL page size (default: 50)
- `MAX_PAGE_SIZE`: Max pagination size (default: 1000)

See `.env.example` for complete reference.

## Troubleshooting

### Check pod logs

```bash
kubectl logs -n graphsql -l app.kubernetes.io/name=graphsql
```

### Check pod status

```bash
kubectl get pods -n graphsql -o wide
```

### Describe pod for events

```bash
kubectl describe pod -n graphsql <pod-name>
```

### Port forward to test locally

```bash
kubectl port-forward -n graphsql svc/graphsql 8000:80
curl http://localhost:8000/health
```

## Building and publishing Docker image

```bash
# Build
docker build -t graphsql:0.1.0 .

# Tag for registry
docker tag graphsql:0.1.0 registry.example.com/graphsql:0.1.0

# Push
docker push registry.example.com/graphsql:0.1.0

# Update Helm values
helm install graphsql ./helm \
  --set image.repository=registry.example.com/graphsql \
  --set image.tag=0.1.0
```
