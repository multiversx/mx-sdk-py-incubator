import pytest

from multiversx_sdk.core.errors import BadUsageError
from multiversx_sdk.core.tokens import (Token, TokenComputer,
                                        TokenIdentifierParts, TokenTransfer)


class TestTokenComputer:
    token_computer = TokenComputer()

    def test_token_is_fungible(self):
        fungible_token = Token("TEST-123456")
        non_fungible_token = Token("NFT-987654", 7)

        assert self.token_computer.is_fungible(fungible_token)
        assert not self.token_computer.is_fungible(non_fungible_token)

    def test_extract_nonce_from_extended_identifier(self):
        extended_nft_identifier = "TEST-123456-0a"
        extended_fungible_identifier = "FNG-123456"

        assert self.token_computer.extract_nonce_from_extended_identifier(extended_nft_identifier) == 10
        assert self.token_computer.extract_nonce_from_extended_identifier(extended_fungible_identifier) == 0

    def test_extract_identifier_from_extended_identifier(self):
        extended_nft_identifier = "TEST-123456-0a"
        extended_fungible_identifier = "FNG-123456"

        assert self.token_computer.extract_identifier_from_extended_identifier(extended_nft_identifier) == "TEST-123456"
        assert self.token_computer.extract_identifier_from_extended_identifier(extended_fungible_identifier) == "FNG-123456"

    def test_extract_ticker_from_identifier(self):
        fungible_identifier = "FNG-123456"
        non_fungible_identifier = "NFT-987654-0a"

        assert self.token_computer.extract_ticker_from_identifier(fungible_identifier) == "FNG"
        assert self.token_computer.extract_ticker_from_identifier(non_fungible_identifier) == "NFT"

    def test_parse_extended_identifier_parts(self):
        fungible_identifier = "FNG-123456"
        non_fungible_identifier = "NFT-987654-0a"

        fungible_parts = self.token_computer.parse_extended_identifier_parts(fungible_identifier)
        non_fungible_parts = self.token_computer.parse_extended_identifier_parts(non_fungible_identifier)

        assert fungible_parts.ticker == "FNG"
        assert fungible_parts.random_sequence == "123456"
        assert fungible_parts.nonce == 0

        assert non_fungible_parts.ticker == "NFT"
        assert non_fungible_parts.random_sequence == "987654"
        assert non_fungible_parts.nonce == 10

    def test_compute_extended_identifier_from_identifier_and_bad_nonce(self):
        fungible_identifier = "FNG-123456"
        fungible_nonce = -10

        with pytest.raises(BadUsageError, match="The token nonce can not be less than 0"):
            self.token_computer.compute_extended_identifier_from_identifier_and_nonce(
                fungible_identifier, fungible_nonce
            )

    def test_compute_extended_identifier_from_identifier_and_nonce(self):
        fungible_identifier = "FNG-123456"
        fungible_nonce = 0

        non_fungible_identifier = "NFT-987654"
        non_fungible_nonce = 10

        fungible_token_identifier = self.token_computer.compute_extended_identifier_from_identifier_and_nonce(
            fungible_identifier, fungible_nonce
        )
        nft_identifier = self.token_computer.compute_extended_identifier_from_identifier_and_nonce(
            non_fungible_identifier, non_fungible_nonce
        )

        assert fungible_token_identifier == "FNG-123456"
        assert nft_identifier == "NFT-987654-0a"

    def test_compute_extended_identifier_from_parts(self):
        fungible_parts = TokenIdentifierParts("FNG", "123456", 0)
        nft_parts = TokenIdentifierParts("NFT", "987654", 10)

        fungible_identifier = self.token_computer.compute_extended_identifier_from_parts(fungible_parts)
        nft_identifier = self.token_computer.compute_extended_identifier_from_parts(nft_parts)

        assert fungible_identifier == "FNG-123456"
        assert nft_identifier == "NFT-987654-0a"


def test_token_transfer_from_native_amount():
    transfer = TokenTransfer.new_from_native_amount(1000000000000000000)

    assert transfer.token.identifier == "EGLD-000000"
    assert transfer.token.nonce == 0
    assert transfer.amount == 1000000000000000000
