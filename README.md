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
3. Copy environment variables: `cp deploy/.env.example deploy/.env`
4. Start services: `docker compose -f ./deploy/docker-compose.yaml up`
5. Make migrations and create superuser:
   - Enter shell: `docker compose -f ./deploy/docker-compose.yaml exec -it adminpanel bash`
   - Autocreate migration files: `python manage.py makemigrations`
   - Apply migrations to db: `python manage.py migrate`
     > If there are problems with migrations applying, try to run the same migrate command with `--fake` option.
   - Create a new superuser: `python manage.py createsuperuser`
6. View admin panel at `http://localhost/admin`

> [!NOTE]
> Server supports auto-reload on code change in debug mode

API documentation:
* Swagger is at http://localhost/api/swagger
* Redoc is at http://localhost/api/redoc

### Environment Variables

See `deploy/.env.example` for reference.

The project requires a file `deploy/.env` with the following environment variables:

* `POSTGRES_USER`- Username for the db
* `POSTGRES_PASSWORD`- database password
* `POSTGRES_DB` - database name
* `POSTGRES_SERVER` - database hostname (`db` - by default)
* `GRAFANA_DB_USER` - username for database user for grafana (will be created if not exists)
* `GRAFANA_DB_PASSWORD` - password for database grafana user
* `GF_SECURITY_ADMIN_PASSWORD` - admin password for Grafana Dashboard
* `SECRET_KEY` - a secret key for token verifications
* `PROJECT_NAME`- project title
* `SCHEMA` - schema of a web page (prefer `https`)
* `HOSTNAME` - hostname of a web page e.g: `example.com`
* `PORT` - port over which web page is served
* `PYTHON_VERSION` - which python version is to be used (specify exact version)
* `DEBUG`- boolean flag for DEBUG mode ( `true` enables fake login and Django debug)
* `oauth_appID` - application ID for oauth
* `oauth_shared_secret` - application secret for ouath
* `oauth_authorization_baseURL`- an URL for user auth
* `oauth_get_infoURL`- tokeninfo URL
* `oauth_tokenURL`- an URL to obtain token
* `oauth_end_session_endpoint`- end oauth session endpoint

You can leave the default values for development.

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

### Changing JS or CSS

When changing JS scripts or CSS styles,
you also should update 'JS_VERSION' setting in `adminpage/adminpage/settings.py`.
This is needed to update the cache in browsers.

