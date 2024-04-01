import csv
import asyncio
import sys
from termcolor import cprint
from aiohttp import ClientSession, TCPConnector
from typing import List, Dict
from modules.interfaces.account import Account
from modules.interfaces.networks import Network
import random
import asyncio
import random
from modules.logger.logger import logger
from config import CHECK_GWEI, MAX_GWEI, ETH_RPC, RETRY_COUNT
from modules.sleep import sleep
from web3 import Web3
from web3.eth import AsyncEth
import asyncio
import random
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import async_geth_poa_middleware
from eth_account import Account as EthereumAccount
from tabulate import tabulate

from config import NETWORKS


def get_accounts(filepath: str) -> List[Account]:
    # Initialize an empty list to store the data
    accounts_data = []

    # Open the file and parse it using the csv module
    with open(filepath, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Each row in the reader is already a dictionary
            if "seed" in row:
                del row["seed"]
            accounts_data.append(Account.from_dict(row))

    return accounts_data


def add_account(current_data: List[Dict], account: Dict):
    if "address" not in account or "private_key" not in account:
        raise Exception("Invalid Account Format!")

    print(f"Successfully added account {account['address']}.")
    current_data.append(account)


async def get_eth_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"

        params = {"ids": "ethereum", "vs_currencies": "usd"}

        async with ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
            async with session.get(url=url, params=params) as response:
                data = await response.json()
                if response.status == 200:
                    return data["ethereum"]["usd"]
    except Exception as error:
        cprint(
            f"\nError in <get_eth_price> function! Error: {error}\n", color="light_red"
        )
        sys.exit()


def get_user_agent():
    random_version = f"{random.uniform(520, 540):.2f}"
    return (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random_version} (KHTML, like Gecko)"
        f" Chrome/119.0.0.0 Safari/{random_version} Edg/119.0.0.0"
    )


async def get_gas():
    try:
        w3 = Web3(
            Web3.AsyncHTTPProvider(random.choice(ETH_RPC["rpc"])),
            modules={"eth": (AsyncEth,)},
        )
        gas_price = await w3.eth.gas_price
        gwei = w3.from_wei(gas_price, "gwei")
        return gwei
    except Exception as error:
        logger.error(error)


async def wait_gas():
    logger.info("Get GWEI")
    while True:
        gas = await get_gas()

        if gas > MAX_GWEI:
            logger.info(f"Current GWEI: {gas} > {MAX_GWEI}")
            await asyncio.sleep(60)
        else:
            logger.info(f"GWEI is normal | current: {gas} < {MAX_GWEI}")
            break


def check_gas(func):
    async def _wrapper(*args, **kwargs):
        if CHECK_GWEI:
            await wait_gas()
        return await func(*args, **kwargs)

    return _wrapper


def retry(func):
    async def wrapper(*args, **kwargs):
        retries = 0
        while retries <= RETRY_COUNT:
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error | {e}")
                await sleep(10, 20)
                retries += 1

    return wrapper

async def get_nonce(address: ChecksumAddress):
    web3 = AsyncWeb3(
        AsyncHTTPProvider(random.choice(NETWORKS["scroll"].rpc)),
        middlewares=[async_geth_poa_middleware],
    )

    nonce = await web3.eth.get_transaction_count(address)

    return nonce


async def check_tx(accounts: List[Account], network: Network):
    tasks = []

    logger.info("Start transaction checker")

    for acc in accounts:
        account = EthereumAccount.from_key(acc.private_key)

        tasks.append(asyncio.create_task(get_nonce(acc.address), name=acc.address))

    await asyncio.gather(*tasks)

    table = [[k, i.get_name(), i.result()] for k, i in enumerate(tasks, start=1)]

    headers = ["#", "Address", "Nonce"]

    logger.info(f'\n{tabulate(table, headers, tablefmt="github")}')

