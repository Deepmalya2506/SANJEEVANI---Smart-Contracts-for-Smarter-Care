import { ethers } from "hardhat";

async function main() {

    const Sanjeevani = await ethers.getContractFactory("SanjeevaniEscrow");

    const contract = await Sanjeevani.deploy();

    await contract.deployed();

    console.log("Contract deployed to:", contract.address);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});