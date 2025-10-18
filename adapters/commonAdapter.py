import asyncio
import logging
from attrs import define, field
from functools import wraps
from aiohttp import ClientTimeout, ClientError
from pydantic import BaseModel, ValidationError
from typing import Type, TypeVar, Any
import aiohttp

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class User(BaseModel):
    id: int
    role: str
    email: str
    password: str
    lastName: str
    firstName: str
    address: str
    rating: float


class APIError(BaseModel):
    error: bool
    status_code: int | None = None
    message: str | None = None
    content: Any | None = None

def async_retry(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        for attempt in range(1, self.retries + 1):
            try:
                return await method(self, *args, **kwargs)
            except (ClientError, asyncio.TimeoutError) as e:
                url = f"{self.base_url}/{args[1]}"
                logger.error(f"API request to {url} failed: {e}")
                if attempt == self.retries:
                    return APIError(error=True, message=str(e))
                await asyncio.sleep(self.backoff * attempt)
    return wrapper

@define
class CommonAdapter:
    base_url: str = field(converter=lambda x: x.rstrip("/"))
    headers: dict | None = field(default=None)
    timeout: int = field(default=10)
    retries: int = field(default=3)
    backoff: float = field(default=1.0)


    @property
    def default_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def __process_response(self, response: aiohttp.ClientResponse, response_model: Type[T] | None = None):
        try:
            data = await response.json()
        except ValueError:
            return await response.text()

        if isinstance(data, list):
            return data

        if isinstance(data, dict) and response_model:
            try:
                return response_model.model_validate(data)
            except ValidationError as e:
                return APIError(
                    error=True,
                    status_code=response.status,
                    message=f"Schema validation failed: {e}",
                    content=data,
                )
        return data

    @async_retry
    async def _request_handler(
        self,
        method: str,
        endpoint: str,
        response_model: Type[T] | None = None,
        **kwargs
    ) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with aiohttp.ClientSession() as session:
            session_method = getattr(session, method)
            async with session_method(
                url,
                json=kwargs,
                headers=self.headers or self.default_headers,
                timeout=ClientTimeout(self.timeout),
                ssl=False
            ) as response:
                return await self.__process_response(response, response_model)

    async def get(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return await self._request_handler("get", endpoint, response_model, **kwargs)

    async def post(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return await self._request_handler("post", endpoint, response_model, **kwargs)

    async def put(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return await self._request_handler("put", endpoint, response_model, **kwargs)

    async def delete(self, endpoint: str, response_model: Type[T] | None = None, **kwargs):
        return await self._request_handler("delete", endpoint, response_model, **kwargs)


async def main():
    ca = CommonAdapter("https://sandkittens.me")
    print(await ca.get("healthcheck", response_model=User))


if __name__ == "__main__":
    asyncio.run(main())
