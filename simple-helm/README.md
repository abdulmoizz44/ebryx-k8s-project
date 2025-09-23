# Simple Flask App Helm Chart

Ultra-simple Helm chart for deploying Flask Health Check application.

## 🚀 Quick Deploy

```bash
# Deploy with default settings
helm install flask-health-app ./simple-helm/flask-app --namespace flask-app --create-namespace

# Or use the script
chmod +x simple-deploy.sh
./simple-deploy.sh
```

## ⚙️ Configuration

Edit `values.yaml` to customize:

```yaml
# Change replicas
replicas: 3

# Change image tag
image:
  tag: v1.2.3

# Enable ingress
ingress:
  enabled: true
  host: your-domain.com

# Change service type
service:
  type: LoadBalancer
```

## 📊 Common Commands

```bash
# Check status
kubectl get all -n flask-app

# Access app
kubectl port-forward svc/flask-health-app 8080:80 -n flask-app
curl http://localhost:8080/healthz

# Update
helm upgrade flask-health-app ./simple-helm/flask-app

# Uninstall
helm uninstall flask-health-app -n flask-app
```

## 📁 Chart Structure

```
simple-helm/flask-app/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Configuration values
└── templates/
    ├── deployment.yaml  # App deployment
    ├── service.yaml     # Service
    ├── secret.yaml      # Secrets
    ├── hpa.yaml         # Auto-scaling
    └── ingress.yaml     # External access
```

That's it! Simple and clean. ✨
