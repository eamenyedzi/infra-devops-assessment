# Infra‑DevOps Assessment – Quick Start Guide

This repository shows **two parallel ways** to run the solution:

| Stack                 | What it gives you                                                            | When to use                                                   |
| --------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **Docker Compose**    | Fast local spin‑up on any machine with Docker                                | Rapid iteration, no Kubernetes knowledge needed               |
| **Helm (+ Minikube)** | Production‑style manifests, optional HPA, basic‑auth, secrets, health‑checks | Showcases best practices and is closer to real‑world clusters |

---

## Design Rationale – Why this approach?

| Decision                                | Rationale                                                                |
| --------------------------------------- | ------------------------------------------------------------------------ |
| **Two runnable paths (Compose & Helm)** | Quick local testing plus production‑style deployment; shows flexibility. |
| **Nginx reverse‑proxy**                 | Lightweight, battle‑tested, native path rewriting & auth.                |
| **Separate **`** / **`** containers**   | Mirrors micro‑service boundaries; independent scaling & CI.              |
| **Non‑root images & least privilege**   | Aligns with container‑security best practices.                           |
| **Credentials via Secret**              | Keeps passwords out of Git; demo of k8s secret management.               |
| **Locust inside the cluster**           | Self‑contained load testing, drives autoscaling demo.                    |
| **HPA + resource limits**               | Shows operational readiness and auto‑scaling behaviour.                  |

___

## 1 ‒ Running with Docker Compose

### Prerequisites

* Docker ≥ 20.x installed and running.

### Steps

```bash
# 0 – clone repo & move in
 git clone https://github.com/eamenyedzi/infra-devops-assessment.git
 cd infra-devops-assessment

# 1 – build images (web1, web2)
 docker compose build

# 2 – up
 docker compose up -d

# 3 – visit
 http://localhost/1   # STELLAR page
 http://localhost/2   # BRIGHTER page
 http://localhost:8089  # load testing url

# 4 – live stats (optional)
 docker stats
```

> **Auth note:** basic‑auth is not **enabled** in Compose for convenience. Use the Kubernetes path to see auth.

---

## 2 ‒ Running with Helm + Minikube

### Prerequisites

* Docker (used to build images)
* Minikube ≥ v1.30
* Helm ≥ v3.11
* `openssl` (to hash passwords)

### 2.1  Start Minikube

```bash
minikube start
# enable metrics‑server for HPA
minikube addons enable metrics-server
```

### 2.2  Build & load local images (skip if you push to a registry)

```bash
# build
 docker build -t web1:latest ./web1
 docker build -t web2:latest ./web2
# load into the Minikube VM
 minikube image load web1:latest
 minikube image load web2:latest
```

### 2.3  Create basic‑auth secret

```bash
APPUSERNAME=admin
PASSWORD=VeryStrongP@ssw0rd
printf "%s:$(openssl passwd -apr1 $PASSWORD)" "$APPUSERNAME" \
  | kubectl create secret generic web-basic-auth \
      --from-literal=username="$APPUSERNAME" \
      --from-literal=password="$PASSWORD" \
      --from-file=.htpasswd=/dev/stdin
```

### 2.4  Install / upgrade the chart

```bash
helm upgrade --install infra-dev ./helm \
  --set auth.enabled=true
```

### 2.5  Access the app

```bash
# Easy port‑forward
kubectl port-forward svc/reverse-proxy 8080:80
# then in browser
http://localhost:8080/1   # prompts for basic‑auth, then STELLAR page
http://localhost:8080/2   # BRIGHTER page
```


### 2.6  Run the Locust load‑test UI

```bash
kubectl port-forward svc/locust 8089:8089 &
open http://localhost:8089
```

Start a test with 100 users, 10 spawn rate → watch stats.

### 2.7  Autoscaling demo (optional)

In the Locust UI set 300 users / 30 spawn rate
```bash
# Pump CPU load until HPA scales web1/web2
kubectl get hpa --watch
```

### 2.8  Cleanup

```bash
helm uninstall infra-dev
minikube delete
```

---

## Folder Layout

```
├── docker-compose.yml        # Compose stack
├── helm/                     # Helm chart (templates, values)
├── web1/  web2/              # Dockerfile + static site for each product
└── load-test/locustfile.py   # Locust traffic definition
```

---

## Troubleshooting

| Symptom                                                                    | Fix                                                                                                      |        |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------ |
| `ImagePullBackOff`                                                         | Did you `minikube image load` or push to a registry?                                                     |        |
| `401 Unauthorized` everywhere                                              | Ensure the secret `web-basic-auth` exists and matches the user/pass you enter                            |        |
| HPA never scales                                                           | `minikube addons enable metrics-server` and ensure CPU load is high enough                               |        |
| Need to see container logs                                                 | **Compose:** `docker compose logs -f web1`  ·  **K8s:** `kubectl logs -l app=reverse-proxy --tail=50 -f` |        |
| Pod keeps restarting                                                       | `kubectl describe pod <name>` → check Events for crashes / probe failures                                |        |
| Debug inside a pod                                                         | `kubectl exec -it <pod> -- sh` then `curl -I http://localhost/`                                          |        |
| Cluster‑wide events                                                        | `kubectl get events --sort-by=.metadata.creationTimestamp`                                               |        |
| Inspect deployment YAML                                                    | \`kubectl get deploy reverse-proxy -o yaml                                                               | less\` |
| `minikube addons enable metrics-server` and ensure CPU load is high enough |                                                                                                          |        |

---

## Security & Best‑Practice Notes

* **No credentials** are stored in Git. Password hashes live in a Kubernetes **Secret**.
* Containers run **non‑root**; paths are pre‑`chown`ed.
* Nginx basic‑auth is optional (`auth.enabled=false`).
* Resource requests/limits and HPAs show production readiness.

---

## Potential Improvements / Next Steps

| Area                            | What to add                                                                                                                                                                        | Why it helps                                           |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **TLS & Ingress**               | Use an *IngressController* (nginx‑ingress or Traefik) and Cert‑Manager to issue free Let’s Encrypt certificates.                                                                   | HTTPS in dev mirrors prod; automatic renewals.         |
| **CI/CD**                       | GitHub Actions / GitLab CI pipeline that:<br>1. Builds & scans images with Trivy<br>2. Pushes to a registry<br>3. Runs `helm lint` + `helm test`<br>4. Deploys to a test namespace | Repeatable, automated, secure delivery.                |
| **Observability**               | Add Prometheus + Grafana Helm charts;<br>export Nginx metrics via the `nginx-prometheus-exporter`; <br>ship logs to Loki or Elasticsearch.                                         | Insight into latency, error rates, capacity planning.  |
| **Ingress rate‑limiting / WAF** | Enable Nginx ModSecurity or cloud‑native rate limits.                                                                                                                              | Protects against brute force and bad actors.           |
| **Helm chart signing**          | `helm package --sign` with cosign / PGP.                                                                                                                                           | Verifiable supply‑chain integrity.                     |

---
