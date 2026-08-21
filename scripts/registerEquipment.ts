import { ethers } from "ethers";
import { CONTRACT_ADDRESS } from "./config";
import fs from "fs";

async function main() {

    /*
        USAGE:

        npx ts-node scripts/registerEquipment.ts \
        WALLET_ADDRESS \
        EQUIPMENT_TYPE \
        "EQUIPMENT_NAME" \
        HOURLY_RATE \
        CAUTION_DEPOSIT

        Example:

        npx ts-node scripts/registerEquipment.ts \
        0x70997970C51812dc3A010C7d01b50e0d17dc79C8 \
        1 \
        "Oxygen Cylinder" \
        500 \
        2000
    */

    const args = process.argv.slice(2);

    if (args.length !== 5) {

        console.error(`
❌ Invalid arguments.

Usage:

npx ts-node scripts/registerEquipment.ts WALLET_ADDRESS EQUIPMENT_TYPE "NAME" HOURLY_RATE CAUTION_DEPOSIT

Example:

npx ts-node scripts/registerEquipment.ts 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 1 "Oxygen Cylinder" 500 2000
        `);

        process.exit(1);
    }

    const walletAddress = args[0];
    const equipmentType = Number(args[1]);
    const name = args[2];
    const hourlyRate = Number(args[3]);
    const cautionDeposit = Number(args[4]);

    // ------------------------------------------------------------
    // VALIDATION
    // ------------------------------------------------------------

    if (!ethers.utils.isAddress(walletAddress)) {
        console.error("❌ Invalid Ethereum wallet address.");
        process.exit(1);
    }

    if (!Number.isInteger(equipmentType) || equipmentType <= 0) {
        console.error("❌ Invalid equipment type.");
        process.exit(1);
    }

    if (!name || name.trim() === "") {
        console.error("❌ Equipment name cannot be empty.");
        process.exit(1);
    }

    if (!Number.isFinite(hourlyRate) || hourlyRate < 0) {
        console.error("❌ Invalid hourly rate.");
        process.exit(1);
    }

    if (
        !Number.isFinite(cautionDeposit) ||
        cautionDeposit < 0
    ) {
        console.error("❌ Invalid caution deposit.");
        process.exit(1);
    }

    // ------------------------------------------------------------
    // CONNECT TO GANACHE
    // ------------------------------------------------------------

    const provider =
        new ethers.providers.JsonRpcProvider(
            "http://127.0.0.1:7545"
        );

    const checksumAddress =
        ethers.utils.getAddress(walletAddress);

    const signer =
        provider.getSigner(checksumAddress);

    // Confirm that Ganache actually controls this address.
    const accounts =
        await provider.listAccounts();

    const normalizedAccounts =
        accounts.map((address) =>
            address.toLowerCase()
        );

    if (
        !normalizedAccounts.includes(
            checksumAddress.toLowerCase()
        )
    ) {
        console.error(
            "\n❌ This wallet is not controlled by the current Ganache instance."
        );

        console.error(
            "Wallet:",
            checksumAddress
        );

        console.error(
            "\nAvailable Ganache accounts:"
        );

        accounts.forEach((account, index) => {
            console.error(
                `${index}: ${account}`
            );
        });

        process.exit(1);
    }

    console.log("\n======================================");
    console.log(" SANJEEVANI EQUIPMENT REGISTRATION");
    console.log("======================================");

    console.log(
        "Hospital wallet:",
        checksumAddress
    );

    console.log(
        "Equipment type:",
        equipmentType
    );

    console.log(
        "Equipment:",
        name
    );

    console.log(
        "Hourly rate:",
        hourlyRate
    );

    console.log(
        "Caution deposit:",
        cautionDeposit
    );

    console.log(
        "Contract:",
        CONTRACT_ADDRESS
    );

    // ------------------------------------------------------------
    // LOAD CONTRACT
    // ------------------------------------------------------------

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
            signer
        );

    // ------------------------------------------------------------
    // HOSPITAL REGISTRATION
    // ------------------------------------------------------------

    const alreadyRegistered =
        await contract.registeredUsers(
            checksumAddress
        );

    if (!alreadyRegistered) {

        console.log(
            "\n🏥 Hospital is not registered."
        );

        console.log(
            "Registering hospital..."
        );

        const tx =
            await contract.registerUser();

        console.log(
            "Registration TX:",
            tx.hash
        );

        await tx.wait();

        console.log(
            "✅ Hospital registered."
        );

    } else {

        console.log(
            "\n✅ Hospital already registered."
        );
    }

    // ------------------------------------------------------------
    // EQUIPMENT REGISTRATION
    // ------------------------------------------------------------

    console.log(
        "\n📦 Registering equipment..."
    );

    const tx =
        await contract.registerEquipment(
            equipmentType,
            name,
            hourlyRate,
            cautionDeposit
        );

    console.log(
        "Transaction:",
        tx.hash
    );

    const receipt =
        await tx.wait();

    console.log(
        "✅ Equipment registered."
    );

    console.log(
        "Block:",
        receipt.blockNumber
    );

    // ------------------------------------------------------------
    // RESULT
    // ------------------------------------------------------------

    const count =
        await contract.equipmentCountByOwner(
            checksumAddress
        );

    console.log(
        "\nEquipment registered by hospital:",
        count.toString()
    );

    console.log(
        "\n======================================"
    );

    console.log(
        "Registration successful."
    );

    console.log(
        "======================================\n"
    );
}

main().catch((error) => {

    console.error(
        "\n❌ Registration failed:\n"
    );

    console.error(error);

    process.exit(1);
});