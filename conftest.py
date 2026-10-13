# configuration for pytest

# here you can add all modules
# with fixtures
pytest_plugins = [
    "api_v1.fixtures.user_creation",
    "api_v1.fixtures.model_creation",
]
