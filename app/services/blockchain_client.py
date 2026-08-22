from web3 import Web3
import json
from pathlib import Path
from app.core.config import settings

w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_URL))

def get_contract_and_account():
    artifact_path = Path(__file__).resolve().parents[2] / "artifacts" / "contracts" / "SanjeevaniEscrow.sol" / "SanjeevaniEscrow.json"
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Compiled contract artifact not found at {artifact_path}. Run 'npx hardhat compile'."
        )

    with artifact_path.open(encoding="utf-8") as artifact_file:
        abi = json.load(artifact_file)["abi"]

    contract = w3.eth.contract(
        address=w3.to_checksum_address(settings.CONTRACT_ADDRESS),
        abi=abi,
    )
    return contract, w3.eth.accounts[0]


def create_loan(data):
    contract, account = get_contract_and_account()
    lender = Web3.to_checksum_address(data["lender"])
    equipment = contract.functions.equipments(data["equipment_id"]).call()
    if not equipment[4]:
        raise ValueError("Equipment is not registered")

    rent = equipment[2] * data["quantity"] * data["duration"]
    deposit = equipment[3] * data["quantity"]
    total_value = rent + deposit

    tx = contract.functions.createLoanRequest(
        lender,
        data["equipment_id"],
        data["quantity"],
        data["duration"]
    ).build_transaction({
        "from": account,
        "value": total_value,
        "nonce": w3.eth.get_transaction_count(account),
        "gas": 3000000,
        "gasPrice": w3.to_wei("1", "gwei")
    })

    tx_hash = w3.eth.send_transaction(tx)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "tx_hash": tx_hash.hex(),
        "status": receipt.status # type:ignore
    }