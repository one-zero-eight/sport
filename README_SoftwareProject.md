# Development
## Kanban board
https://github.com/orgs/inno-sport-inh/projects/1
### Entry criterias:
#### Todo
The task was planned, but not started
#### In Progress
The work on the task started, but not completed and doesn't comply DoD
#### Done
- Code is written and committed to the github
- Code is approved by another members (or at least 1)
- No critical bugs
- Task is moved to the "Done" section in the kanban board
- Acceptance criteria is completed
## Git workflow

## Secrets management



# Build and deployment
## Continuous Integration
Our CI pipeline consists of testing and static analysis tools for Python and React.js \
### Workflow files:
- https://github.com/inno-sport-inh/backend/blob/main/.github/workflows/tests.yaml
- https://github.com/inno-sport-inh/frontend/blob/main/.github/workflows/node.js.yml

### Github actions pages:
- https://github.com/inno-sport-inh/frontend/actions
- https://github.com/inno-sport-inh/backend/actions
  
### Static analysis tools:
#### Python
- flake8 (Code linter)
- vulture (A python tool that finds unused code such as dead functions, classes, variables and imports.)
#### React.js
- github Super-Linter (Code linter)
### Testing tools:
#### Python
- pytest
#### React.js
- Jest

# Architecture
## Static view

## Dynamic view

## Deployment view



# Usage



# Quality assurance
## Automated tests
We used **pytest** for python testing and **Jest** for React.js. \
Unit tests and integration tests was implemented. They can be found here: \
https://github.com/inno-sport-inh/backend/tree/main/adminpage/api-v2/tests
## User acceptance tests
## Quality attribute scenarios
https://github.com/inno-sport-inh/backend/blob/main/docs/quality-assurance/quality-attribute-scenarios.md


