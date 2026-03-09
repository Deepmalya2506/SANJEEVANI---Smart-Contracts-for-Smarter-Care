import { ethers } from "ethers";
import fs from "fs";

async function main() {

  const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");

  const borrower = await provider.getSigner(0);
  const lender = await provider.getSigner(1);

  const borrowerAddr = await borrower.getAddress();
  const lenderAddr = await lender.getAddress();

  const artifact = JSON.parse(
    fs.readFileSync("./artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json","utf8")
  );

  const contract = new ethers.Contract(
    "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9",
    artifact.abi,
    borrower
  );

  const equipmentId = 1;
  const quantity = 2;
  const hours = 4;

  const hourlyRate = 500;
  const caution = 2000;

  const rent = hourlyRate * quantity * hours;
  const deposit = caution * quantity;

  const total = rent + deposit;

  const tx = await contract.createLoanRequest(
    lenderAddr,
    equipmentId,
    quantity,
    hours,
    { value: total }
  );

  await tx.wait();

  console.log("Loan created");

  const loanId = await contract.loanCounter();
  const loan = await contract.loans(loanId);

  console.log("Loan ID:", loanId);
  
  console.log("Loan Data:", loan);

  const balance = await provider.getBalance(contract.target);
  console.log("Escrow Balance:", balance.toString());

}

main();