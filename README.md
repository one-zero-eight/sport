# InnoSport website

[![Tests](https://github.com/one-zero-eight/sport/actions/workflows/tests.yaml/badge.svg)](https://github.com/one-zero-eight/sport/actions/workflows/tests.yaml)
[![Production deploy](https://github.com/one-zero-eight/sport/actions/workflows/deploy_production.yaml/badge.svg)](https://github.com/one-zero-eight/sport/actions/workflows/deploy_production.yaml)

The platform for conducting, tracking and checking students' sports activity at Innopolis University.

## Development

### Set up for development

1. Install [Python 3.12](https://www.python.org/downloads/), [Poetry](https://python-poetry.org/docs/),
   [Docker](https://docs.docker.com/engine/install/)
2. Install project dependencies with [Poetry](https://python-poetry.org/docs/cli/#options-2).
   ```bash
   cd adminpage
   poetry install
   ```
3. Copy environment variables: `cp deploy/.env.example deploy/.env` (leave default values in development)
4. Start services: `docker compose -f ./deploy/docker-compose.yaml up --build`
5. Make migrations and create superuser:
   - Enter shell: `docker compose -f ./deploy/docker-compose.yaml exec -it adminpanel bash`
   - Autocreate migration files: `python3 manage.py makemigrations`
   - Apply migrations to db: `python3 manage.py migrate`
     > If there are problems with migrations applying, try to run the same migrate command with `--fake` option.
   - Create a new superuser: `python3 manage.py createsuperuser`
6. View Admin panel at http://localhost/admin and Swagger at http://localhost/api/swagger

> [!NOTE]
> Server supports auto-reload on code change in debug mode

### Project structure

```
.
├── adminpage - Django project
│   ├── adminpage - main django app
│   │   ├── settings.py
│   │   ├── swagger.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── api
│   │   ├── crud - directory with database queries
│   │   ├── fixtures - database tools for testing
│   │   ├── serializers - DRF serializers
│   │   ├── tests
│   │   │   ├── api - endpoints tests
│   │   │   └── crud - database queries tests
│   │   └── views - api endpoints
│   ├── sport
│   │   ├── admin - django adminpage classes
│   │   ├── dumps - database dumps for tests
│   │   ├── migrations - django database migrations
│   │   ├── models - django database models
│   │   ├── signals - django ORM signal handlers
│   │   ├── static - static files for app (css, fonts, images, js)
│   │   │   └── sport
│   │   │       ├── css
│   │   │       ├── fonts
│   │   │       ├── images
│   │   │       └── js
│   │   ├── templates - django templates for app pages
│   │   └── views - app pages url handlers
├── deploy - deployment configuration
│   ├── docker-compose.yaml - development Docker Compose file
│   ├── docker-compose.prod.yaml - production Docker Compose file
│   ├── docker-compose.test.yaml - services for automatic testing
│   ├── .env.example - example of environment variables
│   ├── nginx-conf - reverse proxy configuration
│   ├── nginx-logs - request logs
│   ├── grafana-provisioning - default dashboards for Grafana
│   └── prometheus - Prometheus configs
├── scripts - development tools
└── README.md
```

## Flows

### Releasing a new version

1. Merge your changes to 'main' branch.
2. Verify that a new version works on the staging server.
3. Create a new tag with the version number in the format `vF24.22.20`,
   where F24 is the semester number and 22.20 is the release number.
   You can create the tag via GitHub releases tab.
4. Ask maintainer (@ArtemSBulgakov) to allow the deployment via GitHub Actions.
5. Verify that changes work on the production server.
