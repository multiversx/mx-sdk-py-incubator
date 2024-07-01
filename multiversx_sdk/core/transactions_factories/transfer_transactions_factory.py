from typing import List, Optional, Protocol, Sequence

from multiversx_sdk.core.errors import BadUsageError
from multiversx_sdk.core.interfaces import IAddress, ITokenTransfer
from multiversx_sdk.core.tokens import TokenComputer, TokenTransfer
from multiversx_sdk.core.transaction import Transaction
from multiversx_sdk.core.transactions_factories.token_transfers_data_builder import \
    TokenTransfersDataBuilder
from multiversx_sdk.core.transactions_factories.transaction_builder import \
    TransactionBuilder

ADDITIONAL_GAS_FOR_ESDT_TRANSFER = 100000
ADDITIONAL_GAS_FOR_ESDT_NFT_TRANSFER = 800000


class IConfig(Protocol):
    chain_id: str
    min_gas_limit: int
    gas_limit_per_byte: int
    gas_limit_esdt_transfer: int
    gas_limit_esdt_nft_transfer: int
    gas_limit_multi_esdt_nft_transfer: int


class TransferTransactionsFactory:
    def __init__(self, config: IConfig) -> None:
        self.config = config
        self.token_computer = TokenComputer()
        self._data_args_builder = TokenTransfersDataBuilder(self.token_computer)

    def create_transaction_for_native_token_transfer(self,
                                                     sender: IAddress,
                                                     receiver: IAddress,
                                                     native_amount: int,
                                                     data: Optional[str] = None) -> Transaction:
        transaction_data = data if data else ""
        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=receiver,
            data_parts=[transaction_data],
            gas_limit=0,
            add_data_movement_gas=True,
            amount=native_amount
        ).build()

    def create_transaction_for_esdt_token_transfer(self,
                                                   sender: IAddress,
                                                   receiver: IAddress,
                                                   token_transfers: Sequence[ITokenTransfer]) -> Transaction:
        data_parts: List[str] = []
        extra_gas_for_transfer = 0

        if len(token_transfers) == 0:
            raise BadUsageError("No token transfer has been provided")
        elif len(token_transfers) == 1:
            transfer = token_transfers[0]

            if self.token_computer.is_fungible(transfer.token):
                data_parts = self._data_args_builder.build_args_for_esdt_transfer(transfer)
                extra_gas_for_transfer = self.config.gas_limit_esdt_transfer + ADDITIONAL_GAS_FOR_ESDT_TRANSFER
            else:
                data_parts = self._data_args_builder.build_args_for_single_esdt_nft_transfer(transfer, receiver)
                extra_gas_for_transfer = self.config.gas_limit_esdt_nft_transfer + ADDITIONAL_GAS_FOR_ESDT_NFT_TRANSFER
                receiver = sender
        else:
            data_parts = self._data_args_builder.build_args_for_multi_esdt_nft_transfer(receiver, token_transfers)
            extra_gas_for_transfer = self.config.gas_limit_multi_esdt_nft_transfer * len(token_transfers) + ADDITIONAL_GAS_FOR_ESDT_NFT_TRANSFER
            receiver = sender

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=receiver,
            data_parts=data_parts,
            gas_limit=extra_gas_for_transfer,
            add_data_movement_gas=True
        ).build()

    def create_transaction_for_transfer(self,
                                        sender: IAddress,
                                        receiver: IAddress,
                                        native_amount: Optional[int] = None,
                                        token_transfers: Optional[Sequence[ITokenTransfer]] = None,
                                        data: Optional[bytes] = None) -> Transaction:
        if not native_amount and not token_transfers:
            raise BadUsageError("No native token amount or token transfers provided")

        if token_transfers and data:
            raise BadUsageError("Can't set data field when sending esdt tokens")

        if native_amount and not token_transfers:
            return self.create_transaction_for_native_token_transfer(
                sender=sender,
                receiver=receiver,
                native_amount=native_amount,
                data=data.decode() if data else None
            )

        token_transfers = list(token_transfers) if token_transfers else []

        native_transfer = TokenTransfer.new_from_native_amount(native_amount) if native_amount else None
        token_transfers.append(native_transfer) if native_transfer else None

        return self.create_transaction_for_esdt_token_transfer(
            sender=sender,
            receiver=receiver,
            token_transfers=token_transfers
        )
