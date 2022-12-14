import os
from pathlib import Path

from erdpy_wallet.validator_pem import ValidatorPEM
from erdpy_wallet.validator_signer import ValidatorSigner


def test_sign_message():
    os.environ["MCL_SIGNER_PATH"] = str(Path("~/elrondsdk/mcl_signer/v1.0.0/signer").expanduser())

    signer = ValidatorSigner.from_pem_file(Path("./erdpy_wallet/testdata/validatorKey00.pem"))
    message = DummyMessage(b"hello")
    signature = signer.sign(message)
    assert signature.hex() == "84fd0a3a9d4f1ea2d4b40c6da67f9b786284a1c3895b7253fec7311597cda3f757862bb0690a92a13ce612c33889fd86"


def test_pem_save():
    path = Path("./erdpy_wallet/testdata/validatorKey00.pem")
    path_saved = path.with_suffix(".saved")

    with open(path) as f:
        content_expected = f.read().strip()

    pem = ValidatorPEM.from_file(path)
    pem.save(path_saved, "e7beaa95b3877f47348df4dd1cb578a4f7cabf7a20bfeefe5cdd263878ff132b765e04fef6f40c93512b666c47ed7719b8902f6c922c04247989b7137e837cc81a62e54712471c97a2ddab75aa9c2f58f813ed4c0fa722bde0ab718bff382208")

    with open(path_saved) as f:
        content_actual = f.read().strip()

    assert content_actual == content_expected
    os.remove(path_saved)


class DummyMessage:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def serialize_for_signing(self) -> bytes:
        return self.data
