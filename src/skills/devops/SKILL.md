---
name: devops
description: DevOps, CI/CD, Docker, Kubernetes. Use for deployment and infrastructure.
triggers:
 - docker
 - kubernetes
 - ci
 - cd
 - deployment
 - deploy
 - dockerfile
 - container
 - github actions
 - github actions
 - pipeline
---

# DevOps Expertise

## Docker

### Dockerfile Best Practices
```dockerfile
# Use specific version tags
FROM python:3.12-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code last
COPY . .

# Non-root user
USER app

CMD ["python", "main.py"]
```

### Docker Commands
```bash
# Build
docker build -t myapp .

# Run
docker run -p 8080:8080 myapp

# Compose
docker-compose up -d

# Logs
docker logs -f container
```

## CI/CD

### GitHub Actions
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest
```

### Common Pipelines
- **GitHub Actions** - GitHub native
- **GitLab CI** - GitLab native
- **Jenkins** - Self-hosted

## Deployment

### Options
| Platform | Use |
|----------|-----|
| Vercel | Frontend, Next.js |
| Railway | Full-stack |
| Fly.io | Docker apps |
| AWS ECS | Kubernetes |
| Render | Simple apps |

### Environment Variables
```bash
# Never commit secrets!
# Use .env.local for dev
# Use secrets management in prod
```

## Monitoring

```bash
# Logs
kubectl logs -f pod/name

# Metrics
curl localhost:9090/metrics

# Health checks
curl localhost:8080/health
```