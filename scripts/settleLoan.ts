import { ethers } from "ethers";
import fs from "fs";
import { CONTRACT_ADDRESS } from "./config.js";

async function main() {

  const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
  const signer = await provider.getSigner(0);

  const artifact = JSON.parse(
    fs.readFileSync("./artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json","utf8")
  );

  const contract = new ethers.Contract(
    CONTRACT_ADDRESS,
    artifact.abi,
    signer
  );

  const tx = await contract.settleLoan(1);

  await tx.wait();

  const loan = await contract.loans(1);

  console.log("Loan Status:", loan.status);

  const balance = await provider.getBalance(CONTRACT_ADDRESS);
  console.log("Escrow Balance:", balance.toString());
}

main();