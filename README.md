# Sport platform

[![Tests](https://github.com/one-zero-eight/sport/actions/workflows/tests.yaml/badge.svg)](https://github.com/one-zero-eight/sport/actions/workflows/tests.yaml)
[![Production deploy](https://github.com/one-zero-eight/sport/actions/workflows/deploy_production.yaml/badge.svg)](https://github.com/one-zero-eight/sport/actions/workflows/deploy_production.yaml)

The platform for conducting, tracking and checking students' sports activity at Innopolis University.

## Development

### Set up for development

1. Install [uv](https://docs.astral.sh/uv/), [Docker](https://docs.docker.com/engine/install/), and Docker Compose **5.3.1** (minimum **5.3.0**, required for `pre_start` hooks).
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Copy environment variables: `cp .env.example .env` (leave default values in development)
4. Start services: `docker compose up --build`
5. Make migrations and create superuser:
   - Enter shell: `docker compose exec -it app bash`
   - Autocreate migration files: `python3 manage.py makemigrations`
   - Apply migrations to db: `python3 manage.py migrate`
     > If there are problems with migrations applying, try to run the same migrate command with `--fake` option.
   - Create a new superuser: `python3 manage.py createsuperuser`
6. View Admin panel at http://localhost/admin and Swagger at http://localhost/api/swagger

> [!NOTE]
> Server supports auto-reload on code change in debug mode

### Commands

- Dump database
  ```bash
  docker compose exec -t db pg_dumpall -c -U postgres > ./sport_dump.sql
  ```
- Drop database (**dangerous!**)
  ```bash
  docker compose down
  # Dangerous!!! - immediately removes all database data
  docker volume rm sport_db-data
  ```
- Setup database from dump and apply migrations
  ```bash
  sh scripts/setup_sport_database.sh ./sport_dump.sql
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
