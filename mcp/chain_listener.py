from web3 import Web3
import json
import asyncio
from mcp.inventory_service import reserve_equipment


RPC = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(RPC))

contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

with open("artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json") as f:
    contract_json = json.load(f)

abi = contract_json["abi"]

contract = w3.eth.contract(address=contract_address, abi=abi) #type: ignore


def handle_event(event):

    args = event["args"]

    loan_id = args["loanId"]
    lender = args["lender"]
    equipment_id = args["equipmentId"]
    quantity = args["quantity"]

    print("🚑 LoanCreated detected")
    print(loan_id, lender, equipment_id, quantity)

    # call inventory service
    asyncio.run(reserve_equipment(lender, equipment_id, quantity))


def listen():

    event_filter = contract.events.LoanCreated.create_filter(from_block="latest")

    while True:

        for event in event_filter.get_new_entries():

            handle_event(event)