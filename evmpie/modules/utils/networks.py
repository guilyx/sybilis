import json
from typing import List

class Network:
    def __init__(
        self,
        name: str,
        rpc: list,
        chain_id: int,
        eip1559_support: bool,
        token: str,
        explorer: str,
        decimals: int = 18,
    ):
        self.name = name.lower()
        self.rpc = rpc
        self.chain_id = chain_id
        self.eip1559_support = eip1559_support
        self.token = token
        self.explorer = explorer
        self.decimals = decimals

    def __repr__(self):
        return f"{self.name}"


def load_networks(filepath: str) -> List[Network]:
    with open(filepath, "r") as f:
        networks_json = json.load(f)
    networks = {}
    for net in networks_json:
        net["name"] = net["name"].lower()
        network = Network(**net)
        networks[network.name] = network
    return networks


def is_network_supported(networks: List[Network], network: str):
    return network.lower() in networks
