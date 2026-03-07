import { ethers } from "ethers";
import fs from "fs";

async function main() {

  const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
  const signer = await provider.getSigner(0);

  const artifact = JSON.parse(
    fs.readFileSync("./artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json","utf8")
  );

  const contract = new ethers.Contract(
    "0x5FbDB2315678afecb367f032d93F642f64180aa3",
    artifact.abi,
    signer
  );

  const existing = await contract.equipments(1);

  if (!existing.exists) {
    await (await contract.registerEquipment("Oxygen Cylinder",500,2000)).wait();
    await (await contract.registerEquipment("Ventilator",2000,15000)).wait();
    await (await contract.registerEquipment("Defibrillator",1200,5000)).wait();
  }

  console.log(await contract.equipments(1));
  console.log(await contract.equipments(2));
  console.log(await contract.equipments(3));
}

main();