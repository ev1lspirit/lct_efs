import logging
import re
from typing import TYPE_CHECKING, Awaitable
from simpleeval import SimpleEval, AttributeDoesNotExist, NameNotDefined


if TYPE_CHECKING:
    from context import SessionContext
    from workflow_builder.expressions import IntegrationStateExpression


logger = logging.getLogger(__name__)


def safe_attr_access(obj, attr):
    """
    Безопасный доступ к атрибутам объекта для simpleeval.
    Поддерживает dict и объекты с атрибутами.
    """
    if isinstance(obj, dict):
        if attr in obj:
            return obj[attr]
        raise AttributeDoesNotExist(f"'{attr}' not found in dict")
    elif hasattr(obj, attr):
        return getattr(obj, attr)
    else:
        raise AttributeDoesNotExist(f"'{attr}' not found in object")


def evaluate_expression(expression: str, context: dict):
    """
    Безопасное вычисление выражения с поддержкой вложенных объектов.
    """
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
    
    # Включаем доступ к атрибутам через кастомный обработчик
    original_attr = s._eval_attribute if hasattr(s, '_eval_attribute') else None
    
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
        # Извлекаем имя переменной из сообщения об ошибке
        var_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
        available_vars = list(context.keys())
        raise NameError(
            f"Variable '{var_name}' not found in context for expression '{expression}'. "
            f"Available variables: {available_vars}"
        ) from e
    except AttributeDoesNotExist as e:
        raise ValueError(
            f"Attribute access failed in expression '{expression}': {e}"
        ) from e
    finally:
        # Восстанавливаем оригинальный обработчик
        if original_attr:
            s._eval_attribute = original_attr

class ParameterInterpolationMixin:
    metadata: "IntegrationStateExpression"
    context: "SessionContext"

    def _extract_variables(self, params: dict) -> list[str]:
        """Извлекает список переменных из params в формате {{variable}}"""
        pattern = r"\{\{(\w+)\}\}"
        variables = set()

        def extract_from_value(value):
            if isinstance(value, str):
                matches = re.findall(pattern, value)
                variables.update(matches)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)

        for value in params.values():
            extract_from_value(value)

        return list(variables)

    def _interpolate_params(self, params: dict, context) -> dict:
        """
        Заменяет {{variable}} и ${expression} на значения из context.
        Поддерживает:
        - {{variable}} - простая подстановка переменной
        - ${expression} - вычисление Python-выражения
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
                        raise ValueError(
                            f"Variable '{var_name}' not found in context. "
                            f"Available variables: {list(context.keys())}"
                        )
                    context_value = context[var_name]
                    result = result.replace(f"{{{{{var_name}}}}}", str(context_value))
                
                # Обрабатываем ${expression}
                for match in re.finditer(pattern_dollar_braces, result):
                    expression = match.group(1).strip()
                    try:
                        # Создаем копию контекста с автоматическим приведением строковых чисел
                        typed_context = {}
                        for key, value in context.items():
                            if isinstance(value, str):
                                try:
                                    # Пытаемся преобразовать в число
                                    typed_context[key] = int(value) if '.' not in value else float(value)
                                except (ValueError, TypeError):
                                    typed_context[key] = value
                            else:
                                typed_context[key] = value
                        
                        context_value = evaluate_expression(expression, typed_context)
                        result = result.replace(match.group(0), str(context_value))
                    except NameError as e:
                        # Специальная обработка для отсутствующих переменных
                        logger.error(
                            f"Variable not found in expression '${{{expression}}}': {e}. "
                            f"Available variables: {list(context.keys())}"
                        )
                        raise
                    except Exception as e:
                        logger.error(
                            f"Error evaluating expression '${{{expression}}}': {type(e).__name__}: {e}. "
                            f"Available variables: {list(context.keys())}"
                        )
                        raise ValueError(
                            f"Failed to evaluate expression '${{{expression}}}': {e}"
                        ) from e
                
                return result
            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [interpolate_value(item) for item in value]
            else:
                return value

        return {key: interpolate_value(value) for key, value in params.items()}

    def interpolate_url(self, url: str, session: dict):
        # Интерполируем URL - заменяем {{variable}} в самом URL
        interpolated_url = url
        url_variables_found = []
        for match in re.finditer(r"\{\{(\w+)\}\}", interpolated_url):
            var_name = match.group(1)
            url_variables_found.append(var_name)
            if var_name not in session:
                raise ValueError(
                    f"Variable '{var_name}' required in URL but not found in context. "
                    f"Available variables: {list(session.keys())}"
                )
            context_value = session[var_name]
            interpolated_url = interpolated_url.replace(
                f"{{{{{var_name}}}}}", str(context_value)
            )
        return interpolated_url

    def context_interpolation(self, url: str, session: dict):
        """
        Интерполирует выражения в формате ${...} используя контекст сессии.
        Поддерживает как простые переменные ${var}, так и Python-выражения ${var + 1}.
        """
        interpolated_url = url
        # Изменяем regex для захвата полного выражения внутри ${}
        # [^}]+ захватывает любые символы кроме }, что позволяет обрабатывать выражения
        for match in re.finditer(r"\$\{([^}]+)\}", interpolated_url):
            expression = match.group(1).strip()
            try:
                # Создаем копию контекста с автоматическим приведением строковых чисел
                typed_context = {}
                for key, value in session.items():
                    if isinstance(value, str):
                        try:
                            # Пытаемся преобразовать в число
                            typed_context[key] = int(value) if '.' not in value else float(value)
                        except (ValueError, TypeError):
                            typed_context[key] = value
                    else:
                        typed_context[key] = value
                
                # Используем simple_eval для безопасного вычисления выражения
                context_value = evaluate_expression(expression, typed_context)
                # Заменяем полное выражение ${...} на вычисленное значение
                interpolated_url = interpolated_url.replace(
                    match.group(0), str(context_value)
                )
            except NameError as e:
                # Специальная обработка для отсутствующих переменных
                logger.error(
                    f"Variable not found in expression '${{{expression}}}': {e}. "
                    f"Available variables: {list(session.keys())}"
                )
                raise
            except Exception as e:
                logger.error(
                    f"Error evaluating expression '${{{expression}}}': {type(e).__name__}: {e}. "
                    f"Available variables: {list(session.keys())}"
                )
                raise ValueError(
                    f"Failed to evaluate expression '${{{expression}}}': {e}"
                ) from e
        return interpolated_url

    def interpolate_params(self, interpolated_url, context: dict):
        method = self.metadata.method.lower()
        request_kwargs = {}

        if method in ['post', 'put', 'patch']:
            # POST/PUT/PATCH используют body (передается как json в requests)
            params_to_use = self.metadata.body or {}
            interpolated_params = self._interpolate_params(params_to_use, context)
            logger.info(f"Integration request: {self.metadata.method.upper()} {interpolated_url}")
            logger.debug(f"Original body: {self.metadata.body}")
            logger.debug(f"Interpolated body: {interpolated_params}")
            # Для POST/PUT/PATCH передаем данные как json, а не params
            request_kwargs['json'] = interpolated_params
        else:
            # GET/DELETE используют params (query string)
            params_to_use = self.metadata.params or {}
            interpolated_params = self._interpolate_params(params_to_use, context)
            logger.info(f"Integration request: {self.metadata.method.upper()} {interpolated_url}")
            logger.debug(f"Original params: {self.metadata.params}")
            logger.debug(f"Interpolated params: {interpolated_params}")
            request_kwargs['params'] = interpolated_params

        logger.debug(f"Request kwargs prepared: {list(request_kwargs.keys())}")
        return request_kwargs
