"""
blockchain_tools.py — Web3 helpers for SanjeevaniEscrow.sol

Contract functions used:
  registerEquipment(name, hourlyRate, cautionDeposit)
  createLoanRequest(lender, equipmentId, quantity, durationHours)  payable
  confirmDelivery(loanId)
  markReturned(loanId)
  settleLoan(loanId)

Events:
  EquipmentRegistered, LoanCreated, DeliveryConfirmed,
  ReturnRequested, LoanSettled
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ── Connection ────────────────────────────────────────────────────────────────
RPC_URL          = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")          # set after deploy
PRIVATE_KEY      = os.getenv("DEPLOYER_PRIVATE_KEY")      # hardhat account #0

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# ── ABI (only the functions + events we need) ─────────────────────────────────
ABI = json.loads("""
[
  {
    "inputs": [
      {"internalType": "string",  "name": "_name",           "type": "string"},
      {"internalType": "uint256", "name": "_hourlyRate",     "type": "uint256"},
      {"internalType": "uint256", "name": "_cautionDeposit", "type": "uint256"}
    ],
    "name": "registerEquipment",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {"internalType": "address", "name": "_lender",        "type": "address"},
      {"internalType": "uint256", "name": "_equipmentId",   "type": "uint256"},
      {"internalType": "uint256", "name": "_quantity",      "type": "uint256"},
      {"internalType": "uint256", "name": "_durationHours", "type": "uint256"}
    ],
    "name": "createLoanRequest",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "_loanId", "type": "uint256"}],
    "name": "confirmDelivery",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "_loanId", "type": "uint256"}],
    "name": "markReturned",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "_loanId", "type": "uint256"}],
    "name": "settleLoan",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "name": "loans",
    "outputs": [
      {"internalType": "uint256", "name": "loanId",           "type": "uint256"},
      {"internalType": "address", "name": "borrower",         "type": "address"},
      {"internalType": "address", "name": "lender",           "type": "address"},
      {"internalType": "uint256", "name": "equipmentId",      "type": "uint256"},
      {"internalType": "uint256", "name": "quantity",         "type": "uint256"},
      {"internalType": "uint256", "name": "startTime",        "type": "uint256"},
      {"internalType": "uint256", "name": "expectedDuration", "type": "uint256"},
      {"internalType": "uint256", "name": "depositAmount",    "type": "uint256"},
      {"internalType": "uint256", "name": "rentAmount",       "type": "uint256"},
      {"internalType": "uint8",   "name": "status",           "type": "uint8"}
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "loanCounter",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "equipmentCounter",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "name": "equipments",
    "outputs": [
      {"internalType": "uint256", "name": "id",             "type": "uint256"},
      {"internalType": "string",  "name": "name",           "type": "string"},
      {"internalType": "uint256", "name": "hourlyRate",     "type": "uint256"},
      {"internalType": "uint256", "name": "cautionDeposit", "type": "uint256"},
      {"internalType": "bool",    "name": "exists",         "type": "bool"}
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": false, "name": "loanId",        "type": "uint256"},
      {"indexed": false, "name": "borrower",      "type": "address"},
      {"indexed": false, "name": "lender",        "type": "address"},
      {"indexed": false, "name": "equipmentId",   "type": "uint256"},
      {"indexed": false, "name": "quantity",      "type": "uint256"},
      {"indexed": false, "name": "depositAmount", "type": "uint256"}
    ],
    "name": "LoanCreated",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": false, "name": "loanId",   "type": "uint256"},
      {"indexed": false, "name": "borrower", "type": "address"},
      {"indexed": false, "name": "lender",   "type": "address"}
    ],
    "name": "DeliveryConfirmed",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": false, "name": "loanId",          "type": "uint256"},
      {"indexed": false, "name": "rentPaid",         "type": "uint256"},
      {"indexed": false, "name": "depositReturned",  "type": "uint256"}
    ],
    "name": "LoanSettled",
    "type": "event"
  }
]
""")

LOAN_STATUSES = {
    0: "REQUESTED",
    1: "ACTIVE",
    2: "RETURN_PENDING",
    3: "COMPLETED",
    4: "DISPUTE"
}

# ── Contract instance ─────────────────────────────────────────────────────────

def _get_contract():
    if not CONTRACT_ADDRESS:
        raise ValueError("CONTRACT_ADDRESS not set in .env")
    return w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=ABI
    )

def _account():
    return w3.eth.account.from_key(PRIVATE_KEY)

def _send_tx(fn, value_wei=0):
    """Build, sign and send a transaction. Returns receipt dict."""
    account = _account()
    tx = fn.build_transaction({
        "from":     account.address,
        "nonce":    w3.eth.get_transaction_count(account.address),
        "gas":      500_000,
        "gasPrice": w3.eth.gas_price,
        "value":    value_wei,
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    return {
        "tx_hash":     tx_hash.hex(),
        "block":       receipt.blockNumber,
        "status":      "success" if receipt.status == 1 else "failed",
        "gas_used":    receipt.gasUsed,
    }


# ── Public helpers ────────────────────────────────────────────────────────────

def register_equipment_on_chain(name: str, hourly_rate_wei: int, caution_deposit_wei: int) -> dict:
    """Register a new equipment type on-chain. Returns tx info + new equipment ID."""
    try:
        contract = _get_contract()
        fn = contract.functions.registerEquipment(name, hourly_rate_wei, caution_deposit_wei)
        receipt_info = _send_tx(fn)
        new_id = contract.functions.equipmentCounter().call()
        return {**receipt_info, "equipment_id": new_id}
    except Exception as e:
        return {"error": str(e)}


def create_loan_on_chain(
    lender_wallet: str,
    equipment_id: int,
    quantity: int,
    duration_hours: int,
    borrower_wallet: str,
) -> dict:
    """
    Create a loan request on-chain. Calculates required ETH (rent + deposit)
    automatically from contract state and sends the payable tx.
    Returns tx_hash + loan_id.
    """
    try:
        contract = _get_contract()

        # Fetch equipment pricing from contract
        eq = contract.functions.equipments(equipment_id).call()
        # eq = (id, name, hourlyRate, cautionDeposit, exists)
        if not eq[4]:
            return {"error": f"Equipment ID {equipment_id} not registered on-chain"}

        hourly_rate     = eq[2]   # wei
        caution_deposit = eq[3]   # wei

        rent    = hourly_rate * quantity * duration_hours
        deposit = caution_deposit * quantity
        total   = rent + deposit

        fn = contract.functions.createLoanRequest(
            Web3.to_checksum_address(lender_wallet),
            equipment_id,
            quantity,
            duration_hours
        )
        receipt_info = _send_tx(fn, value_wei=total)

        # Loan ID = current loanCounter after tx
        loan_id = contract.functions.loanCounter().call()

        return {
            **receipt_info,
            "loan_id":        loan_id,
            "rent_wei":       rent,
            "deposit_wei":    deposit,
            "total_paid_wei": total,
            "lender":         lender_wallet,
            "borrower":       borrower_wallet,
        }
    except Exception as e:
        return {"error": str(e)}


def confirm_delivery_on_chain(loan_id: int, confirmer_wallet: str) -> dict:
    """Confirm delivery (REQUESTED → ACTIVE). Caller must be borrower or lender."""
    try:
        contract = _get_contract()
        fn = contract.functions.confirmDelivery(loan_id)
        receipt_info = _send_tx(fn)
        return {**receipt_info, "loan_id": loan_id, "new_status": "ACTIVE"}
    except Exception as e:
        return {"error": str(e)}


def mark_returned_on_chain(loan_id: int) -> dict:
    """Borrower marks equipment as returned (ACTIVE → RETURN_PENDING)."""
    try:
        contract = _get_contract()
        fn = contract.functions.markReturned(loan_id)
        receipt_info = _send_tx(fn)
        return {**receipt_info, "loan_id": loan_id, "new_status": "RETURN_PENDING"}
    except Exception as e:
        return {"error": str(e)}


def settle_loan_on_chain(loan_id: int) -> dict:
    """Settle loan (RETURN_PENDING → COMPLETED). Releases escrow to lender + refunds deposit."""
    try:
        contract = _get_contract()
        fn = contract.functions.settleLoan(loan_id)
        receipt_info = _send_tx(fn)
        return {**receipt_info, "loan_id": loan_id, "new_status": "COMPLETED"}
    except Exception as e:
        return {"error": str(e)}


def get_loan_status(loan_id: int) -> dict:
    """Read loan state from chain (no gas cost)."""
    try:
        contract = _get_contract()
        loan = contract.functions.loans(loan_id).call()
        # (loanId, borrower, lender, equipmentId, quantity,
        #  startTime, expectedDuration, depositAmount, rentAmount, status)
        return {
            "loan_id":           loan[0],
            "borrower":          loan[1],
            "lender":            loan[2],
            "equipment_id":      loan[3],
            "quantity":          loan[4],
            "start_time":        loan[5],
            "expected_duration": loan[6],
            "deposit_amount_wei":loan[7],
            "rent_amount_wei":   loan[8],
            "status":            LOAN_STATUSES.get(loan[9], "UNKNOWN"),
        }
    except Exception as e:
        return {"error": str(e)}