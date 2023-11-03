import pytest
from multiversx_sdk_core import Address, Transaction

from multiversx_sdk_network_providers.proxy_network_provider import (
    ContractQuery, ProxyNetworkProvider)


class TestProxy:
    proxy = ProxyNetworkProvider("https://devnet-gateway.multiversx.com")

    def test_get_network_config(self):
        result = self.proxy.get_network_config()

        assert result.chain_id == "D"
        assert result.gas_per_data_byte == 1500
        assert result.round_duration == 6000
        assert result.rounds_per_epoch == 2400
        assert result.min_gas_limit == 50000
        assert result.min_gas_price == 1_000_000_000
        assert result.min_transaction_version == 1
        assert result.top_up_factor == 0.5
        assert result.num_shards_without_meta == 3

    def test_get_network_status(self):
        result = self.proxy.get_network_status()

        assert result.nonce > 0
        assert result.current_round > 0
        assert result.epoch_number > 0
        assert result.round_at_epoch_start > 0
        assert result.rounds_passed_in_current_epcoch > 0
        assert result.nonces_passed_in_current_epoch > 0
        assert result.highest_final_nonce > 0
        assert result.nonce_at_epoch_start > 0
        assert result.rounds_per_epoch == 2400

    def test_get_network_gas_configs(self):
        result = self.proxy.get_network_gas_configs()
        built_in_cost = result["gasConfigs"]["builtInCost"]
        meta_system_sc_cost = result["gasConfigs"]["metaSystemSCCost"]

        assert built_in_cost["ESDTTransfer"] == 200000
        assert meta_system_sc_cost["Stake"] == 5000000

    def test_get_account(self):
        address = Address.new_from_bech32(
            "erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl"
        )
        result = self.proxy.get_account(address)

        assert (
            result.address.to_bech32()
            == "erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl"
        )
        assert result.username == ""

    def test_get_fungible_token_of_account(self):
        address = Address.new_from_bech32(
            "erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl"
        )
        result = self.proxy.get_fungible_token_of_account(address, "TEST-ff155e")

        assert result.identifier == "TEST-ff155e"
        assert result.balance == 100000000000000000

    def test_get_nonfungible_token_of_account(self):
        address = Address.new_from_bech32(
            "erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl"
        )
        result = self.proxy.get_nonfungible_token_of_account(
            address, "NFTEST-ec88b8", 1
        )

        assert result.balance == 1
        assert result.nonce == 1
        assert result.collection == "NFTEST-ec88b8"
        assert result.identifier == "NFTEST-ec88b8-01"
        assert result.type == ""
        assert result.royalties == 25

    def test_get_transaction_status(self):
        result = self.proxy.get_transaction_status(
            "9d47c4b4669cbcaa26f5dec79902dd20e55a0aa5f4b92454a74e7dbd0183ad6c"
        )
        assert result.status == "success"

    def test_query_contract(self):
        query = ContractQuery(
            Address.new_from_bech32(
                "erd1qqqqqqqqqqqqqpgqqy34h7he2ya6qcagqre7ur7cc65vt0mxrc8qnudkr4"
            ),
            "getSum",
            0,
            [],
        )
        result = self.proxy.query_contract(query)
        assert len(result.return_data) == 1

    def test_get_definition_of_fungible_token(self):
        result = self.proxy.get_definition_of_fungible_token("TEST-ff155e")

        assert result.identifier == "TEST-ff155e"
        assert (
            result.owner.to_bech32()
            == "erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl"
        )
        assert result.can_upgrade
        assert not result.can_freeze
        assert result.decimals == 6
        assert result.supply == 100000000000

    def test_get_definition_of_token_collection(self):
        result = self.proxy.get_definition_of_token_collection("NFTEST-ec88b8")

        assert result.collection == "NFTEST-ec88b8"
        assert (
            result.owner.to_bech32()
            == "erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl"
        )
        assert result.type == "NonFungibleESDT"
        assert result.decimals == 0
        assert not result.can_freeze
        assert not result.can_pause

    def test_get_transaction(self):
        result = self.proxy.get_transaction(
            "9d47c4b4669cbcaa26f5dec79902dd20e55a0aa5f4b92454a74e7dbd0183ad6c"
        )

        assert result.nonce == 0
        assert result.block_nonce == 835600
        assert result.epoch == 348
        assert (
            result.hash
            == "9d47c4b4669cbcaa26f5dec79902dd20e55a0aa5f4b92454a74e7dbd0183ad6c"
        )
        assert result.is_completed == None
        assert (
            result.sender.to_bech32()
            == "erd18s6a06ktr2v6fgxv4ffhauxvptssnaqlds45qgsrucemlwc8rawq553rt2"
        )
        assert result.contract_results.items == []

    def test_get_transaction_with_events(self):
        transaction = self.proxy.get_transaction("6fe05e4ca01d42c96ae5182978a77fe49f26bcc14aac95ad4f19618173f86ddb")
        assert transaction.logs
        assert transaction.logs.events
        assert len(transaction.logs.events) == 2
        assert len(transaction.logs.events[0].topics) == 8
        assert transaction.logs.events[0].topics[0].hex() == "544553542d666631353565"
        assert transaction.logs.events[0].topics[1].hex() == ""
        assert transaction.logs.events[0].topics[2].hex() == "63616e4368616e67654f776e6572"

    def test_get_sc_invoking_tx(self):
        result = self.proxy.get_transaction(
            "6fe05e4ca01d42c96ae5182978a77fe49f26bcc14aac95ad4f19618173f86ddb", True
        )

        assert result.is_completed == True
        assert len(result.contract_results.items) > 0
        assert (
            result.data
            == "issue@54455354546f6b656e@54455354@016345785d8a0000@06@63616e4368616e67654f776e6572@74727565@63616e55706772616465@74727565@63616e4164645370656369616c526f6c6573@74727565"
        )
        assert sum([r.is_refund for r in result.contract_results.items]) == 1

    def test_get_hyperblock(self):
        result_by_nonce = self.proxy.get_hyperblock(835683)
        result_by_hash = self.proxy.get_hyperblock(
            "55ef33845c94111c09233d3882f17023a18f6bb86a1b7e7a5ba0c5b5030e1957"
        )

        assert result_by_nonce.get("hash") == result_by_hash.get("hash")
        assert result_by_nonce.get("nonce") == result_by_hash.get("nonce")
        assert result_by_nonce.get("round") == result_by_hash.get("round")
        assert result_by_nonce.get("epoch") == result_by_hash.get("epoch")
        assert result_by_nonce.get("numTxs") == result_by_hash.get("numTxs")
        assert result_by_nonce.get("timestamp") == result_by_hash.get("timestamp")

    def test_send_transaction(self):
        transaction = Transaction(
            sender="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            receiver="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            gas_limit=50000,
            chain_id="D",
            amount=5000000000000000000,
            nonce=100,
            gas_price=1000000000,
            version=2,
            signature=bytes.fromhex("faf50b8368cb2c20597dad671a14aa76d4c65937d6e522c64946f16ad6a250262463e444596fa7ee2af1273f6ad0329d43af48d1ae5f3b295bc8f48fdba41a05")
        )
        expected_hash = (
            "fc914860c1d137ed8baa602e561381f97c7bad80d150c5bf90760d3cfd3a4cea"
        )
        assert self.proxy.send_transaction(transaction) == expected_hash

    @pytest.mark.skip
    def test_send_transactions(self):
        first_tx = Transaction(
            sender="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            receiver="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            gas_limit=50000,
            chain_id="D",
            nonce=103,
            amount=5000000000000000000,
            gas_price=1000000000,
            version=1,
            signature=bytes.fromhex("fe444941b3d90457c5acd2441cc8be1fd7e2a42171ad074d7eb7f7536651e025a698595a04210224572b74f6588c4c0a2e6cada26dec27b7472be5803ae09705")
        )

        second_tx = Transaction(
            sender="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            receiver="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            gas_limit=50000,
            chain_id="D",
            nonce=104,
            amount=5000000000000000000,
            gas_price=1000000000,
            version=1,
            signature=bytes.fromhex("a1501d95da8f5518f0a60abc4970638a25d2919b1f901a89b924cd9b873fbe29a6f501fd7773216691850215178a8050e1469168f31455373dd85bab55eaa006")
        )

        invalid_tx = Transaction(
            sender="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            receiver="erd1487vz5m4zpxjyqw4flwa3xhnkzg4yrr3mkzf5sf0zgt94hjprc8qazcccl",
            gas_limit=50000,
            chain_id="D",
            nonce=77
        )

        transactions = [first_tx, second_tx, invalid_tx]

        expected_hashes = [
            "7e1db7f5254c5c75bec6d454aa7160d191eb0e27ad45db4c164f2c3a5b51a169",
            "b5117f1c9461162c73b12ffd43e238b6dfce70687ed3aeb02c7f6a4a0a68938f",
        ]
        assert self.proxy.send_transactions(transactions) == (
            2,
            {"0": f"{expected_hashes[0]}", "1": f"{expected_hashes[1]}"},
        )
