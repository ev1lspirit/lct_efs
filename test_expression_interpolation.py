"""
Тест для проверки интерполяции выражений в формате ${expression}
"""
import re
from simpleeval import SimpleEval, AttributeDoesNotExist, NameNotDefined


def safe_attr_access(obj, attr):
    """Безопасный доступ к атрибутам для simpleeval"""
    if isinstance(obj, dict):
        if attr in obj:
            return obj[attr]
        raise AttributeDoesNotExist(f"'{attr}' not found in dict")
    elif hasattr(obj, attr):
        return getattr(obj, attr)
    else:
        raise AttributeDoesNotExist(f"'{attr}' not found in object")


def evaluate_expression(expression: str, context: dict):
    """Безопасное вычисление выражения с поддержкой вложенных объектов."""
    s = SimpleEval()
    s.names = context
    s.functions = {
        "len": len, 
        "sum": sum, 
        "max": max, 
        "min": min, 
        "str": str, 
        "int": int, 
        "float": float
    }
    
    def custom_attr(node):
        """Кастомный обработчик атрибутов с поддержкой dict"""
        obj = s._eval(node.value)
        attr = node.attr
        return safe_attr_access(obj, attr)
    
    s._eval_attribute = custom_attr
    
    # Добавляем поддержку унарного оператора NOT (!)
    # Заменяем ! на not (с учетом того, что ! может быть внутри выражения)
    normalized_expression = expression.strip()
    # Заменяем !( на not ( и !variable на not variable
    normalized_expression = re.sub(r'!(\w+|[\(])', r'not \1', normalized_expression)
    
    try:
        return s.eval(normalized_expression)
    except (NameError, NameNotDefined) as e:
        # Более информативная ошибка при отсутствии переменной
        var_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
        available_vars = list(context.keys())
        raise NameError(
            f"Variable '{var_name}' not found in context for expression '{expression}'. "
            f"Available variables: {available_vars}"
        ) from e


def interpolate_params(params: dict, context: dict) -> dict:
    """
    Заменяет {{variable}} и ${expression} на значения из context.
    """
    pattern_double_braces = r"\{\{(\w+)\}\}"
    pattern_dollar_braces = r"\$\{([^}]+)\}"

    def interpolate_value(value):
            if isinstance(value, str):
                result = value
                
                # Обрабатываем {{variable}}
                matches = re.findall(pattern_double_braces, result)
                for var_name in matches:
                    if var_name not in context:
                        raise ValueError(f"Variable '{var_name}' not found in context")
                    context_value = context[var_name]
                    result = result.replace(f"{{{{{var_name}}}}}", str(context_value))
                
                # Обрабатываем ${expression}
                for match in re.finditer(pattern_dollar_braces, result):
                    expression = match.group(1).strip()
                    try:
                        # Создаем копию контекста с приведением типов для числовых значений
                        typed_context = {}
                        for key, value in context.items():
                            # Пытаемся преобразовать строковые числа в int/float
                            if isinstance(value, str):
                                try:
                                    # Сначала пробуем int
                                    if '.' not in value:
                                        typed_context[key] = int(value)
                                    else:
                                        typed_context[key] = float(value)
                                except (ValueError, TypeError):
                                    # Если не число, оставляем как строку
                                    typed_context[key] = value
                            else:
                                typed_context[key] = value
                        
                        context_value = evaluate_expression(expression, typed_context)
                        result = result.replace(match.group(0), str(context_value))
                    except NameError as e:
                        # Пробрасываем NameError наверх с информативным сообщением
                        raise
                    except Exception as e:
                        raise ValueError(f"Failed to evaluate expression '${{{expression}}}': {e}") from e
                
                return result
            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [interpolate_value(item) for item in value]
            else:
                return value

    return {key: interpolate_value(value) for key, value in params.items()}


# Тесты
def test_simple_variable():
    """Тест простой переменной ${variable}"""
    context = {"quantity_change": 5}
    params = {"quantity": "${quantity_change}"}
    result = interpolate_params(params, context)
    assert result == {"quantity": "5"}, f"Expected {{'quantity': '5'}}, got {result}"
    print("✓ Тест простой переменной прошел")


def test_expression_with_addition():
    """Тест выражения с арифметикой ${variable + 1}"""
    context = {"quantity_change": 5}
    params = {"quantity": "${quantity_change + 1}"}
    result = interpolate_params(params, context)
    assert result == {"quantity": "6"}, f"Expected {{'quantity': '6'}}, got {result}"
    print("✓ Тест выражения с сложением прошел")


def test_expression_with_string_number():
    """Тест выражения с арифметикой когда переменная - строка ${variable + 1}"""
    context = {"quantity_change": "5"}  # Строка, а не число!
    params = {"quantity": "${quantity_change + 1}"}
    result = interpolate_params(params, context)
    assert result == {"quantity": "6"}, f"Expected {{'quantity': '6'}}, got {result}"
    print("✓ Тест выражения с строковым числом прошел")


