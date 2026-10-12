import pytest
from django.db import connection


@pytest.mark.django_db
def test_database_connection_pool_is_enabled():
    pool = connection.pool

    assert pool is not None
    assert pool.min_size == 1
    assert pool.max_size == 5

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
