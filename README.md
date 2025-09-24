# Flask Health App - Kubernetes Deployment with CI/CD

A comprehensive Flask web application deployed on Amazon EKS with a complete CI/CD pipeline, logging infrastructure, and security scanning.

## Architecture Overview

This project includes:
- **Flask Web Application** with health check endpoints
- **Amazon EKS Cluster** for container orchestration
- **GitHub Actions CI/CD Pipeline** with security scanning
- **EFK Stack** (Elasticsearch, FluentBit, Kibana) for logging
- **Helm Charts** for application deployment
- **NGINX Ingress Controller** for traffic management
- **Cert-Manager** for SSL/TLS certificates

---

## How to Set Up the Cluster

### Prerequisites

- AWS CLI configured with appropriate credentials
- kubectl installed
- eksctl installed
- Helm 3 installed

### Step 1: Create EKS Cluster

```bash
# Create EKS cluster with 2 t2.medium nodes
eksctl create cluster \
  --name ebryx-cluster \
  --region us-east-1 \
  --nodegroup-name my-custom-ng \
  --nodes 2 \
  --node-type t2.medium

# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name ebryx-cluster
```

### Step 2: Install Helm

```bash
# Install Helm 3
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Step 3: Install NGINX Ingress Controller

```bash
# Add NGINX Ingress Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX Ingress Controller
helm install my-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### Step 4: Install Cert-Manager (SSL/TLS)

```bash
# Install cert-manager for automatic SSL certificate management
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
```

### Step 5: Set Up EBS CSI Driver

```bash
# Associate OIDC provider
eksctl utils associate-iam-oidc-provider \
  --region us-east-1 \
  --cluster ebryx-cluster \
  --approve

# Create IAM service account for EBS CSI driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster ebryx-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve

# Get IAM role ARN
ARN=$(aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole --query 'Role.Arn' --output text)

# Install EBS CSI driver addon
eksctl create addon --cluster ebryx-cluster --name aws-ebs-csi-driver --version latest \
    --service-account-role-arn $ARN --force
```

### Step 6: Deploy EFK Stack (Elasticsearch, FluentBit, Kibana)

```bash
# Create logging namespace
kubectl create namespace logging

# Add Elastic Helm repository
helm repo add elastic https://helm.elastic.co

# Install Elasticsearch
helm install elasticsearch \
  --set replicas=1 \
  --set volumeClaimTemplate.storageClassName=gp2 \
  --set persistence.labels.enabled=true \
  elastic/elasticsearch -n logging

# Get Elasticsearch credentials
kubectl get secrets --namespace=logging elasticsearch-master-credentials -ojsonpath='{.data.username}' | base64 -d
kubectl get secrets --namespace=logging elasticsearch-master-credentials -ojsonpath='{.data.password}' | base64 -d

# Add FluentBit Helm repository
helm repo add fluent https://fluent.github.io/helm-charts

# Install FluentBit with custom configuration
helm install fluent-bit fluent/fluent-bit -f fluentbit-values.yaml -n logging

# Install Kibana
helm install kibana elastic/kibana -n logging
```

### Step 7: Deploy Flask Application

```bash
# Deploy the Flask application using Helm
helm upgrade --install flask-health-app ./simple-helm/flask-app \
  --namespace flask-app \
  --create-namespace
```

---

## How to Run the Pipeline

### GitHub Actions CI/CD Pipeline

The pipeline is automatically triggered on:
- **Push to main branch**
- **Manual workflow dispatch**

### Pipeline Stages

1. **Security Scanning Stage**
   - SAST (Static Application Security Testing) with SonarCloud
   - Dependency scanning with OWASP Dependency-Check
   - Only proceeds if no High/Critical vulnerabilities found

2. **Test Stage**
   - Python unit tests using pytest
   - Code coverage reporting
   - Test artifacts uploaded

3. **Build Stage**
   - Multi-stage Docker image build
   - Dockerfile security linting with Hadolint
   - Images tagged with short Git SHA (e.g., `k8s-assessment:a1b2c3d`)

4. **Image Security Stage**
   - Container vulnerability scanning with Trivy
   - Pipeline fails only on CRITICAL vulnerabilities
   - HIGH/MEDIUM/LOW vulnerabilities are acceptable

5. **Push Stage**
   - Push to Amazon ECR only if security scans pass
   - Images tagged with Git SHA and `latest`

6. **Deploy Stage**
   - Deploy to EKS using Helm
   - Verification of deployment status

### Manual Pipeline Trigger

1. Navigate to your GitHub repository
2. Go to **Actions** tab
3. Select **Build and Push to ECR** workflow
4. Click **Run workflow**
5. Choose branch (main) and click **Run workflow**

### Required GitHub Secrets

