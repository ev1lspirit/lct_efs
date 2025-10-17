"""
Тесты для проверки обработки ошибок в client_session_id
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from api.routes import (
    _get_or_create_session,
    _handle_existing_session,
    _create_new_session,
    _is_valid_session_id,
    WorkflowRequest,
)
from storage.redis.service import RedisCache


class TestSessionIdValidation:
    """Тесты валидации session_id"""

    def test_valid_uuid_session_id(self):
        """Валидный UUID должен приниматься"""
        assert _is_valid_session_id("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_without_hyphens(self):
        """UUID без дефисов должен приниматься"""
        assert _is_valid_session_id("550e8400e29b41d4a716446655440000") is True

    def test_valid_alphanumeric_session_id(self):
        """Буквенно-цифровая строка должна приниматься"""
        assert _is_valid_session_id("session_123-abc") is True

    def test_invalid_session_id_with_slashes(self):
        """Session_id со слэшами должен отклоняться (защита от path traversal)"""
        assert _is_valid_session_id("../../etc/passwd") is False

    def test_invalid_session_id_with_special_chars(self):
        """Session_id со спецсимволами должен отклоняться"""
        assert _is_valid_session_id("session@#$%") is False

    def test_invalid_empty_session_id(self):
        """Пустой session_id должен отклоняться"""
        assert _is_valid_session_id("") is False

    def test_invalid_none_session_id(self):
        """None как session_id должен отклоняться"""
        assert _is_valid_session_id(None) is False

    def test_invalid_too_long_session_id(self):
        """Слишком длинный session_id должен отклоняться (защита от DOS)"""
        assert _is_valid_session_id("a" * 129) is False

    def test_valid_max_length_session_id(self):
        """Session_id максимальной длины должен приниматься"""
        assert _is_valid_session_id("a" * 128) is True


class TestSessionRetrieval:
    """Тесты получения сессий"""

    @pytest.mark.asyncio
    async def test_get_or_create_rejects_invalid_session_id(self):
        """Должна вернуться ошибка 400 при невалидном session_id"""
        body = WorkflowRequest(
            client_session_id="../../malicious",
            client_workflow_id="test_workflow",
        )
        redis_cache = Mock(spec=RedisCache)

        with pytest.raises(HTTPException) as exc_info:
            await _get_or_create_session(body, redis_cache)

        assert exc_info.value.status_code == 400
        assert "Invalid session_id format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_handle_existing_session_detects_missing_workflow_id(self):
        """Должна вернуться ошибка 500 если в сессии нет workflow_id"""
        body = WorkflowRequest(
            client_session_id="valid-session-123",
            event_name="test_event",
        )
        redis_cache = Mock(spec=RedisCache)

        # Сессия существует, но без workflow_id
        session_context = {"some_data": "value"}

        with pytest.raises(HTTPException) as exc_info:
            _handle_existing_session(body, redis_cache, session_context)

        assert exc_info.value.status_code == 500
        assert "corrupted" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_handle_existing_session_warns_on_workflow_id_change(self):
        """Должно логироваться предупреждение при попытке сменить workflow_id"""
        body = WorkflowRequest(
            client_session_id="valid-session-123",
            client_workflow_id="new_workflow",
            event_name="test_event",
        )
        redis_cache = Mock(spec=RedisCache)

        session_context = {
            "__workflow_id": "original_workflow",
            "__created_at": "2025-10-16",
        }

        with patch("api.routes.logger") as mock_logger:
            result = _handle_existing_session(body, redis_cache, session_context)

            # Проверяем, что было предупреждение
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "change workflow_id" in warning_msg.lower()

            # Проверяем, что использован оригинальный workflow_id
            assert body.client_workflow_id == "original_workflow"
            assert result == session_context

    @pytest.mark.asyncio
    async def test_create_new_session_requires_workflow_id(self):
        """Создание новой сессии требует workflow_id"""
        body = WorkflowRequest(
            client_session_id="new-session-123",
            client_workflow_id=None,  # Отсутствует!
        )
        redis_cache = Mock(spec=RedisCache)

        with pytest.raises(HTTPException) as exc_info:
            _create_new_session(body, redis_cache)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_create_new_session_sets_ttl(self):
        """Создание новой сессии должно устанавливать TTL"""
        body = WorkflowRequest(
            client_session_id="new-session-123",
            client_workflow_id="test_workflow",
            context={"initial": "data"},
        )
        redis_cache = Mock(spec=RedisCache)

        result = _create_new_session(body, redis_cache)

        # Проверяем, что update_session вызван с TTL
        redis_cache.update_session.assert_called_once()
        call_args = redis_cache.update_session.call_args
        
        assert call_args[0][0] == "new-session-123"
        assert call_args[1]["ttl"] == 3600

        # Проверяем структуру созданной сессии
        assert "__workflow_id" in result
        assert result["__workflow_id"] == "test_workflow"
        assert "initial" in result

    @pytest.mark.asyncio
    async def test_handle_existing_session_updates_context(self):
        """Обновление контекста в существующей сессии должно вызывать update_session"""
        body = WorkflowRequest(
            client_session_id="existing-session",
            context={"new_field": "new_value"},
        )
        redis_cache = Mock(spec=RedisCache)

        session_context = {
            "__workflow_id": "test_workflow",
            "old_field": "old_value",
        }

        result = _handle_existing_session(body, redis_cache, session_context)

        # Проверяем, что контекст обновлен
        assert "new_field" in result
        assert result["new_field"] == "new_value"

        # Проверяем, что update_session был вызван
        redis_cache.update_session.assert_called_once()


# NOTE: Тесты для низкоуровневых методов RedisCache и SessionContext требуют
# интеграционного подхода с реальным Redis/fakeredis. Используем более высокоуровневые
# функциональные тесты через API routes, которые покрывают эту логику.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
