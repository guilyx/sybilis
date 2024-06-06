from modules.interfaces.evm import EVMInterface
from modules.interfaces.account import Account
from modules.tools import retry, check_gas
from modules.logger.logger import logger
from modules.exceptions import BlockchainException

from config import NETWORKS
from config import EthereumSettings

import random
from typing import List, Union


class Ethereum(EVMInterface):
    def __init__(self, account: Account):
        super().__init__(account, NETWORKS["ethereum"], EthereumSettings())
        self.swap_modules = {}

    def get_swap_module(self):
        swap_module = random.choice(self.swap_modules)
        return self.swap_modules[swap_module]

    @retry
    @check_gas
    async def deposit_scroll(
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

        logger.info(f"[{self.address}] Bridge to Scroll | {amount} ETH")

        contract = self.get_contract(
            self.config.BRIDGE_CONTRACTS["deposit"], self.config.DEPOSIT_ABI
        )
        contract_oracle = self.get_contract(
            self.config.BRIDGE_CONTRACTS["oracle"], self.config.ORACLE_ABI
        )

        fee = int(
            await contract_oracle.functions.estimateCrossDomainMessageFee(168000).call()
            * 1.2
        )

        total_tx_wei = fee + amount_wei
        total_tx_eth = self.web3.from_wei(total_tx_wei * 1.2, "ether")

        logger.info(
            f"[{self.address}] Bridge to Scroll | Amount + Fees is {total_tx_eth} ETH"
        )

        logger.info(
            f"[{self.address}] Bridge to Scroll | Expected {self.web3.from_wei(fee, 'ether')} ETH fee..."
        )

        tx_data = await self.get_tx_data(total_tx_wei, False)

        logger.info(f"[{self.address}] Bridge to Scroll | TX Data: {tx_data}")

        transaction = await contract.functions.depositETH(
            total_tx_wei,
            168000,
        ).build_transaction(tx_data)

        logger.info(f"[{self.address}] Bridge to Scroll | TX Built: {transaction}")

        raise Exception("Stoccazo")

        signed_txn = await self.sign(transaction)

        logger.info(f"[{self.address}] Bridge to Scroll | TX Signed")

        txn_hash = await self.send_raw_transaction(signed_txn)

        logger.info(f"[{self.address}] Bridge to Scroll | TX Sent: {txn_hash}")

        await self.wait_until_tx_finished(txn_hash.hex())
