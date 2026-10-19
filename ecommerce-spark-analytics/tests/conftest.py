import pytest

from src.spark_session import get_spark


@pytest.fixture(scope="session")
def spark():
    session = get_spark("tests", shuffle_partitions=1)
    yield session
    session.stop()