Configure these secrets in your GitHub repository:

```
AWS_ACCESS_KEY_ID          # AWS access key for ECR and EKS
AWS_SECRET_ACCESS_KEY      # AWS secret key
EKS_CLUSTER_NAME          # Name of your EKS cluster (ebryx-cluster)
SONAR_TOKEN               # SonarCloud authentication token
GITHUB_TOKEN              # GitHub token (automatically provided)
```

---

## Security Measures Implemented

### 1. Static Application Security Testing (SAST)
- **SonarCloud** integration for code quality and security analysis
- **Quality Gate** enforcement - pipeline fails if quality standards not met
- **Automatic code scanning** on every commit

### 2. Dependency Vulnerability Scanning
- **OWASP Dependency-Check** for known vulnerabilities in dependencies
- **Pipeline failure** on High/Critical vulnerabilities
- **Detailed reports** uploaded as artifacts

### 3. Container Security
- **Multi-stage Docker builds** for minimal attack surface
- **Non-root user** execution in containers
- **Dockerfile linting** with Hadolint for security best practices
- **Trivy vulnerability scanning** of container images
- **CRITICAL vulnerability blocking** - pipeline fails and prevents deployment

### 4. Infrastructure Security
- **Private subnets** for worker nodes
- **IAM roles** with least privilege access
- **Network policies** for pod-to-pod communication control
- **TLS/SSL encryption** with cert-manager and Let's Encrypt

### 5. Runtime Security
- **Resource limits and requests** for all containers
- **Health checks** (liveness and readiness probes)
- **Security contexts** with restricted capabilities
- **Kubernetes secrets** for sensitive data management

### 6. CI/CD Security
- **Workflow secrets** for credential management
- **No hardcoded credentials** in code or configurations
- **Separate environments** for different deployment stages
- **Audit trail** through GitHub Actions logs

---

## Live Application Access

### Flask Health Check Application

