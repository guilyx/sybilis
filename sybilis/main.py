from dotenv import load_dotenv
import os
import sys

load_dotenv("/home/wardn/github/sybilis/.env")

import questionary
from questionary import Choice
from concurrent.futures import ThreadPoolExecutor
from config import NETWORKS
from modules.tools import get_accounts
from wrappers import *
from modules.logger.logger import logger
from typing import Union
from modules.sleep import sleep
import time
import random

from config import SLEEP_FROM, SLEEP_TO, N_THREADS, THREAD_SLEEP_FROM, THREAD_SLEEP_TO

ACCOUNTS = get_accounts(os.getenv("ACCOUNTS"))

modules = [swap_syncswap, deposit_scroll, withdraw_scroll]


def get_module():
    result = questionary.select(
        "Select a method to get started",
        choices=[
            Choice("1) Deposit to Scroll", deposit_scroll),
            Choice("2) Withdraw from Scroll", withdraw_scroll),
            Choice("3) Swap on SyncSwap", swap_syncswap),
            # Choice("4) Make transfer", make_transfer),
            Choice("4) Check transaction count", "get_tx_count"),
            Choice("5) Check balance (ethereum)", "get_ethereum_balance"),
            Choice("6) Check balance (scroll)", "get_scroll_balance"),
            Choice("7) Exit", "exit"),
        ],
        qmark="⚙️ ",
        pointer="✅ ",
    ).ask()
    if result == "exit":
        sys.exit()
    return result


async def run_module(module, account):
    try:
        await module(account)
    except Exception as e:
        logger.error(e)

    await sleep(SLEEP_FROM, SLEEP_TO)


def _async_run_module(module, account):
    asyncio.run(run_module(module, account))


def _async_run_module(module, account):
    asyncio.run(run_module(module, account))


def main(module):
    with ThreadPoolExecutor(max_workers=N_THREADS) as executor:
        if module == "get_ethereum_balance":
            get_ethereum_balance(ACCOUNTS)

        else:
            for acc in ACCOUNTS:
                executor.submit(_async_run_module, module, acc)
                time.sleep(random.randint(THREAD_SLEEP_FROM, THREAD_SLEEP_TO))


if __name__ == "__main__":
    logger.info("Spinning Sybilis Bot...!")
    
    asyncio.run(get_ethereum_balance(ACCOUNTS))
    asyncio.run(get_scroll_balance(ACCOUNTS))
    main(get_module())

    get_tx_count(ACCOUNTS, NETWORKS["scroll"])
    logger.info("❤️ Subscribe to me – https://t.me/sybilis\n")
    logger.info("🤑 Donate me: 0x07ed706146545d01fa66a3c08ebca8c93a0089e5")
