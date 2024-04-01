from modules.interfaces.evm import EVMInterface
from modules.interfaces.networks import Network
from modules.interfaces.account import Account
from modules.tools import retry, check_gas
from modules.logger.logger import logger
from modules.sleep import sleep
from modules.blockchains.scroll.syncswap import SyncSwap

from config import NETWORKS
from config import ScrollSettings

import random
from typing import List, Union


class Scroll(EVMInterface):
    def __init__(self, account: Account):
        super().__init__(account, NETWORKS["scroll"], ScrollSettings())
        self.swap_modules = {
            "syncswap": SyncSwap(account),
        }

    def get_swap_module(self):
        swap_module = random.choice(self.swap_modules)
        return self.swap_modules[swap_module]

    @retry
    @check_gas
    async def withdraw(
        self,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ):
        amount_wei, amount, balance = await self.get_amount(
            "ETH", min_amount, max_amount, decimal, all_amount, min_percent, max_percent
        )

        logger.info(f"[{self.address}] Bridge from Scroll | {amount} ETH")

        contract = self.get_contract(
            self.config.BRIDGE_CONTRACTS["withdraw"], self.config.WITHDRAW_ABI
        )

        tx_data = await self.get_tx_data(amount_wei)

        transaction = await contract.functions.withdrawETH(
            amount_wei, 0
        ).build_transaction(tx_data)

        signed_txn = await self.sign(transaction)

        txn_hash = await self.send_raw_transaction(signed_txn)

        await self.wait_until_tx_finished(txn_hash.hex())

    @retry
    @check_gas
    async def wrap_eth(
        self,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ):
        amount_wei, amount, balance = await self.get_amount(
            "ETH", min_amount, max_amount, decimal, all_amount, min_percent, max_percent
        )

        weth_contract = self.get_contract(
            self.config.TOKENS["WETH"], self.config.WETH_ABI
        )

        logger.info(f"[{self.address}] Wrap {amount} ETH")

        tx_data = await self.get_tx_data(amount_wei)

        transaction = await weth_contract.functions.deposit().build_transaction(tx_data)

        signed_txn = await self.sign(transaction)

        txn_hash = await self.send_raw_transaction(signed_txn)

        await self.wait_until_tx_finished(txn_hash.hex())

    @retry
    @check_gas
    async def unwrap_eth(
        self,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ):
        amount_wei, amount, balance = await self.get_amount(
            "WETH",
            min_amount,
            max_amount,
            decimal,
            all_amount,
            min_percent,
            max_percent,
        )

        weth_contract = self.get_contract(
            self.config.TOKENS["WETH"], self.config.WETH_ABI
        )

        logger.info(f"[{self.address}] Unwrap {amount} ETH")

        tx_data = await self.get_tx_data()

        transaction = await weth_contract.functions.withdraw(
            amount_wei
        ).build_transaction(tx_data)

        signed_txn = await self.sign(transaction)

        txn_hash = await self.send_raw_transaction(signed_txn)

        await self.wait_until_tx_finished(txn_hash.hex())

    @retry
    @check_gas
    async def transfer(
        self,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ) -> None:
        amount_wei, amount, balance = await self.get_amount(
            "ETH", min_amount, max_amount, decimal, all_amount, min_percent, max_percent
        )

        logger.info(
            f"[{self.address}] Make transfer to {self.recipient} | {amount} ETH"
        )

        tx_data = await self.get_tx_data(amount_wei)
        tx_data.update({"to": self.web3.to_checksum_address(self.recipient)})

        signed_txn = await self.sign(tx_data)

        txn_hash = await self.send_raw_transaction(signed_txn)

        await self.wait_until_tx_finished(txn_hash.hex())

    async def swap(
        self,
        tokens: List,
        sleep_from: int,
        sleep_to: int,
        slippage: Union[int, float],
        min_percent: int,
        max_percent: int,
    ):
        random.shuffle(tokens)

        logger.info(f"[{self.address}] Start swap tokens")

        for _, token in enumerate(tokens, start=1):
            if token == "ETH":
                continue

            balance = await self.get_balance(self.config.TOKENS[token])

            if balance["balance_wei"] > 0:
                swap_module = self.get_swap_module()
                await swap_module.swap(
                    token,
                    "ETH",
                    balance["balance"],
                    balance["balance"],
                    balance["decimal"],
                    slippage,
                    True,
                    min_percent,
                    max_percent,
                )

            if _ != len(tokens):
                await sleep(sleep_from, sleep_to)
