from web3 import Web3
from web3.types import TxParams
import json

from app.core.config import settings

# ---------------------------------------------------------
# BLOCKCHAIN CONNECTION
# ---------------------------------------------------------

w3 = Web3(
    Web3.HTTPProvider(
        settings.BLOCKCHAIN_RPC_URL
    )
)

if not w3.is_connected():
    raise RuntimeError(
        f"Unable to connect to blockchain RPC: "
        f"{settings.BLOCKCHAIN_RPC_URL}"
    )


# ---------------------------------------------------------
# CONTRACT ABI
# ---------------------------------------------------------

with open(
    "artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json",
    "r"
) as f:
    contract_json = json.load(f)

abi = contract_json["abi"]


# ---------------------------------------------------------
# CONTRACT
# ---------------------------------------------------------

contract = w3.eth.contract(
    address=w3.to_checksum_address(
        settings.CONTRACT_ADDRESS
    ),
    abi=abi
)


# ---------------------------------------------------------
# CHECK WHETHER A WALLET IS REGISTERED
# ---------------------------------------------------------

def is_registered_wallet(wallet: str) -> bool:

    wallet = w3.to_checksum_address(wallet)

    return contract.functions.registeredUsers(
        wallet
    ).call()


# ---------------------------------------------------------
# CREATE LOAN
# ---------------------------------------------------------

def create_loan(data):

    borrower = w3.to_checksum_address(
        data["borrower"]
    )

    lender = w3.to_checksum_address(
        data["lender"]
    )

    equipment_id = int(
        data["equipment_id"]
    )

    quantity = int(
        data["quantity"]
    )

    duration = int(
        data["duration"]
    )

    value = int(
        data["value"]
    )

    # The borrower is the transaction sender.
    tx: TxParams = {
        "from": borrower,
        "value": value,
        "nonce": w3.eth.get_transaction_count(borrower),
        "gas": 3000000,
        "gasPrice": w3.to_wei("1", "gwei"),
    }

    tx = contract.functions.createLoanRequest(
        lender,
        equipment_id,
        quantity,
        duration
    ).build_transaction(tx)

    # -----------------------------------------------------
    # IMPORTANT:
    # For the current local Ganache prototype,
    # transactions can be sent from the unlocked
    # Ganache account directly.
    # -----------------------------------------------------

    tx_hash = w3.eth.send_transaction(tx)

    receipt = w3.eth.wait_for_transaction_receipt(
        tx_hash
    )

    return {
        "tx_hash": tx_hash.hex(),
        "status": receipt.status
    }