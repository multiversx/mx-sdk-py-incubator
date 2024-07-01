import pytest

from multiversx_sdk.core.address import Address
from multiversx_sdk.core.errors import BadUsageError
from multiversx_sdk.core.tokens import Token, TokenTransfer
from multiversx_sdk.core.transactions_factories.transactions_factory_config import \
    TransactionsFactoryConfig
from multiversx_sdk.core.transactions_factories.transfer_transactions_factory import \
    TransferTransactionsFactory


class TestTransferTransactionsFactory:
    transfer_factory = TransferTransactionsFactory(TransactionsFactoryConfig("D"))
    alice = Address.new_from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")
    bob = Address.new_from_bech32("erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx")

    def test_create_transaction_for_native_token_transfer_no_data(self):
        transaction = self.transfer_factory.create_transaction_for_native_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx"
        assert transaction.value == 1000000000000000000
        assert transaction.chain_id == "D"
        assert transaction.gas_limit == 50_000
        assert transaction.data == b""

    def test_create_transaction_for_native_token_transfer_with_data(self):
        transaction = self.transfer_factory.create_transaction_for_native_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000,
            data="test data"
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx"
        assert transaction.value == 1000000000000000000
        assert transaction.chain_id == "D"
        assert transaction.gas_limit == 63_500
        assert transaction.data == b"test data"

    def test_create_transaction_for_esdt_transfer(self):
        foo_token = Token("FOO-123456")
        token_transfer = TokenTransfer(foo_token, 1000000)

        transaction = self.transfer_factory.create_transaction_for_esdt_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            token_transfers=[token_transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "ESDTTransfer@464f4f2d313233343536@0f4240"
        assert transaction.gas_limit == 410_000

    def test_create_transaction_for_nft_transfer(self):
        nft = Token("NFT-123456", 10)
        token_transfer = TokenTransfer(nft, 1)

        transaction = self.transfer_factory.create_transaction_for_esdt_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            token_transfers=[token_transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "ESDTNFTTransfer@4e46542d313233343536@0a@01@8049d639e5a6980d1cd2392abcce41029cda74a1563523a202f09641cc2618f8"
        assert transaction.gas_limit == 1_210_500

    def test_create_transaction_for_multiple_nft_transfers(self):
        first_nft = Token("NFT-123456", 10)
        first_transfer = TokenTransfer(first_nft, 1)

        second_nft = Token("TEST-987654", 1)
        second_transfer = TokenTransfer(second_nft, 1)

        transaction = self.transfer_factory.create_transaction_for_esdt_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            token_transfers=[first_transfer, second_transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "MultiESDTNFTTransfer@8049d639e5a6980d1cd2392abcce41029cda74a1563523a202f09641cc2618f8@02@4e46542d313233343536@0a@01@544553542d393837363534@01@01"
        assert transaction.gas_limit == 1_466_000

    def test_create_transaction_for_token_transfer_with_errors(self):
        with pytest.raises(BadUsageError, match="No native token amount or token transfers provided"):
            self.transfer_factory.create_transaction_for_transfer(
                sender=self.alice,
                receiver=self.bob
            )

        with pytest.raises(BadUsageError, match="Can't set data field when sending esdt tokens"):
            nft = Token("NFT-123456", 10)
            transfer = TokenTransfer(nft, 1)

            self.transfer_factory.create_transaction_for_transfer(
                sender=self.alice,
                receiver=self.bob,
                token_transfers=[transfer],
                data="hello".encode()
            )

    def test_create_transaction_for_token_transfer(self):
        first_nft = Token("NFT-123456", 10)
        first_transfer = TokenTransfer(first_nft, 1)

        second_nft = Token("TEST-987654", 1)
        second_transfer = TokenTransfer(second_nft, 1)

        transaction = self.transfer_factory.create_transaction_for_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000,
            token_transfers=[first_transfer, second_transfer]
        )

        assert transaction.sender == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.receiver == "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "MultiESDTNFTTransfer@8049d639e5a6980d1cd2392abcce41029cda74a1563523a202f09641cc2618f8@03@4e46542d313233343536@0a@01@544553542d393837363534@01@01@45474c442d303030303030@@0de0b6b3a7640000"
        assert transaction.gas_limit == 1_727_500
