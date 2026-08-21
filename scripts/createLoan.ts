import { ethers } from "ethers";
import { CONTRACT_ADDRESS } from "./config";
import fs from "fs";

async function main() {

    /*
        Usage:

        npx ts-node scripts/createLoan.ts \
        BORROWER_ADDRESS \
        LENDER_ADDRESS \
        EQUIPMENT_ID \
        QUANTITY \
        DURATION_HOURS
    */

    const args = process.argv.slice(2);

    if (args.length !== 5) {
        console.error(`
Usage:

npx ts-node scripts/createLoan.ts BORROWER_ADDRESS LENDER_ADDRESS EQUIPMENT_ID QUANTITY DURATION_HOURS

Example:

npx ts-node scripts/createLoan.ts 0xBORROWER 0xLENDER 1 1 48
        `);

        process.exit(1);
    }

    const borrowerAddress = ethers.utils.getAddress(args[0]);
    const lenderAddress = ethers.utils.getAddress(args[1]);

    const equipmentId = Number(args[2]);
    const quantity = Number(args[3]);
    const durationHours = Number(args[4]);

    if (equipmentId <= 0 || quantity <= 0 || durationHours <= 0) {
        throw new Error(
            "Equipment ID, quantity and duration must be greater than zero."
        );
    }

    const provider =
        new ethers.providers.JsonRpcProvider(
            "http://127.0.0.1:7545"
        );

    const accounts = await provider.listAccounts();

    const normalizedAccounts =
        accounts.map((a) => a.toLowerCase());

    if (!normalizedAccounts.includes(
        borrowerAddress.toLowerCase()
    )) {
        throw new Error(
            "Borrower address is not controlled by Ganache."
        );
    }

    if (!normalizedAccounts.includes(
        lenderAddress.toLowerCase()
    )) {
        throw new Error(
            "Lender address is not controlled by Ganache."
        );
    }

    const borrowerSigner =
        provider.getSigner(borrowerAddress);

    const artifact = JSON.parse(
        fs.readFileSync(
            "./artifacts/contracts/SanjeevaniEscrow.sol/SanjeevaniEscrow.json",
            "utf8"
        )
    );

    const contract =
        new ethers.Contract(
            CONTRACT_ADDRESS,
            artifact.abi,
            borrowerSigner
        );

    console.log("\n======================================");
    console.log(" SANJEEVANI LOAN REQUEST");
    console.log("======================================");

    console.log("Borrower:", borrowerAddress);
    console.log("Lender:", lenderAddress);
    console.log("Equipment ID:", equipmentId);
    console.log("Quantity:", quantity);
    console.log("Duration:", `${durationHours} hours`);

    // ------------------------------------------------------------
    // CHECK EQUIPMENT
    // ------------------------------------------------------------

    const equipment =
        await contract.equipments(equipmentId);

    if (!equipment.exists) {
        throw new Error(
            "Equipment does not exist."
        );
    }

    console.log("\nEquipment:");
    console.log("Owner:", equipment.owner);
    console.log("Name:", equipment.name);
    console.log(
        "Hourly rate:",
        equipment.hourlyRate.toString()
    );
    console.log(
        "Caution deposit:",
        equipment.cautionDeposit.toString()
    );

    // ------------------------------------------------------------
    // CALCULATE PAYMENT
    // ------------------------------------------------------------

    const rent =
        equipment.hourlyRate
            .mul(quantity)
            .mul(durationHours);

    const deposit =
        equipment.cautionDeposit
            .mul(quantity);

    const total =
        rent.add(deposit);

    console.log("\nFinancials:");
    console.log("Rent:", rent.toString());
    console.log("Deposit:", deposit.toString());
    console.log("Total:", total.toString());

    // ------------------------------------------------------------
    // CREATE LOAN
    // ------------------------------------------------------------

    console.log("\nCreating loan...");

    const tx =
        await contract.createLoanRequest(
            lenderAddress,
            equipmentId,
            quantity,
            durationHours,
            {
                value: total
            }
        );

    console.log(
        "Transaction:",
        tx.hash
    );

    const receipt =
        await tx.wait();

    console.log(
        "Block:",
        receipt.blockNumber
    );

    console.log(
        "\n✅ Loan request created successfully."
    );

    console.log(
        "======================================\n"
    );
}

main().catch((error) => {

    console.error(
        "\n❌ Loan request failed."
    );

    if (error.reason) {
        console.error(
            "Reason:",
            error.reason
        );
    } else {
        console.error(error.message);
    }

    process.exit(1);
});