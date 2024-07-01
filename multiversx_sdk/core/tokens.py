from typing import List

from multiversx_sdk.core.codec import (decode_unsigned_number,
                                       encode_unsigned_number)
from multiversx_sdk.core.constants import (
    EGLD_IDENTIFIER_FOR_MULTI_ESDTNFT_TRANSFER, TOKEN_RANDOM_SEQUENCE_LENGTH)
from multiversx_sdk.core.errors import (BadUsageError,
                                        InvalidTokenIdentifierError)
from multiversx_sdk.core.interfaces import IToken, ITokenIdentifierParts


class Token:
    def __init__(self, identifier: str, nonce: int = 0) -> None:
        self.identifier = identifier
        self.nonce = nonce


class TokenTransfer:
    def __init__(self, token: IToken, amount: int) -> None:
        """`amount` should always be in atomic units: 1.000000 "USDC-c76f1f" = "1000000"""
        self.token = token
        self.amount = amount

    @staticmethod
    def new_from_native_amount(amount: int) -> "TokenTransfer":
        native_token = Token(EGLD_IDENTIFIER_FOR_MULTI_ESDTNFT_TRANSFER)
        return TokenTransfer(native_token, amount)


class TokenIdentifierParts:
    def __init__(self, ticker: str, random_sequence: str, nonce: int) -> None:
        self.ticker = ticker
        self.random_sequence = random_sequence
        self.nonce = nonce


class TokenComputer:
    def __init__(self) -> None:
        pass

    def is_fungible(self, token: IToken) -> bool:
        return token.nonce == 0

    def extract_nonce_from_extended_identifier(self, identifier: str) -> int:
        parts = identifier.split("-")

        self._check_if_extended_identifier_was_provided(parts)
        self._check_length_of_random_sequence(parts[1])

        # in case the identifier of a fungible token is provided
        if len(parts) == 2:
            return 0

        hex_nonce = bytes.fromhex(parts[2])
        return decode_unsigned_number(hex_nonce)

    def extract_identifier_from_extended_identifier(self, identifier: str) -> str:
        parts = identifier.split("-")

        self._check_if_extended_identifier_was_provided(parts)
        self._ensure_token_ticker_validity(parts[0])
        self._check_length_of_random_sequence(parts[1])

        return parts[0] + "-" + parts[1]

    def extract_ticker_from_identifier(self, identifier: str) -> str:
        parts = identifier.split("-")

        self._check_length_of_random_sequence(parts[1])
        self._ensure_token_ticker_validity(parts[0])
        return parts[0]

    def parse_extended_identifier_parts(self, identifier: str) -> TokenIdentifierParts:
        parts = identifier.split("-")

        self._check_if_extended_identifier_was_provided(parts)
        self._check_length_of_random_sequence(parts[1])
        self._ensure_token_ticker_validity(parts[0])

        nonce = decode_unsigned_number(bytes.fromhex(parts[2])) if len(parts) == 3 else 0
        return TokenIdentifierParts(parts[0], parts[1], nonce)

    def compute_extended_identifier_from_identifier_and_nonce(self, identifier: str, nonce: int) -> str:
        identifier_parts = identifier.split("-")

        self._check_length_of_random_sequence(identifier_parts[1])
        self._ensure_token_ticker_validity(identifier_parts[0])

        if nonce < 0:
            raise BadUsageError("The token nonce can not be less than 0")

        if nonce == 0:
            return identifier

        nonce_hex = encode_unsigned_number(nonce).hex()
        return identifier + "-" + nonce_hex

    def compute_extended_identifier_from_parts(self, parts: ITokenIdentifierParts) -> str:
        identifier = parts.ticker + "-" + parts.random_sequence
        return self.compute_extended_identifier_from_identifier_and_nonce(identifier, parts.nonce)

    def _check_if_extended_identifier_was_provided(self, token_parts: List[str]) -> None:
        # this is for the identifiers of fungible tokens
        MIN_EXTENDED_IDENTIFIER_LENGTH_IF_SPLIT = 2
        # this is for the identifiers of nft, sft and meta-esdt
        MAX_EXTENDED_IDENTIFIER_LENGTH_IF_SPLIT = 3

        if len(token_parts) < MIN_EXTENDED_IDENTIFIER_LENGTH_IF_SPLIT or len(token_parts) > MAX_EXTENDED_IDENTIFIER_LENGTH_IF_SPLIT:
            raise InvalidTokenIdentifierError("Invalid extended token identifier provided")

    def _ensure_token_ticker_validity(self, ticker: str) -> None:
        MIN_TICKER_LENGTH = 3
        MAX_TICKER_LENGTH = 10

        if len(ticker) < MIN_TICKER_LENGTH or len(ticker) > MAX_TICKER_LENGTH:
            raise InvalidTokenIdentifierError(f"The token ticker should be between {MIN_TICKER_LENGTH} and {MAX_TICKER_LENGTH} characters")

        if not ticker.isalnum():
            raise InvalidTokenIdentifierError("The token ticker should only contain alphanumeric characters")

        if not ticker.isupper():
            raise InvalidTokenIdentifierError("The token ticker should be upper case")

    def _check_length_of_random_sequence(self, random_sequence: str) -> None:
        if len(random_sequence) != TOKEN_RANDOM_SEQUENCE_LENGTH:
            raise InvalidTokenIdentifierError("The identifier is not valid. The random sequence does not have the right length")
