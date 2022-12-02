from typing import Tuple

from erdpy_core import bech32
from erdpy_core.errors import ErrBadAddress, ErrBadPubkeyLength

SC_HEX_PUBKEY_PREFIX = "0" * 16
DEFAULT_HRP = "erd"
PUBKEY_LENGTH = 32
PUBKEY_STRING_LENGTH = PUBKEY_LENGTH * 2  # hex-encoded
BECH32_LENGTH = 62


class Address():
    def __init__(self, pubkey: bytes, hrp: str):
        if len(pubkey) != PUBKEY_LENGTH:
            raise ErrBadPubkeyLength(len(pubkey), PUBKEY_LENGTH)

        self.pubkey = bytes(pubkey)
        self.hrp = hrp

    @classmethod
    def from_bech32(cls, value: str) -> 'Address':
        hrp, pubkey = _decode_bech32(value)
        return cls(pubkey, hrp)

    @classmethod
    def from_hex(cls, value: str, hrp: str) -> 'Address':
        pubkey = bytes.fromhex(value)
        return cls(pubkey, hrp)

    def hex(self) -> str:
        return self.pubkey.hex()

    def bech32(self) -> str:
        converted = bech32.convertbits(self.pubkey, 8, 5)
        assert converted is not None
        encoded = bech32.bech32_encode(self.hrp, converted)
        return encoded

    def is_smart_contract(self):
        return self.hex().startswith(SC_HEX_PUBKEY_PREFIX)

    def __repr__(self):
        return self.bech32()


class AddressFactory():
    def __init__(self, hrp: str = DEFAULT_HRP) -> None:
        self.hrp = hrp

    def create_zero(self) -> Address:
        return Address(bytearray(32), self.hrp)

    def create_from_bech32(self, value: str) -> Address:
        hrp, pubkey = _decode_bech32(value)
        if hrp != self.hrp:
            raise ErrBadAddress(value)

        return Address(pubkey, hrp)

    def create_from_pubkey(self, pubkey: bytes) -> Address:
        return Address(pubkey, self.hrp)

    def create_from_hex(self, value: str) -> Address:
        return Address.from_hex(value, self.hrp)


class AddressConverter():
    def __init__(self, hrp: str = DEFAULT_HRP) -> None:
        self.hrp = hrp

    def bech32_to_pubkey(self, value: str) -> bytes:
        hrp, pubkey = _decode_bech32(value)
        if hrp != self.hrp:
            raise ErrBadAddress(value)

        return pubkey

    def pubkey_to_bech32(self, pubkey: bytes) -> str:
        address = Address(pubkey, self.hrp)
        return address.bech32()


def _decode_bech32(value: str) -> Tuple[str, bytes]:
    hrp, value_bytes = bech32.bech32_decode(value)
    if hrp is None or value_bytes is None:
        raise ErrBadAddress(value)

    decoded_bytes = bech32.convertbits(value_bytes, 5, 8, False)
    if decoded_bytes is None:
        raise ErrBadAddress(value)

    return hrp, bytearray(decoded_bytes)
