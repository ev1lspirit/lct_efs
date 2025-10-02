"""
Unit тесты для интерполяции переменных в Integration States
"""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from workflow_builder.handlers import IntegrationHandler
from workflow_builder.expressions import IntegrationStateExpression
from context import SessionContext
from adapters.commonAdapter import CommonAdapter


class TestIntegrationInterpolation:
    """Тесты интерполяции переменных"""
    
    def test_interpolate_params_simple(self):
        """Тест простой интерполяции переменных"""
        # Mock context
        context = Mock(spec=SessionContext)
        context.session = {"user_id": "12345", "city": "Moscow"}
        
        # Создаем expression
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/data",
            params={"user": "{{user_id}}", "location": "{{city}}"},
            method="get",
            dependent_variables=["user_id", "city"]
        )
        
        # Создаем handler
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        # Тестируем интерполяцию
        interpolated = handler._interpolate_params(expr.params)
        
        assert interpolated == {"user": "12345", "location": "Moscow"}
    
    def test_interpolate_params_nested(self):
        """Тест интерполяции вложенных структур"""
        context = Mock(spec=SessionContext)
        context.session = {"email": "test@example.com", "name": "John", "age": "30"}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={
                "user": {
                    "email": "{{email}}",
                    "name": "{{name}}"
                },
                "metadata": {
                    "age": "{{age}}"
                }
            },
            method="post",
            dependent_variables=["email", "name", "age"]
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        interpolated = handler._interpolate_params(expr.params)
        
        assert interpolated["user"]["email"] == "test@example.com"
        assert interpolated["user"]["name"] == "John"
        assert interpolated["metadata"]["age"] == "30"
    
    def test_interpolate_params_arrays(self):
        """Тест интерполяции массивов"""
        context = Mock(spec=SessionContext)
        context.session = {"name": "John", "email": "john@example.com", "id": "123"}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={
                "tags": ["user_{{name}}", "email_{{email}}", "id_{{id}}"],
                "filters": [{"key": "name", "value": "{{name}}"}]
            },
            method="post",
            dependent_variables=["name", "email", "id"]
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        interpolated = handler._interpolate_params(expr.params)
        
        assert interpolated["tags"] == ["user_John", "email_john@example.com", "id_123"]
        assert interpolated["filters"][0]["value"] == "John"
    
    def test_interpolate_params_multiple_vars_in_string(self):
        """Тест множественных переменных в одной строке"""
        context = Mock(spec=SessionContext)
        context.session = {"first_name": "John", "last_name": "Doe"}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={
                "full_name": "{{first_name}} {{last_name}}",
                "display": "User: {{first_name}} {{last_name}}"
            },
            method="get",
            dependent_variables=["first_name", "last_name"]
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        interpolated = handler._interpolate_params(expr.params)
        
        assert interpolated["full_name"] == "John Doe"
        assert interpolated["display"] == "User: John Doe"
    
    def test_interpolate_params_missing_variable(self):
        """Тест ошибки при отсутствии переменной"""
        context = Mock(spec=SessionContext)
        context.session = {"user_id": "12345"}  # email отсутствует
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={"user": "{{user_id}}", "email": "{{email}}"},
            method="get",
            dependent_variables=["user_id", "email"]
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        # Должна быть ошибка с понятным сообщением
        with pytest.raises(ValueError) as exc_info:
            handler._interpolate_params(expr.params)
        
        assert "Variable 'email' not found in context" in str(exc_info.value)
        assert "Available variables: ['user_id']" in str(exc_info.value)
    
    def test_interpolate_params_no_variables(self):
        """Тест params без переменных (должен работать как раньше)"""
        context = Mock(spec=SessionContext)
        context.session = {"user_id": "12345"}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={"status": "active", "limit": 10},
            method="get",
            dependent_variables=[]
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        interpolated = handler._interpolate_params(expr.params)
        
        assert interpolated == {"status": "active", "limit": 10}
    
    def test_interpolate_params_mixed_types(self):
        """Тест смешанных типов (строки, числа, bool)"""
        context = Mock(spec=SessionContext)
        context.session = {"user_id": "12345", "active": "true", "count": "42"}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={
                "id": "{{user_id}}",
                "active": "{{active}}",
                "count": "{{count}}",
                "static_number": 100,
                "static_bool": True
            },
            method="get",
            dependent_variables=["user_id", "active", "count"]
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        interpolated = handler._interpolate_params(expr.params)
        
        assert interpolated["id"] == "12345"
        assert interpolated["active"] == "true"
        assert interpolated["count"] == "42"
        assert interpolated["static_number"] == 100
        assert interpolated["static_bool"] is True


