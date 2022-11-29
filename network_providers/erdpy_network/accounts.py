from typing import Any, Dict
from erdpy_network.interface import IAddress
from erdpy_core import Address


class AccountOnNetwork:
    def __init__(self):
        self.address: IAddress = Address.zero()
        self.nonce: int = 0
        self.balance: int = 0
        self.code: bytes = b''
        self.username: str = ''

    @staticmethod
    def from_http_response(payload: Dict[str, Any]) -> 'AccountOnNetwork':
        result = AccountOnNetwork()

        address = payload.get('address', '')
        result.address = Address.from_bech32(address) if address else Address.zero()

        result.nonce = payload.get('nonce', 0)
        result.balance = int(payload.get('balance', 0))
        result.code = bytes.fromhex(payload.get('code', ''))
        result.username = payload.get('username', '')

        return result
