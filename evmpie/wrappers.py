from modules.blockchains.scroll.scroll import Scroll
from modules.blockchains.ethereum.ethereum import Ethereum
from modules.interfaces.account import Account
from modules.logger.logger import logger
from modules.tools import check_tx
from tabulate import tabulate
import asyncio
from typing import List
from config import SLEEP_FROM, SLEEP_TO


async def deposit_scroll(account: Account):
    """
    Deposit from official bridge
    ______________________________________________________
    all_amount - bridge from min_percent to max_percent
    """

    min_amount = 0.0036
    max_amount = 0.004
    decimal = 4

    all_amount = False

    min_percent = 100
    max_percent = 100

    eth = Ethereum(account)
    await eth.deposit_scroll(
        min_amount, max_amount, decimal, all_amount, min_percent, max_percent
    )


async def withdraw_scroll(account: Account):
    """
    Withdraw from official bridge
    ______________________________________________________
    all_amount - withdraw from min_percent to max_percent
    """

    min_amount = 0.0012
    max_amount = 0.0012
    decimal = 4

    all_amount = True

    min_percent = 10
    max_percent = 10

    scroll = Scroll(account)
    await scroll.withdraw(
        min_amount, max_amount, decimal, all_amount, min_percent, max_percent
    )


async def make_transfer(account: Account):
    """
    Transfer ETH
    """

    min_amount = 0.0001
    max_amount = 0.0002
    decimal = 5

    all_amount = True

    min_percent = 10
    max_percent = 10

    scroll = Scroll(account)
    await scroll.transfer(
        min_amount, max_amount, decimal, all_amount, min_percent, max_percent
    )


def get_tx_count(accounts: List[Account], network):
    asyncio.run(check_tx(accounts, network))


async def get_ethereum_balance(accounts: List[Account]):
    tasks = []
    for acc in accounts:
        account = Ethereum(acc)

        tasks.append(
            asyncio.create_task(account.get_eth_balance(), name=account.address)
        )

    await asyncio.gather(*tasks)

    table = [[k, i.get_name(), i.result()] for k, i in enumerate(tasks, start=1)]

    headers = ["#", "Address", "Balance (ETH)"]

    logger.info(f'\n{tabulate(table, headers, tablefmt="github")}')


async def get_scroll_balance(accounts: List[Account]):
    tasks = []
    for acc in accounts:
        account = Scroll(acc)

        tasks.append(
            asyncio.create_task(account.get_eth_balance(), name=account.address)
        )

    await asyncio.gather(*tasks)

    table = [[k, i.get_name(), i.result()] for k, i in enumerate(tasks, start=1)]

    headers = ["#", "Address", "Balance (ETH)"]

    logger.info(f'\n{tabulate(table, headers, tablefmt="github")}')


async def swap_syncswap(account: Account):
    """
    Make swap on SyncSwap

    from_token – Choose SOURCE token ETH, USDC | Select one
    to_token – Choose DESTINATION token ETH, USDC | Select one

    Disclaimer – Don't use stable coin in from and to token | from_token USDC to_token USDT DON'T WORK!!!
    ______________________________________________________
    all_amount - swap from min_percent to max_percent
    """

    from_token = "USDC"
    to_token = "ETH"

    min_amount = 1
    max_amount = 2
    decimal = 6
    slippage = 1

    all_amount = True

    min_percent = 100
    max_percent = 100

    scroll = Scroll(account)
    await scroll.swap(
        ["USDC"],
        SLEEP_FROM,
        SLEEP_TO,
        slippage,
        min_percent,
        max_percent,
    )