class TestExtractVariables:
    """Тесты автоматического извлечения переменных"""
    
    def test_extract_variables_simple(self):
        """Тест извлечения простых переменных"""
        context = Mock(spec=SessionContext)
        context.session = {}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={"id": "{{user_id}}", "email": "{{email}}"},
            method="get"
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        variables = handler._extract_variables(expr.params)
        
        assert set(variables) == {"user_id", "email"}
    
    def test_extract_variables_nested(self):
        """Тест извлечения переменных из вложенных структур"""
        context = Mock(spec=SessionContext)
        context.session = {}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={
                "user": {
                    "id": "{{user_id}}",
                    "profile": {
                        "email": "{{email}}",
                        "city": "{{city}}"
                    }
                }
            },
            method="post"
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        variables = handler._extract_variables(expr.params)
        
        assert set(variables) == {"user_id", "email", "city"}
    
    def test_extract_variables_arrays(self):
        """Тест извлечения переменных из массивов"""
        context = Mock(spec=SessionContext)
        context.session = {}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={
                "filters": [
                    {"key": "name", "value": "{{name}}"},
                    {"key": "age", "value": "{{age}}"}
                ],
                "tags": ["{{tag1}}", "{{tag2}}"]
            },
            method="post"
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        variables = handler._extract_variables(expr.params)
        
        assert set(variables) == {"name", "age", "tag1", "tag2"}
    
    def test_extract_variables_duplicates(self):
        """Тест удаления дубликатов"""
        context = Mock(spec=SessionContext)
        context.session = {}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={
                "id": "{{user_id}}",
                "user_id": "{{user_id}}",
                "filters": {"user": "{{user_id}}"}
            },
            method="get"
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        variables = handler._extract_variables(expr.params)
        
        # Должно быть только одно значение, без дубликатов
        assert variables.count("user_id") == 1
    
    def test_extract_variables_empty(self):
        """Тест params без переменных"""
        context = Mock(spec=SessionContext)
        context.session = {}
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users",
            params={"status": "active", "limit": 10},
            method="get"
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        variables = handler._extract_variables(expr.params)
        
        assert variables == []


class TestDependentVariablesValidation:
    """Тесты валидации dependent_variables через @check_context_consistency"""
    
    @patch.object(CommonAdapter, '__init__', return_value=None)
    @patch.object(CommonAdapter, 'get')
    def test_dependent_variables_present(self, mock_get, mock_init):
        """Тест успешной валидации dependent_variables"""
        mock_get.return_value = {"success": True}
        
        context = Mock(spec=SessionContext)
        context.session = {"user_id": "12345", "email": "test@example.com"}
        context.__enter__ = Mock(return_value=context.session)
        context.__exit__ = Mock(return_value=False)
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users/{{user_id}}",
            params={"email": "{{email}}"},
            method="get",
            dependent_variables=["user_id", "email"]
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        # Не должно быть исключений
        result = handler.result()
        assert result == {"success": True}
    
    def test_dependent_variables_missing(self):
        """Тест ошибки при отсутствии dependent_variables"""
        context = Mock(spec=SessionContext)
        context.session = {"user_id": "12345"}  # email отсутствует
        
        expr = IntegrationStateExpression(
            variable="result",
            url="http://api.test.com/users/{{user_id}}",
            params={"email": "{{email}}"},
            method="get",
            dependent_variables=["user_id", "email"]  # email required но отсутствует
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        # Должна быть ошибка от декоратора @check_context_consistency
        with pytest.raises(ValueError) as exc_info:
            handler.result()
        
        assert "Missing dependent variables in context" in str(exc_info.value)
        assert "email" in str(exc_info.value)


class TestErrorHandling:
    """Тесты обработки ошибок API"""
    
    @patch.object(CommonAdapter, '__init__', return_value=None)
    @patch.object(CommonAdapter, 'get')
    def test_error_variable_saved(self, mock_get, mock_init):
        """Тест сохранения ошибки в error_variable"""
        # Мокируем ответ с ошибкой
        error_response = Mock()
        error_response.error = True
        error_response.message = "API Error: User not found"
        error_response.status_code = 404
        error_response.content = {"detail": "User ID 12345 not found"}
        mock_get.return_value = error_response
        
        context = Mock(spec=SessionContext)
        context.session = {"user_id": "12345"}
        context.__enter__ = Mock(return_value=context.session)
        context.__exit__ = Mock(return_value=False)
        
        expr = IntegrationStateExpression(
            variable="user_data",
            url="http://api.test.com/users/{{user_id}}",
            params={},
            method="get",
            dependent_variables=["user_id"],
            error_variable="api_error"
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        result = handler.result()
        
        # Проверяем, что ошибка сохранена в контекст
        assert result == error_response
        context.__enter__.assert_called_once()
        
        # Проверяем структуру сохраненной ошибки
        saved_error = context.session["api_error"]
        assert saved_error["error"] is True
        assert saved_error["message"] == "API Error: User not found"
        assert saved_error["status_code"] == 404
        assert saved_error["content"] == {"detail": "User ID 12345 not found"}
    
    @patch.object(CommonAdapter, '__init__', return_value=None)
    @patch.object(CommonAdapter, 'post')
    def test_error_without_error_variable(self, mock_post, mock_init):
        """Тест ошибки без error_variable (просто возвращаем response)"""
        error_response = Mock()
        error_response.error = True
        error_response.message = "Payment failed"
        mock_post.return_value = error_response
        
        context = Mock(spec=SessionContext)
        context.session = {"amount": "100"}
        context.__enter__ = Mock(return_value=context.session)
        context.__exit__ = Mock(return_value=False)
        
        expr = IntegrationStateExpression(
            variable="payment_result",
            url="http://api.payment.com/charge",
            params={"amount": "{{amount}}"},
            method="post",
            dependent_variables=["amount"]
            # error_variable отсутствует
        )
        
        handler = IntegrationHandler(
            adapter=CommonAdapter,
            metadata=expr,
            context=context
        )
        
        result = handler.result()
        
        # Должен вернуть error_response как есть
        assert result == error_response
        # Контекст НЕ должен обновляться для error_variable
        assert "api_error" not in context.session


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
