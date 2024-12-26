from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.imweb.imweb_member_handler import ImwebMemberHandler


@pytest.mark.asyncio
async def test_get_mbti_result():
    """MBTI 결과 조회 테스트"""
    mock_member = {
        "email": "test@example.com",
        "home_page": "ENFJ",
        "member_code": "12345",
    }

    with patch(
        "app.imweb.old_imweb.imweb_service.get_member_by_email", new_callable=AsyncMock
    ) as mock_get_member:
        mock_get_member.return_value = mock_member

        handler = ImwebMemberHandler()
        result = await handler.get_mbti_result("test@example.com")

        assert result == "ENFJ"
        mock_get_member.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_get_mbti_result_no_member():
    """존재하지 않는 회원의 MBTI 결과 조회 테스트"""
    with patch(
        "app.imweb.old_imweb.imweb_service.get_member_by_email", new_callable=AsyncMock
    ) as mock_get_member:
        mock_get_member.return_value = None

        handler = ImwebMemberHandler()
        result = await handler.get_mbti_result("nonexistent@example.com")

        assert result is None


@pytest.mark.asyncio
async def test_save_mbti_result():
    """MBTI 결과 저장 테스트"""
    mock_member = {"email": "test@example.com", "member_code": "12345"}

    # Mock response with context manager
    class MockResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    # Mock session with proper async context manager
    class MockClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

        async def patch(self, *args, **kwargs):
            return MockResponse()

    with (
        patch(
            "app.imweb.old_imweb.imweb_service.get_member_by_email",
            new_callable=AsyncMock,
        ) as mock_get_member,
        patch(
            "app.imweb.old_imweb.imweb_service.get_access_token", new_callable=AsyncMock
        ) as mock_get_token,
        patch("aiohttp.ClientSession", return_value=MockClientSession()),
    ):
        mock_get_member.return_value = mock_member
        mock_get_token.return_value = "mock_token"

        handler = ImwebMemberHandler()
        result = await handler.save_mbti_result("test@example.com", "ENFJ")

        assert result is True
        mock_get_member.assert_called_once_with("test@example.com")
        mock_get_token.assert_called_once()


@pytest.mark.asyncio
async def test_save_mbti_result_no_member():
    """존재하지 않는 회원의 MBTI 결과 저장 테스트"""
    with patch(
        "app.imweb.old_imweb.imweb_service.get_member_by_email", new_callable=AsyncMock
    ) as mock_get_member:
        mock_get_member.return_value = None

        handler = ImwebMemberHandler()
        with pytest.raises(HTTPException) as exc_info:
            await handler.save_mbti_result("nonexistent@example.com", "ENFJ")

        assert exc_info.value.status_code == 404
        assert "회원을 찾을 수 없습니다" in str(exc_info.value.detail)
