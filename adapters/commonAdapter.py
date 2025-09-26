import requests
from requests.exceptions import RequestException, Timeout
from pydantic import BaseModel, ValidationError
from typing import Type, TypeVar, Any
import time

T = TypeVar("T", bound=BaseModel)


class APIError(BaseModel):
    error: bool
    status_code: int | None = None
    message: str | None = None
    content: Any | None = None


class CommonAdapter:
    def __init__(self, base_url: str, default_headers: dict | None = None,
                 timeout: int = 10, retries: int = 3, backoff: float = 1.0):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(default_headers or {})
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def _request_handler(
        self,
        method: str,
        endpoint: str,
        response_model: Type[T] | None = None,
        **kwargs
    ) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
                resp.raise_for_status()

                try:
                    data = resp.json()
                except ValueError:
                    return resp.text

                # если массив → возвращаем список как есть
                if isinstance(data, list):
                    return data

                # если объект и указана модель → мапим
                if isinstance(data, dict) and response_model:
                    try:
                        return response_model.model_validate(data)
                    except ValidationError as e:
                        return APIError(
                            error=True,
                            status_code=resp.status_code,
                            message=f"Schema validation failed: {e}",
                            content=data,
                        )

                # если объект без модели → возвращаем dict
                return data

            except (RequestException, Timeout) as e:
                if attempt == self.retries:
                    return APIError(error=True, message=str(e))
                time.sleep(self.backoff * attempt)

            except requests.HTTPError as e:
                return APIError(
                    error=True,
                    status_code=resp.status_code if 'resp' in locals() else None,
                    message=str(e),
                    content=resp.text if 'resp' in locals() else None,
                )

    # Методы-обертки
    def get(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return self._request_handler("get", endpoint, response_model, **kwargs)

    def post(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return self._request_handler("post", endpoint, response_model, **kwargs)

    def put(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return self._request_handler("put", endpoint, response_model, **kwargs)

    def delete(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return self._request_handler("delete", endpoint, response_model, **kwargs)
