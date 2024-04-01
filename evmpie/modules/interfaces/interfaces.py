import asyncio

from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector
from abc import ABC, abstractmethod
from config import LAYERSWAP_API_KEY
from exceptions import SoftwareException
from evmpie.modules.tools import get_user_agent


class DEX(ABC):
    @abstractmethod
    async def swap(self):
        pass


class RequestClient(ABC):
    def __init__(self, client):
        self.client = client

    async def make_request(
        self,
        method: str = "GET",
        url: str = None,
        headers: dict = None,
        params: dict = None,
        data: str = None,
        json: dict = None,
    ):

        headers = (headers or {}) | {"User-Agent": get_user_agent()}
        async with self.client.session.request(
            method=method, url=url, headers=headers, data=data, params=params, json=json
        ) as response:
            try:
                data = await response.json()

                if response.status == 200:
                    return data
                raise SoftwareException(
                    f"Bad request to {self.__class__.__name__} API. "
                    f"Response status: {response.status}. Response: {await response.text()}"
                )
            except Exception as error:
                raise SoftwareException(
                    f"Bad request to {self.__class__.__name__} API. "
                    f"Response status: {response.status}. Response: {await response.text()} Error: {error}"
                )


class Bridge(ABC):
    def __init__(self, client):
        self.client = client

        if self.__class__.__name__ == "LayerSwap":
            self.headers = {
                "X-LS-APIKEY": f"{LAYERSWAP_API_KEY}",
                "Content-Type": "application/json",
            }
        elif self.__class__.__name__ == "Rhino":
            self.headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        elif self.__class__.__name__ == "Bungee":
            self.headers = {
                "Api-Key": "1b2fd225-062f-41aa-8c63-d1fef19945e7",
            }

    @abstractmethod
    async def bridge(self, *args, **kwargs):
        pass

    async def make_request(
        self,
        method: str = "GET",
        url: str = None,
        headers: dict = None,
        params: dict = None,
        data: str = None,
        json: dict = None,
    ):

        headers = (headers or {}) | {"User-Agent": get_user_agent()}
        async with self.client.session.request(
            method=method, url=url, headers=headers, data=data, json=json, params=params
        ) as response:
            data = await response.json()
            if response.status in [200, 201]:
                return data
            raise SoftwareException(
                f"Bad request to {self.__class__.__name__} API. "
                f"Response status: {response.status}. Status: {response.status}. Response: {await response.text()}"
            )


class Refuel(ABC):
    @abstractmethod
    async def refuel(self, *args, **kwargs):
        pass


class Messenger(ABC):
    @abstractmethod
    async def send_message(self):
        pass


class Landing(ABC):
    @abstractmethod
    async def deposit(self):
        pass

    @abstractmethod
    async def withdraw(self):
        pass


class Minter(ABC):
    @abstractmethod
    async def mint(self, *args, **kwargs):
        pass


class Creator(ABC):
    @abstractmethod
    async def create(self):
        pass


class Blockchain(ABC):
    def __init__(self, client):
        self.client = client

    async def make_request(
        self,
        method: str = "GET",
        url: str = None,
        headers: dict = None,
        params: dict = None,
        data: str = None,
        json: dict = None,
    ):

        headers = (headers or {}) | {"User-Agent": get_user_agent()}
        async with self.client.session.request(
            method=method, url=url, headers=headers, data=data, params=params, json=json
        ) as response:

            data = await response.json()
            if response.status == 200:
                return data
            raise SoftwareException(
                f"Bad request to {self.__class__.__name__} API. "
                f"Response status: {response.status}. Status: {response.status}. Response: {await response.text()}"
            )