def test_complex_expression():
    """Тест сложного выражения"""
    context = {"price": 100, "discount": 10}
    params = {"total": "${price - discount}", "message": "${'Price: ' + str(price) + ' руб'}"}
    result = interpolate_params(params, context)
    assert result == {"total": "90", "message": "Price: 100 руб"}, f"Unexpected result: {result}"
    print("✓ Тест сложного выражения прошел")


def test_double_braces():
    """Тест формата {{variable}}"""
    context = {"user_id": 123}
    params = {"id": "{{user_id}}"}
    result = interpolate_params(params, context)
    assert result == {"id": "123"}, f"Expected {{'id': '123'}}, got {result}"
    print("✓ Тест двойных скобок прошел")


def test_mixed_formats():
    """Тест смешанных форматов"""
    context = {"count": 5, "name": "товар"}
    params = {
        "title": "${'У вас ' + str(count) + ' ' + name}",
        "id": "{{name}}"
    }
    result = interpolate_params(params, context)
    assert result == {"title": "У вас 5 товар", "id": "товар"}, f"Unexpected result: {result}"
    print("✓ Тест смешанных форматов прошел")


def test_nested_structures():
    """Тест вложенных структур"""
    context = {"quantity_change": 3}
    params = {
        "nested": {
            "quantity": "${quantity_change + 1}",
            "list": ["${quantity_change}", "${quantity_change * 2}"]
        }
    }
    result = interpolate_params(params, context)
    expected = {
        "nested": {
            "quantity": "4",
            "list": ["3", "6"]
        }
    }
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Тест вложенных структур прошел")


def test_nested_object_access():
    """Тест доступа к вложенным объектам через точку"""
    context = {
        "store": {"rating": 4.5, "name": "Shop"},
        "cart_snapshot": {
            "user": {"email": "user@example.com"},
            "summary": {"total": 1500, "total_items": 3}
        }
    }
    params = {
        "rating_text": "${'⭐ ' + str(store.rating)}",
        "email_message": "${'Мы отправили подтверждение на ' + cart_snapshot.user.email}",
        "total": "${cart_snapshot.summary.total}",
        "items": "${str(cart_snapshot.summary.total_items) + ' товара'}"
    }
    result = interpolate_params(params, context)
    expected = {
        "rating_text": "⭐ 4.5",
        "email_message": "Мы отправили подтверждение на user@example.com",
        "total": "1500",
        "items": "3 товара"
    }
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Тест доступа к вложенным объектам прошел")


def test_not_operator():
    """Тест оператора отрицания (!)"""
    context = {"product_liked": False, "is_active": True, "count": 0}
    params = {
        "not_liked": "${!product_liked}",
        "not_active": "${!is_active}",
        "has_count": "${!count}"
    }
    result = interpolate_params(params, context)
    expected = {
        "not_liked": "True",
        "not_active": "False",
        "has_count": "True"
    }
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Тест оператора отрицания прошел")


def test_not_operator_with_expressions():
    """Тест оператора отрицания в сложных выражениях"""
    context = {"product_liked": False, "in_cart": True}
    params = {
        "show_like": "${!product_liked}",
        "show_remove": "${!(!in_cart)}",  # двойное отрицание
        "message": "${'Нравится' if !product_liked else 'Не нравится'}"
    }
    result = interpolate_params(params, context)
    expected = {
        "show_like": "True",
        "show_remove": "True",
        "message": "Нравится"
    }
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Тест оператора отрицания в выражениях прошел")


def test_missing_variable_error():
    """Тест обработки отсутствующей переменной"""
    context = {"user_id": 123}
    params = {"liked": "${!product_liked}"}  # product_liked отсутствует
    
    try:
        result = interpolate_params(params, context)
        assert False, "Expected NameError to be raised"
    except NameError as e:
        error_msg = str(e)
        assert "product_liked" in error_msg, f"Expected 'product_liked' in error: {error_msg}"
        assert "Available variables" in error_msg, f"Expected 'Available variables' in error: {error_msg}"
        assert "user_id" in error_msg, f"Expected 'user_id' in available variables: {error_msg}"
        print("✓ Тест обработки отсутствующей переменной прошел")


if __name__ == "__main__":
    print("Запуск тестов интерполяции выражений...\n")
    
    test_simple_variable()
    test_expression_with_addition()
    test_expression_with_string_number()
    test_complex_expression()
    test_double_braces()
    test_mixed_formats()
    test_nested_structures()
    test_nested_object_access()
    test_not_operator()
    test_not_operator_with_expressions()
    test_missing_variable_error()
    
    print("\n✅ Все тесты прошли успешно!")
    print("\nПоддерживаемые возможности:")
    print("  • ${variable} - простые переменные")
    print("  • ${variable + 1} - арифметические выражения")
    print("  • ${!variable} - логическое отрицание (NOT)")
    print("  • ${object.property} - вложенные объекты")
    print("  • ${object.nested.deep} - глубокая вложенность")
    print("  • Автоматическое приведение строковых чисел")
    print("  • Информативные сообщения об ошибках")
