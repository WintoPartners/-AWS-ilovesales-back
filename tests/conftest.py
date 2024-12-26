import pytest

from app.common.config import Settings


@pytest.fixture
def app_config():
    return Settings(
        IMWEB_API_KEY="c1659c6b9160db5915f4081f69e99540547557c250",
        IMWEB_SECRET_KEY="5081fe22a032054bf9be7e",
    )


@pytest.fixture
def mock_imweb_api():
    # 아임웹 API 모킹
    pass
