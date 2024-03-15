from config import ACCOUNTS, NETWORKS, ETH_PRICE
from modules.utils.networks import is_network_supported
import os, sys

# print(ACCOUNTS)
print(is_network_supported(NETWORKS, "Blast"))
print(ETH_PRICE)
