from modules.interfaces.evm import EVMInterface
from modules.interfaces.networks import Network
from modules.interfaces.account import Account
from modules.tools import retry, check_gas
from modules.logger.logger import logger
from config import NETWORKS
from config import ScrollSettings
from web3 import Web3
from eth_abi import abi
import time


class SyncSwap(EVMInterface):
    def __init__(self, account: Account) -> None:
        super().__init__(account, NETWORKS["scroll"], ScrollSettings())
        self.swap_contract = self.get_contract(
            self.config.SYNCSWAP_CONTRACTS["router"], self.config.SYNCSWAP_ROUTER_ABI
        )

    async def get_pool(self, from_token: str, to_token: str):
        contract = self.get_contract(
            self.config.SYNCSWAP_CONTRACTS["classic_pool"],
            self.config.SYNCSWAP_CLASSIC_POOL_ABI,
        )

        pool_address = await contract.functions.getPool(
            Web3.to_checksum_address(self.config.TOKENS[from_token]),
            Web3.to_checksum_address(self.config.TOKENS[to_token]),
        ).call()

        return pool_address

    async def get_min_amount_out(
        self, pool_address: str, token_address: str, amount: int, slippage: float
    ):
        pool_contract = self.get_contract(
            pool_address, self.config.SYNCSWAP_CLASSIC_POOL_DATA_ABI
        )

        min_amount_out = await pool_contract.functions.getAmountOut(
            token_address, amount, self.address
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * slippage))

    @retry
    @check_gas
    async def swap(
        self,
        from_token: str,
        to_token: str,
        min_amount: float,
        max_amount: float,
        decimal: int,
        slippage: float,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ):
        token_address = Web3.to_checksum_address(self.config.TOKENS[from_token])

        amount_wei, amount, balance = await self.get_amount(
            from_token,
            min_amount,
            max_amount,
            decimal,
            all_amount,
            min_percent,
            max_percent,
        )

        logger.info(
            f"[{self.address}] Swap on SyncSwap – {from_token} -> {to_token} | {amount} {from_token}"
        )

        pool_address = await self.get_pool(from_token, to_token)

        if pool_address != self.config.ZERO_ADDRESS:
            tx_data = await self.get_tx_data()

            if from_token == "ETH":
                tx_data.update({"value": amount_wei})
            else:
                await self.approve(
                    amount_wei,
                    token_address,
                    Web3.to_checksum_address(self.config.SYNCSWAP_CONTRACTS["router"]),
                )

            min_amount_out = await self.get_min_amount_out(
                pool_address, token_address, amount_wei, slippage
            )

            steps = [
                {
                    "pool": pool_address,
                    "data": abi.encode(
                        ["address", "address", "uint8"],
                        [token_address, self.address, 1],
                    ),
                    "callback": self.config.ZERO_ADDRESS,
                    "callbackData": "0x",
                }
            ]

            paths = [
                {
                    "steps": steps,
                    "tokenIn": (
                        self.config.ZERO_ADDRESS
                        if from_token == "ETH"
                        else token_address
                    ),
                    "amountIn": amount_wei,
                }
            ]

            deadline = int(time.time()) + 1000000

            contract_txn = await self.swap_contract.functions.swap(
                paths, min_amount_out, deadline
            ).build_transaction(tx_data)

            signed_txn = await self.sign(contract_txn)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())
        else:
            logger.error(
                f"[{self.address}] Swap path {from_token} to {to_token} not found!"
            )
