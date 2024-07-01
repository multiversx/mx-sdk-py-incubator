from pathlib import Path
from typing import Any, List, Optional, Protocol, Sequence, Union

from multiversx_sdk.abi.serializer import Serializer
from multiversx_sdk.abi.typesystem import is_list_of_typed_values
from multiversx_sdk.core.address import Address
from multiversx_sdk.core.code_metadata import CodeMetadata
from multiversx_sdk.core.constants import (ARGS_SEPARATOR,
                                           CONTRACT_DEPLOY_ADDRESS,
                                           VM_TYPE_WASM_VM)
from multiversx_sdk.core.interfaces import IAddress, ITokenTransfer
from multiversx_sdk.core.serializer import arg_to_string, args_to_buffers
from multiversx_sdk.core.tokens import TokenComputer, TokenTransfer
from multiversx_sdk.core.transaction import Transaction
from multiversx_sdk.core.transactions_factories.token_transfers_data_builder import \
    TokenTransfersDataBuilder
from multiversx_sdk.core.transactions_factories.transaction_builder import \
    TransactionBuilder


class IConfig(Protocol):
    chain_id: str
    min_gas_limit: int
    gas_limit_per_byte: int
    gas_limit_claim_developer_rewards: int
    gas_limit_change_owner_address: int


class IAbi(Protocol):
    def encode_endpoint_input_parameters(self, endpoint_name: str, values: List[Any]) -> List[bytes]:
        ...

    def encode_constructor_input_parameters(self, values: List[Any]) -> List[bytes]:
        ...

    def encode_upgrade_constructor_input_parameters(self, values: List[Any]) -> List[bytes]:
        ...


class SmartContractTransactionsFactory:
    def __init__(self, config: IConfig, abi: Optional[IAbi] = None) -> None:
        self.config = config
        self.abi = abi
        self.serializer = Serializer(parts_separator=ARGS_SEPARATOR)
        self.token_computer = TokenComputer()
        self._data_args_builder = TokenTransfersDataBuilder(self.token_computer)

    def create_transaction_for_deploy(self,
                                      sender: IAddress,
                                      bytecode: Union[Path, bytes],
                                      gas_limit: int,
                                      arguments: Sequence[Any] = [],
                                      native_transfer_amount: int = 0,
                                      is_upgradeable: bool = True,
                                      is_readable: bool = True,
                                      is_payable: bool = False,
                                      is_payable_by_sc: bool = True) -> Transaction:
        if isinstance(bytecode, Path):
            bytecode = bytecode.read_bytes()

        metadata = CodeMetadata(is_upgradeable, is_readable, is_payable, is_payable_by_sc)

        parts = [
            arg_to_string(bytecode),
            arg_to_string(VM_TYPE_WASM_VM),
            str(metadata)
        ]

        prepared_arguments = self._encode_deploy_arguments(list(arguments))
        parts += [arg.hex() for arg in prepared_arguments]

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=Address.new_from_bech32(CONTRACT_DEPLOY_ADDRESS),
            data_parts=parts,
            gas_limit=gas_limit,
            add_data_movement_gas=False,
            amount=native_transfer_amount
        ).build()

    def create_transaction_for_execute(self,
                                       sender: IAddress,
                                       contract: IAddress,
                                       function: str,
                                       gas_limit: int,
                                       arguments: Sequence[Any] = [],
                                       native_transfer_amount: int = 0,
                                       token_transfers: Sequence[ITokenTransfer] = []) -> Transaction:
        transfers = list(token_transfers)
        number_of_tokens = len(transfers)
        receiver = contract

        if native_transfer_amount and number_of_tokens:
            native_tranfer = TokenTransfer.new_from_native_amount(native_transfer_amount)
            transfers.append(native_tranfer)

            native_transfer_amount = 0
            number_of_tokens += 1

        data_parts: List[str] = []

        if number_of_tokens == 1:
            transfer = transfers[0]

            if self.token_computer.is_fungible(transfer.token):
                data_parts = self._data_args_builder.build_args_for_esdt_transfer(transfer=transfer)
            else:
                data_parts = self._data_args_builder.build_args_for_single_esdt_nft_transfer(
                    transfer=transfer, receiver=receiver)
                receiver = sender
        elif number_of_tokens > 1:
            data_parts = self._data_args_builder.build_args_for_multi_esdt_nft_transfer(
                receiver=receiver, transfers=transfers)
            receiver = sender

        prepared_arguments = self._encode_execute_arguments(function, list(arguments))

        data_parts.append(function) if not data_parts else data_parts.append(arg_to_string(function))
        data_parts += [arg.hex() for arg in prepared_arguments]

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=receiver,
            data_parts=data_parts,
            gas_limit=gas_limit,
            add_data_movement_gas=False,
            amount=native_transfer_amount
        ).build()

    def create_transaction_for_upgrade(self,
                                       sender: IAddress,
                                       contract: IAddress,
                                       bytecode: Union[Path, bytes],
                                       gas_limit: int,
                                       arguments: Sequence[Any] = [],
                                       native_transfer_amount: int = 0,
                                       is_upgradeable: bool = True,
                                       is_readable: bool = True,
                                       is_payable: bool = False,
                                       is_payable_by_sc: bool = True) -> Transaction:
        if isinstance(bytecode, Path):
            bytecode = bytecode.read_bytes()

        metadata = CodeMetadata(is_upgradeable, is_readable, is_payable, is_payable_by_sc)

        parts = [
            "upgradeContract",
            arg_to_string(bytecode),
            str(metadata)
        ]

        prepared_arguments = self._encode_upgrade_arguments(list(arguments))
        parts += [arg.hex() for arg in prepared_arguments]

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=contract,
            data_parts=parts,
            gas_limit=gas_limit,
            add_data_movement_gas=False,
            amount=native_transfer_amount
        ).build()

    def create_transaction_for_claiming_developer_rewards(self,
                                                          sender: IAddress,
                                                          contract: IAddress) -> Transaction:
        data_parts = ["ClaimDeveloperRewards"]

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=contract,
            data_parts=data_parts,
            gas_limit=self.config.gas_limit_claim_developer_rewards,
            add_data_movement_gas=False
        ).build()

    def create_transaction_for_changing_owner_address(self,
                                                      sender: IAddress,
                                                      contract: IAddress,
                                                      new_owner: IAddress) -> Transaction:
        data_parts = ["ChangeOwnerAddress", new_owner.to_hex()]

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=contract,
            data_parts=data_parts,
            gas_limit=self.config.gas_limit_change_owner_address,
            add_data_movement_gas=False,
        ).build()

    def _encode_deploy_arguments(self, args: List[Any]) -> List[bytes]:
        if self.abi:
            return self.abi.encode_constructor_input_parameters(args)

        if is_list_of_typed_values(args):
            return self.serializer.serialize_to_parts(args)

        return args_to_buffers(args)

    def _encode_execute_arguments(self, function_name: str, args: List[Any]) -> List[bytes]:
        if self.abi:
            return self.abi.encode_endpoint_input_parameters(function_name, args)

        if is_list_of_typed_values(args):
            return self.serializer.serialize_to_parts(args)

        return args_to_buffers(args)

    def _encode_upgrade_arguments(self, args: List[Any]) -> List[bytes]:
        if self.abi:
            return self.abi.encode_upgrade_constructor_input_parameters(args)

        if is_list_of_typed_values(args):
            return self.serializer.serialize_to_parts(args)

        return args_to_buffers(args)
