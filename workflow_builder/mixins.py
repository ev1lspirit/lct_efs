import logging
import re
from typing import TYPE_CHECKING, Awaitable


if TYPE_CHECKING:
    from context import SessionContext
    from workflow_builder.expressions import IntegrationStateExpression


logger = logging.getLogger(__name__)

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
        """Заменяет {{variable}} на значения из context.session"""
        pattern = r"\{\{(\w+)\}\}"

        def interpolate_value(value):
            if isinstance(value, str):
                # Находим все переменные в строке
                matches = re.findall(pattern, value)
                result = value
                for var_name in matches:
                    if var_name not in context:
                        raise ValueError(
                            f"Variable '{var_name}' not found in context. "
                            f"Available variables: {list(context.keys())}"
                        )
                    context_value = context[var_name]
                    # Заменяем {{var}} на значение
                    result = result.replace(f"{{{{{var_name}}}}}", str(context_value))
                return result
            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [interpolate_value(item) for item in value]
            else:
                return value

        return {key: interpolate_value(value) for key, value in params.items()}

    def interpolate_url(self, session: dict):
        # Интерполируем URL - заменяем {{variable}} в самом URL
        interpolated_url = self.metadata.url
        url_variables_found = []
        for match in re.finditer(r"\{\{(\w+)\}\}", self.metadata.url):
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