Your Flask application is live and accessible at: **[https://flask.yimo.world/](https://flask.yimo.world/)**

#### Available Endpoints:

- **Main Dashboard:** `https://flask.yimo.world/`
- **Readiness Probe:** `https://flask.yimo.world/healthz`
- **Liveness Probe:** `https://flask.yimo.world/failcheck`
- **Toggle Readiness:** `https://flask.yimo.world/toggle-readiness`
- **Toggle Liveness:** `https://flask.yimo.world/toggle-liveness`

#### Application Features:
- ✅ Modern responsive UI with real-time status
- ✅ Kubernetes health check endpoints
- ✅ Interactive toggle functionality for testing
- ✅ SSL/TLS encryption via HTTPS
- ✅ Load balancer integration
- ✅ Auto-scaling capabilities

#### Testing the Application:

```bash
# Test readiness probe
curl https://flask.yimo.world/healthz

# Test liveness probe
curl https://flask.yimo.world/failcheck

# Toggle readiness state for testing
curl https://flask.yimo.world/toggle-readiness

# Toggle liveness state for testing
curl https://flask.yimo.world/toggle-liveness
```

---

## How to Access the Kibana Dashboard

### Live Application URLs

- **Flask Application:** [https://flask.yimo.world/](https://flask.yimo.world/)
- **Kibana Dashboard:** [http://ae1f434adf906422f833581d6ed5b6d8-2141573473.us-east-1.elb.amazonaws.com:5601/](http://ae1f434adf906422f833581d6ed5b6d8-2141573473.us-east-1.elb.amazonaws.com:5601/)

### Step 1: Access Your Live Kibana Dashboard

Your Kibana dashboard is accessible at:
```
http://ae1f434adf906422f833581d6ed5b6d8-2141573473.us-east-1.elb.amazonaws.com:5601/
```

**Note:** If you see "Please upgrade your browser" message, try accessing with:
- **Chrome/Chromium** (latest version)
- **Firefox** (latest version)
- **Safari** (latest version)

### Step 2: Alternative Access Methods

#### Option A: Port Forward (If direct access fails)

```bash
# Forward Kibana port to local machine
kubectl port-forward -n logging svc/kibana-kibana 5601:5601

# Access via browser
open http://localhost:5601
```

#### Option B: Ingress Configuration (Already configured)

```bash
# Create Kibana Ingress (if not already configured)
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kibana-ingress
  namespace: logging
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - kibana.yourdomain.com
    secretName: kibana-tls
  rules:
  - host: kibana.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kibana-kibana
            port:
              number: 5601
EOF
```

### Step 3: Kibana Login Credentials

```bash
# Get Elasticsearch username (usually 'elastic')
kubectl get secrets --namespace=logging elasticsearch-master-credentials -ojsonpath='{.data.username}' | base64 -d

# Get Elasticsearch password
kubectl get secrets --namespace=logging elasticsearch-master-credentials -ojsonpath='{.data.password}' | base64 -d
```

**Default Credentials:**
- **Username:** `elastic`
- **Password:** Use the output from the command above

### Step 4: Configure Kibana for Flask App Logs

1. **Access Kibana** at `http://localhost:5601`
2. **Login** with Elasticsearch credentials
3. **Create Index Pattern:**
   - Go to **Management** → **Stack Management** → **Index Patterns**
   - Click **Create index pattern**
   - Enter pattern: `logstash-*` or `abhishek-flask-app-*`
   - Select timestamp field: `@timestamp`
   - Click **Create index pattern**

4. **View Flask App Logs:**
   - Go to **Analytics** → **Discover**
   - Select your index pattern
   - Filter by: `kubernetes.container_name: flask-health-app`
   - View HTTP access logs with extracted fields:
     - `http.method` (GET, POST, etc.)
     - `http.path` (/healthz, /, etc.)
     - `http.status_code` (200, 404, 500, etc.)
     - `http.remote_addr` (client IP)

### Sample Kibana Queries

```bash
# View only Flask app logs
kubernetes.container_name: "flask-health-app"

# View HTTP access logs with status codes
kubernetes.container_name: "flask-health-app" AND http.status_code: 200

# View error logs
kubernetes.container_name: "flask-health-app" AND http.status_code: [400 TO 599]

# View health check requests
kubernetes.container_name: "flask-health-app" AND http.path: "/healthz"
```

---

## Troubleshooting

### Common Issues

1. **Pipeline Fails on Vulnerability Scan:**
   - Check Trivy scan results in GitHub Actions artifacts
   - Only CRITICAL vulnerabilities block deployment
   - Update base image or dependencies to fix vulnerabilities

2. **Kibana Not Accessible:**
   - Check if Kibana pod is running: `kubectl get pods -n logging -l app=kibana`
   - Verify port-forward: `kubectl port-forward -n logging svc/kibana-kibana 5601:5601`
   - Check Elasticsearch connectivity

3. **Flask App Not Receiving Traffic:**
   - Verify ingress controller: `kubectl get pods -n ingress-nginx`
   - Check service: `kubectl get svc -n flask-app flask-health-app`
   - Verify deployment: `kubectl get deployment -n flask-app flask-health-app`

4. **Logs Not Appearing in Kibana:**
   - Check FluentBit status: `kubectl get pods -n logging -l app.kubernetes.io/name=fluent-bit`
   - Verify FluentBit logs: `kubectl logs -n logging -l app.kubernetes.io/name=fluent-bit`
   - Ensure Elasticsearch is healthy: `kubectl get pods -n logging -l app=elasticsearch-master`

### Useful Commands

```bash
# Check all pods status
kubectl get pods --all-namespaces

# View Flask app logs directly
kubectl logs -n flask-app -l app=flask-health-app -f

# Check ingress status
kubectl get ingress --all-namespaces

# Restart FluentBit if logs not flowing
kubectl rollout restart daemonset/fluent-bit -n logging

# Check Elasticsearch cluster health
kubectl exec -n logging elasticsearch-master-0 -- curl -X GET "localhost:9200/_cluster/health?pretty"
```

---

## Project Structure

```
flask_app_assessment/
├── app/                          # Flask application
│   ├── app.py                   # Main application file
│   ├── Dockerfile               # Multi-stage Docker build
│   ├── requirements.txt         # Python dependencies
│   ├── templates/               # HTML templates
│   ├── tests/                   # Unit tests
│   └── sonar-project.properties # SonarCloud configuration
├── simple-helm/flask-app/       # Helm chart
│   ├── Chart.yaml              # Chart metadata
│   ├── values.yaml             # Default values
│   └── templates/              # Kubernetes manifests
├── .github/workflows/           # CI/CD pipelines
│   └── build-and-push-ecr.yml  # Main pipeline
├── fluentbit-values.yaml        # FluentBit configuration
└── README.md                    # This file
```

---

## Key Features

- ✅ **Multi-stage Docker builds** for optimized images
- ✅ **Comprehensive security scanning** (SAST, dependency, container)
- ✅ **Automated testing** with coverage reporting
- ✅ **GitOps deployment** with Helm
- ✅ **Centralized logging** with HTTP field extraction
- ✅ **SSL/TLS termination** with automatic certificate management
- ✅ **Resource management** with requests/limits and HPA
- ✅ **Health monitoring** with liveness/readiness probes
- ✅ **Network security** with ingress controls

---

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review GitHub Actions logs for pipeline issues
3. Check Kubernetes pod logs for runtime issues
4. Verify Kibana dashboards for application monitoring

**Repository:** https://github.com/abdulmoizz44/ebryx-k8s-project
