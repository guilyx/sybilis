import csv
import asyncio
import sys
from termcolor import cprint
from aiohttp import ClientSession, TCPConnector, ClientResponseError
from typing import List, Dict


def get_accounts(filepath: str) -> List[Dict]:
    # Initialize an empty list to store the data
    accounts_data = []

    # Open the file and parse it using the csv module
    with open(filepath, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Each row in the reader is already a dictionary
            if "seed" in row:
                del row["seed"]
            accounts_data.append(row)

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
