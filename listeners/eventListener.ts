/* 
Blockchain
     ↓
Event Listener
     ↓
MCP Logic
     ↓
MongoDB
*/


import { ethers } from "ethers";
import fs from "fs";
import { CONTRACT_ADDRESS } from "../scripts/config.js";

async function main() {

  const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");

  const artifact = JSON.parse(
    fs.readFileSync(
      "./artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json",
      "utf8"
    )
  );

  const contract = new ethers.Contract(
    CONTRACT_ADDRESS,
    artifact.abi,
    provider
  );

  console.log("👂 Listening to blockchain events...");

  contract.on("LoanCreated", (loanId, borrower, lender, equipmentId, quantity) => {
    console.log("\n🚑 Loan Created Event");
    console.log("Loan ID:", loanId.toString());
    console.log("Borrower:", borrower);
    console.log("Lender:", lender);
    console.log("Equipment:", equipmentId.toString());
    console.log("Quantity:", quantity.toString());
  });

  contract.on("DeliveryConfirmed", (loanId, borrower, lender) => {
    console.log("\n📦 Delivery Confirmed");
    console.log("Loan ID:", loanId.toString());
  });

  contract.on("ReturnRequested", (loanId) => {
    console.log("\n🔁 Return Requested");
    console.log("Loan ID:", loanId.toString());
  });

  contract.on("LoanSettled", (loanId, rentPaid, depositReturned) => {
    console.log("\n💰 Loan Settled");
    console.log("Loan ID:", loanId.toString());
    console.log("Rent Paid:", rentPaid.toString());
    console.log("Deposit Returned:", depositReturned.toString());
  });

}

main();