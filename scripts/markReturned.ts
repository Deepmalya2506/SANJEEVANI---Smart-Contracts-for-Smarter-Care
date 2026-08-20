import { ethers } from "ethers";
import { CONTRACT_ADDRESS } from "./config";
import fs from "fs";

async function main() {

  const provider = new ethers.providers.JsonRpcProvider("http://127.0.0.1:7545");
  const signer = await provider.getSigner(0);

  const artifact = JSON.parse(
    fs.readFileSync("./artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json","utf8")
  );

  const contract = new ethers.Contract(
    CONTRACT_ADDRESS,
    artifact.abi,
    signer
  );

  const tx = await contract.markReturned(1);

  await tx.wait();

  const loan = await contract.loans(1);

  console.log("Loan Status:", loan.status);
}

main();