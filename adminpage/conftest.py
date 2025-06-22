# configuration for pytest

# here you can add all modules
# with fixtures
pytest_plugins = [
    "api.fixtures.user_creation",
    "api.fixtures.model_creation",
]
