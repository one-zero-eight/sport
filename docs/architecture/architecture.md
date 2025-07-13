## Tech Stack

### 1. Programming Languages
- **Python** 3.12
- **Bash** (shell scripting)
- **SQL**
- **YAML** (configuration)

### 2. Frameworks and Libraries
#### Backend
- **Django** 5.1.3 — web framework for rapid development and clean design
- **Django REST Framework** — API toolkit for building Web APIs
- **drf-spectacular** ^0.28.0 — OpenAPI 3 schema generation and documentation
- **Django Apps / Extensions**:
  - django-cors-headers — CORS support
  - django-prometheus — metrics instrumentation
  - django-hijack — user session hijacking for support
  - django-auth-adfs — Azure AD authentication
  - django-sendfile2 — efficient file serving
  - django-smartfields — enhanced model field handling
  - django-admin-autocomplete-filter — admin filters
  - django-admin-rangefilter — admin range filters
  - django-import-export — import/export in admin
  - django-pglock — advisory locking
  - django-revproxy — reverse proxy in Django
  - django-image-optimizer — image optimization

#### Data Processing & Utilities
- **Pillow** 9.5.0 — image processing
- **OpenPyXL** 3.1.5 — Excel file handling
- **requests** 2.32.3 — HTTP requests
- **PyJWT** 2.4.0 — JSON Web Tokens
- **cryptography** — RSA key handling

#### Testing & Quality
- **pytest** 8.3.3
- **pytest-django** 4.9.0
- **pytest-freezegun** (Git) — time-freezing fixtures
- **flake8** — linting
- **vulture** — dead code detection
- **GitHub Super-Linter** (React.js context)

### 3. Containerization & Orchestration
- **Docker** — containerization
- **Docker Compose** — multi-container environments
- **Dockerfile** (multi-stage build)

### 4. Deployment & Server
- **Uvicorn** 0.32.1 — ASGI server
- **NGINX** — reverse proxy configuration
- **Gunicorn** (not used; Uvicorn workers)
- **Unix Shell Scripts**:
  - database setup (`scripts/setup_sport_database.sh`)
  - migration & collectstatic (`docker-entrypoint.sh`)

### 5. Database & Caching
- **PostgreSQL** — relational database
- **psycopg2-binary** 2.9.10 — PostgreSQL driver
- **Django DatabaseCache** — table-based cache backend

### 6. Continuous Integration & Delivery
- **GitHub Actions**:
  - **tests.yaml** — automated testing pipeline
  - **deploy_staging.yaml** — staging deployment
  - **deploy_production.yaml** — production deployment
- **Poetry** — dependency management
- **Make / Shell commands** — project setup and management

### 7. Monitoring & Observability
- **Prometheus** — metrics collection (`deploy/prometheus/prometheus.yml`)
- **Grafana** — dashboards provisioning (`deploy/grafana-provisioning`)
- **Sentry** 2.19.0 — error tracking

### 8. Documentation & API Exploration
- **Swagger UI** (via drf-spectacular sidecar)
- **Markdown** — project documentation
- **OpenAPI 3.1** — API specification

### 9. Security & Authentication
- **Azure AD / ADFS** — OAuth2/OpenID Connect
- **InNoHassle JWT** — custom token authentication
- **django-cors-headers** — CORS policy management
- **Environment Variables** — configuration via .env files

### 10. Project Structure & Configuration
- **EditorConfig** — code style consistency
- **PyProject.toml / Poetry.lock** — Python project metadata
- **.env** samples for different environments (development, test, production)
- **pytest.ini** — test discovery and settings
- **.github/** — issue and pull request templates

---
