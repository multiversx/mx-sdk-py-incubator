from pathlib import Path

from multiversx_sdk.abi.abi import Abi
from multiversx_sdk.abi.biguint_value import BigUIntValue
from multiversx_sdk.abi.small_int_values import U32Value
from multiversx_sdk.core.address import Address
from multiversx_sdk.core.constants import CONTRACT_DEPLOY_ADDRESS
from multiversx_sdk.core.tokens import Token, TokenTransfer
from multiversx_sdk.core.transactions_factories.smart_contract_transactions_factory import \
    SmartContractTransactionsFactory
from multiversx_sdk.core.transactions_factories.transactions_factory_config import \
    TransactionsFactoryConfig


class TestSmartContractTransactionsFactory:
    testdata = Path(__file__).parent.parent.parent / "testutils" / "testdata"
    bytecode = (testdata / "adder.wasm").read_bytes()
    abi = Abi.load(testdata / "adder.abi.json")

    config = TransactionsFactoryConfig("D")
    factory = SmartContractTransactionsFactory(config)
    abi_aware_factory = SmartContractTransactionsFactory(config, abi)

    def test_create_transaction_for_deploy(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        gas_limit = 6000000

        # Works due to legacy encoding fallbacks.
        transaction = self.factory.create_transaction_for_deploy(
            sender=sender,
            bytecode=self.bytecode,
            gas_limit=gas_limit,
            arguments=[1]
        )

        transaction_with_typed = self.factory.create_transaction_for_deploy(
            sender=sender,
            bytecode=self.bytecode,
            gas_limit=gas_limit,
            arguments=[BigUIntValue(1)]
        )

        transaction_abi_aware_with_untyped = self.abi_aware_factory.create_transaction_for_deploy(
            sender=sender,
            bytecode=self.bytecode,
            gas_limit=gas_limit,
            arguments=[1]
        )

        transaction_abi_aware_with_typed = self.abi_aware_factory.create_transaction_for_deploy(
            sender=sender,
            bytecode=self.bytecode,
            gas_limit=gas_limit,
            arguments=[BigUIntValue(1)]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == CONTRACT_DEPLOY_ADDRESS
        assert transaction.data == f"{self.bytecode.hex()}@0500@0504@01".encode()
        assert transaction.gas_limit == gas_limit
        assert transaction.value == 0

        assert transaction_with_typed == transaction
        assert transaction_abi_aware_with_untyped == transaction
        assert transaction_abi_aware_with_typed == transaction

    def test_create_transaction_for_execute_no_transfer(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        function = "add"
        gas_limit = 6000000

        # Works due to legacy encoding fallbacks.
        transaction = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=[7]
        )

        transaction_with_typed = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=[U32Value(7)]
        )

        transaction_abi_aware_with_untyped = self.abi_aware_factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=[7]
        )

        transaction_abi_aware_with_typed = self.abi_aware_factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=[U32Value(7)]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4"
        assert transaction.gas_limit == gas_limit
        assert transaction.data
        assert transaction.data.decode() == "add@07"
        assert transaction.value == 0

        assert transaction_with_typed == transaction
        assert transaction_abi_aware_with_untyped == transaction
        assert transaction_abi_aware_with_typed == transaction

    def test_create_transaction_for_execute_and_tranfer_native_token(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        function = "add"
        gas_limit = 6000000
        args = [7]
        egld_amount = 1000000000000000000

        transaction = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=args,
            native_transfer_amount=egld_amount
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4"
        assert transaction.gas_limit == gas_limit
        assert transaction.data
        assert transaction.data.decode() == "add@07"
        assert transaction.value == 1000000000000000000

    def test_create_transaction_for_execute_and_send_single_esdt(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        function = "dummy"
        gas_limit = 6000000
        args = [7]
        token = Token("FOO-6ce17b", 0)
        transfer = TokenTransfer(token, 10)

        transaction = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=args,
            token_transfers=[transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4"
        assert transaction.gas_limit == gas_limit
        assert transaction.data
        assert transaction.data.decode() == "ESDTTransfer@464f4f2d366365313762@0a@64756d6d79@07"
        assert transaction.value == 0

    def test_create_transaction_for_execute_and_send_multiple_esdts(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqak8zt22wl2ph4tswtyc39namqx6ysa2sd8ss4xmlj3")
        function = "dummy"
        gas_limit = 6000000
        args = [7]

        foo_token = Token("FOO-6ce17b", 0)
        foo_transfer = TokenTransfer(foo_token, 10)

        bar_token = Token("BAR-5bc08f", 0)
        bar_transfer = TokenTransfer(bar_token, 3140)

        transaction = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=args,
            token_transfers=[foo_transfer, bar_transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.gas_limit == gas_limit
        assert transaction.data
        assert transaction.data.decode() == "MultiESDTNFTTransfer@00000000000000000500ed8e25a94efa837aae0e593112cfbb01b448755069e1@02@464f4f2d366365313762@@0a@4241522d356263303866@@0c44@64756d6d79@07"
        assert transaction.value == 0

    def test_create_transaction_for_execute_and_send_single_nft(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        function = "dummy"
        gas_limit = 6000000
        args = [7]
        token = Token("NFT-123456", 1)
        transfer = TokenTransfer(token, 1)

        transaction = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=args,
            token_transfers=[transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.gas_limit == gas_limit
        assert transaction.data
        assert transaction.data.decode() == "ESDTNFTTransfer@4e46542d313233343536@01@01@00000000000000000500b9353fe8407f87310c87e12fa1ac807f0485da39d152@64756d6d79@07"
        assert transaction.value == 0

    def test_create_transaction_for_execute_and_send_multiple_nfts(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        function = "dummy"
        gas_limit = 6000000
        args = [7]

        first_token = Token("NFT-123456", 1)
        first_transfer = TokenTransfer(first_token, 1)
        second_token = Token("NFT-123456", 42)
        second_transfer = TokenTransfer(second_token, 1)

        transaction = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=args,
            token_transfers=[first_transfer, second_transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.gas_limit == gas_limit
        assert transaction.data
        assert transaction.data.decode() == "MultiESDTNFTTransfer@00000000000000000500b9353fe8407f87310c87e12fa1ac807f0485da39d152@02@4e46542d313233343536@01@01@4e46542d313233343536@2a@01@64756d6d79@07"
        assert transaction.value == 0

    def test_create_transaction_for_execute_and_send_native_and_nfts(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        function = "dummy"
        gas_limit = 6000000
        args = [7]

        first_token = Token("NFT-123456", 1)
        first_transfer = TokenTransfer(first_token, 1)
        second_token = Token("NFT-123456", 42)
        second_transfer = TokenTransfer(second_token, 1)

        transaction = self.factory.create_transaction_for_execute(
            sender=sender,
            contract=contract,
            function=function,
            gas_limit=gas_limit,
            arguments=args,
            native_transfer_amount=1000000000000000000,
            token_transfers=[first_transfer, second_transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.gas_limit == gas_limit
        assert transaction.data
        assert transaction.data.decode() == "MultiESDTNFTTransfer@00000000000000000500b9353fe8407f87310c87e12fa1ac807f0485da39d152@03@4e46542d313233343536@01@01@4e46542d313233343536@2a@01@45474c442d303030303030@@0de0b6b3a7640000@64756d6d79@07"
        assert transaction.value == 0

    def test_create_transaction_for_upgrade(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract_address = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        contract = self.testdata / "adder.wasm"
        gas_limit = 6000000

        # Works due to legacy encoding fallbacks.
        transaction = self.factory.create_transaction_for_upgrade(
            sender=sender,
            contract=contract_address,
            bytecode=contract,
            gas_limit=gas_limit,
            arguments=[7]
        )

        transaction_with_typed = self.factory.create_transaction_for_upgrade(
            sender=sender,
            contract=contract_address,
            bytecode=contract,
            gas_limit=gas_limit,
            arguments=[BigUIntValue(7)]
        )

        transaction_abi_aware_with_untyped = self.abi_aware_factory.create_transaction_for_upgrade(
            sender=sender,
            contract=contract_address,
            bytecode=contract,
            gas_limit=gas_limit,
            arguments=[7]
        )

        transaction_abi_aware_with_typed = self.abi_aware_factory.create_transaction_for_upgrade(
            sender=sender,
            contract=contract_address,
            bytecode=contract,
            gas_limit=gas_limit,
            arguments=[BigUIntValue(7)]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4"
        assert transaction.data == f"upgradeContract@{self.bytecode.hex()}@0504@07".encode()
        assert transaction.data.decode().startswith("upgradeContract@")
        assert transaction.gas_limit == gas_limit
        assert transaction.value == 0

        assert transaction_with_typed == transaction
        assert transaction_abi_aware_with_untyped == transaction
        assert transaction_abi_aware_with_typed == transaction

    def test_create_transaction_for_claiming_developer_rewards(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract_address = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")

        transaction = self.factory.create_transaction_for_claiming_developer_rewards(
            sender=sender,
            contract=contract_address
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4"
        assert transaction.data.decode() == "ClaimDeveloperRewards"
        assert transaction.gas_limit == 6_000_000

    def test_create_transaction_for_changing_owner_address(self):
        sender = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
        contract_address = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4")
        new_owner = Address.from_bech32("erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx")

        transaction = self.factory.create_transaction_for_changing_owner_address(
            sender=sender,
            contract=contract_address,
            new_owner=new_owner
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qqqqqqqqqqqqqpgqhy6nl6zq07rnzry8uyh6rtyq0uzgtk3e69fqgtz9l4"
        assert transaction.data.decode() == "ChangeOwnerAddress@8049d639e5a6980d1cd2392abcce41029cda74a1563523a202f09641cc2618f8"
        assert transaction.gas_limit == 6_000_000
