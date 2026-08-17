# Changelog

All notable changes to the KubeSight Production Observability Platform will be documented in this file.

## [1.0.0] - 2026-08-17

### Security
- Updated Docker base images from `python:3.11.11-slim` to `python:3.11-slim` for latest security patches
- Added automated OS package updates during Docker build for security vulnerability remediation
- Upgraded Python dependencies: setuptools from 65.5.1 to 84.0.0, wheel from 0.45.1 to 0.48.0
- Fixed Dockerfile ENV format warnings for compliance
- Trivy HIGH/CRITICAL vulnerability scanning now fully operational for both Docker images
- Current security status: 0 HIGH/CRITICAL vulnerabilities in both API and Frontend images

### CI/CD
- Enhanced GitHub Actions pipeline with comprehensive security scanning
- Added Trivy filesystem scanning for repository vulnerability detection
- Added Trivy Docker image scanning with HIGH/CRITICAL blocking
- Added Gitleaks secret detection for credential leak prevention
- Added Kubesec security validation for Kubernetes manifests
- All 7 CI/CD checks passing: Helm Lint, Helm Template Validation, Kubeconform, Trivy (filesystem + Docker), Gitleaks, Kubesec

### Documentation
- Updated README.md with comprehensive CI/CD pipeline documentation
- Added Docker image security section with current scan results
- Added production validation results and configuration verification
- Added security and production readiness checklists
- Updated technology stack to reflect current versions (Flask 3.0)

### Production Validation
- Verified pod failure/recovery mechanisms
- Confirmed Redis persistence across pod restarts
- Validated rolling restart with zero downtime
- Confirmed Prometheus scraping via ServiceMonitors
- Validated Helm upgrade and rollback operations
- Verified production Helm template rendering

### Platform Architecture
- Maintained existing Kubernetes/Helm architecture
- Preserved all observability stack components (Prometheus, Grafana, ServiceMonitors, PrometheusRules)
- Continued NetworkPolicy-based traffic segmentation
- Maintained HPA, PDB, and RollingUpdate configurations