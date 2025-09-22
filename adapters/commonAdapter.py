import requests
from requests.exceptions import RequestException, Timeout


class CommonAdapter:
    def __init__(self, base_url: str, default_headers: dict | None = None, timeout: int = 10):
        """
        :param base_url: базовый
        :param default_headers: заголовки по умолчанию (например, {"Authorization": "Bearer ..."})
        :param timeout: таймаут в секундах для всех запросов
        """
        self.base_url = base_url.rstrip("/")  # убираем лишний слэш
        self.session = requests.Session()  # используем Session для повторного соединения
        self.session.headers.update(default_headers or {})
        self.timeout = timeout

    def _handle_response(self, response: requests.Response):
        """Обработка ответа сервера с проверкой ошибок"""
        try:
            response.raise_for_status()  # выбросит исключение при 4xx/5xx
        except requests.HTTPError as e:
            return {
                "error": True,
                "status_code": response.status_code,
                "message": str(e),
                "content": response.text,
            }

        # пробуем распарсить JSON, иначе возвращаем текст
        try:
            return response.json()
        except ValueError:
            return response.text

    def get(self, endpoint: str, params: dict | None = None, headers: dict | None = None):
        """GET-запрос"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            return self._handle_response(resp)
        except (RequestException, Timeout) as e:
            return {"error": True, "message": str(e)}

    def post(self, endpoint: str, data: dict | None = None, json: dict | None = None,
             headers: dict | None = None):
        """POST-запрос"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            resp = self.session.post(url, data=data, json=json, headers=headers, timeout=self.timeout)
            return self._handle_response(resp)
        except (RequestException, Timeout) as e:
            return {"error": True, "message": str(e)}

    def put(self, endpoint: str, json: dict | None = None, headers: dict | None = None):
        """PUT-запрос"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            resp = self.session.put(url, json=json, headers=headers, timeout=self.timeout)
            return self._handle_response(resp)
        except (RequestException, Timeout) as e:
            return {"error": True, "message": str(e)}

    def delete(self, endpoint: str, headers: dict | None = None):
        """DELETE-запрос"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            resp = self.session.delete(url, headers=headers, timeout=self.timeout)
            return self._handle_response(resp)
        except (RequestException, Timeout) as e:
            return {"error": True, "message": str(e)}
