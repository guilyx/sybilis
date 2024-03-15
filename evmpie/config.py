import asyncio

from modules.utils.tools import get_accounts, get_eth_price
from modules.utils.networks import load_networks

ACCOUNTS = get_accounts("/home/erwinl/github/web3/evmpie/env/accounts.csv")
NETWORKS = load_networks("/home/erwinl/github/web3/evmpie/config/networks.json")
ETH_PRICE = asyncio.run(get_eth_price())
