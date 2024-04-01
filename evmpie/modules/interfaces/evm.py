from abc import ABC, abstractmethod
import asyncio
import random
from typing import Union, Type, Dict, Any
import time

from modules.interfaces.networks import Network
from modules.interfaces.account import Account
from modules.logger.logger import logger
from modules.sleep import sleep

from hexbytes import HexBytes
from config import ERC20_ABI, GAS_MULTIPLIER, MAX_PRIORITY_FEE, GAS_LIMIT_MULTIPLIER
from eth_account import Account as EthereumAccount
from web3 import AsyncWeb3
from web3.contract import Contract
from web3.exceptions import TransactionNotFound
from web3.middleware import async_geth_poa_middleware


class EVMInterface(ABC):
    def __init__(self, account: Account, network: Network, config):
        self.network = network
        self.web3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(random.choice(self.network.rpc)),
            middlewares=[async_geth_poa_middleware],
        )
        self.account = EthereumAccount.from_key(account.private_key)
        self.address = self.account.address
        self.config = config

    def set_config(self, config):
        self.config = config

    def get_config(self):
        return self.config

    async def get_eth_balance(self):
        balance = await self.web3.eth.get_balance(self.address)
        return self.web3.from_wei(balance, "ether")

    async def get_tx_data(self, value: int = 0, gas_price: bool = True):
        tx = {
            "chainId": await self.web3.eth.chain_id,
            "from": self.address,
            "value": value,
            "nonce": await self.web3.eth.get_transaction_count(self.address),
        }

        if gas_price:
            tx.update({"gasPrice": await self.web3.eth.gas_price})

        return tx

    async def transaction_fee(self, tx_data: dict):
        gas_price = await self.web3.eth.gas_price
        gas = await self.web3.eth.estimate_gas(tx_data)

        return int(gas * gas_price)

    def get_contract(
        self, contract_address: str, abi=None
    ) -> Union[Type[Contract], Contract]:
        contract_address = self.web3.to_checksum_address(contract_address)

        if abi is None:
            abi = ERC20_ABI

        contract = self.web3.eth.contract(address=contract_address, abi=abi)

        return contract

    async def get_balance(self, contract_address: str) -> Dict:
        contract_address = self.web3.to_checksum_address(contract_address)
        contract = self.get_contract(contract_address)

        symbol = await contract.functions.symbol().call()
        decimal = await contract.functions.decimals().call()
        balance_wei = await contract.functions.balanceOf(self.address).call()

        balance = balance_wei / 10**decimal

        return {
            "balance_wei": balance_wei,
            "balance": balance,
            "symbol": symbol,
            "decimal": decimal,
        }

    async def get_amount(
        self,
        from_token: str,
        min_amount: float,
        max_amount: float,
        decimal: int,
        all_amount: bool,
        min_percent: int,
        max_percent: int,
    ) -> Union[int, float, float]:
        random_amount = round(random.uniform(min_amount, max_amount), decimal)
        random_percent = random.randint(min_percent, max_percent)
        percent = 1 if random_percent == 100 else random_percent / 100

        if from_token == "ETH":
            balance = await self.web3.eth.get_balance(self.address)
            amount_wei = (
                int(balance * percent)
                if all_amount
                else self.web3.to_wei(random_amount, "ether")
            )
            amount = (
                self.web3.from_wei(int(balance * percent), "ether")
                if all_amount
                else random_amount
            )
        else:
            balance = await self.get_balance(self.config.TOKENS[from_token])
            amount_wei = (
                int(balance["balance_wei"] * percent)
                if all_amount
                else int(random_amount * 10 ** balance["decimal"])
            )
            amount = balance["balance"] * percent if all_amount else random_amount
            balance = balance["balance_wei"]

        return amount_wei, amount, balance

    async def check_allowance(self, token_address: str, contract_address: str) -> int:
        token_address = self.web3.to_checksum_address(token_address)
        contract_address = self.web3.to_checksum_address(contract_address)

        contract = self.web3.eth.contract(address=token_address, abi=ERC20_ABI)
        amount_approved = await contract.functions.allowance(
            self.address, contract_address
        ).call()

        return amount_approved

    async def approve(
        self, amount: float, token_address: str, contract_address: str
    ) -> None:
        token_address = self.web3.to_checksum_address(token_address)
        contract_address = self.web3.to_checksum_address(contract_address)

        contract = self.web3.eth.contract(address=token_address, abi=ERC20_ABI)

        allowance_amount = await self.check_allowance(token_address, contract_address)

        if amount > allowance_amount:
            logger.info(f"[{self.address}] Make approve")

            approve_amount = 2**128 if amount > allowance_amount else 0

            tx_data = await self.get_tx_data()

            transaction = await contract.functions.approve(
                contract_address, approve_amount
            ).build_transaction(tx_data)

            signed_txn = await self.sign(transaction)

            txn_hash = await self.send_raw_transaction(signed_txn)

            await self.wait_until_tx_finished(txn_hash.hex())

            await sleep(5, 20)

    async def wait_until_tx_finished(self, hash: str, max_wait_time=180) -> None:
        start_time = time.time()
        while True:
            try:
                receipts = await self.web3.eth.get_transaction_receipt(hash)
                status = receipts.get("status")
                if status == 1:
                    logger.success(
                        f"[{self.address}] {self.explorer}{hash} successfully!"
                    )
                    return
                elif status is None:
                    await asyncio.sleep(0.3)
                else:
                    logger.error(
                        f"[{self.address}] {self.explorer}{hash} transaction failed!"
                    )
                    return
            except TransactionNotFound:
                if time.time() - start_time > max_wait_time:
                    print(f"FAILED TX: {hash}")
                    return
                await asyncio.sleep(1)

    async def sign(self, transaction) -> Any:
        if transaction.get("gasPrice", None) is None:
            max_priority_fee_per_gas = self.web3.to_wei(
                MAX_PRIORITY_FEE["ethereum"], "gwei"
            )
            max_fee_per_gas = await self.web3.eth.gas_price

            transaction.update(
                {
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                    "maxFeePerGas": max_fee_per_gas,
                }
            )
        else:
            transaction.update(
                {"gasPrice": int(transaction["gasPrice"] * GAS_LIMIT_MULTIPLIER)}
            )

        gas = await self.web3.eth.estimate_gas(transaction)
        gas = int(gas * GAS_MULTIPLIER)

        transaction.update({"gas": gas})

        signed_txn = self.web3.eth.account.sign_transaction(
            transaction, self.private_key
        )

        return signed_txn

    async def send_raw_transaction(self, signed_txn) -> HexBytes:
        txn_hash = await self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        return txn_hash