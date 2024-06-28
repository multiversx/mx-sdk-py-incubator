from typing import Optional, Protocol, Sequence


class IAddress(Protocol):
    def to_bech32(self) -> str:
        ...

    def to_hex(self) -> str:
        ...


class ITransaction(Protocol):
    sender: str
    receiver: str
    gas_limit: int
    chain_id: str
    nonce: int
    value: int
    sender_username: str
    receiver_username: str
    gas_price: int
    data: bytes
    version: int
    options: int
    guardian: str
    signature: bytes
    guardian_signature: bytes
    relayer: str

    @property
    def inner_transactions(self) -> Sequence["ITransaction"]:
        ...


class IMessage(Protocol):
    data: bytes
    signature: bytes
    address: Optional[IAddress]
    version: int
    signer: str


class IToken(Protocol):
    identifier: str
    nonce: int


class ITokenTransfer(Protocol):
    @property
    def token(self) -> IToken:
        ...

    amount: int


class ITokenIdentifierParts(Protocol):
    ticker: str
    random_sequence: str
    nonce: int


class INetworkConfig(Protocol):
    min_gas_limit: int
    gas_per_data_byte: int
    gas_price_modifier: float
    chain_id: str


class IValidatorPublicKey(Protocol):
    def hex(self) -> str:
        ...
