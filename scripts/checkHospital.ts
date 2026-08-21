import { ethers } from "ethers";
import { CONTRACT_ADDRESS } from "./config";
import fs from "fs";

async function main() {

    const args = process.argv.slice(2);

    if (args.length !== 1) {
        console.error(`
Usage:

npx ts-node scripts/checkHospital.ts WALLET_ADDRESS

Example:

npx ts-node scripts/checkHospital.ts 0xdb4Ec4C3312388a6EF551ef7876371F6277C1405
        `);

        process.exit(1);
    }

    const wallet =
        ethers.utils.getAddress(args[0]);

    const provider =
        new ethers.providers.JsonRpcProvider(
            "http://127.0.0.1:7545"
        );

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
            provider
        );

    console.log(
        "\n======================================"
    );

    console.log(
        " SANJEEVANI HOSPITAL CHECK"
    );

    console.log(
        "======================================"
    );

    console.log(
        "Hospital wallet:",
        wallet
    );

    // ------------------------------------------------------------
    // CHECK REGISTRATION
    // ------------------------------------------------------------

    const registered =
        await contract.registeredUsers(wallet);

    console.log(
        "Registered:",
        registered
    );

    if (!registered) {

        console.log(
            "\n❌ Hospital is not registered."
        );

        return;
    }

    // ------------------------------------------------------------
    // GET GLOBAL EQUIPMENT COUNT
    // ------------------------------------------------------------

    const totalEquipment =
        await contract.equipmentCounter();

    let ownedCount = 0;

    console.log(
        "\nEquipment owned by this hospital:"
    );

    // ------------------------------------------------------------
    // FIND EQUIPMENT OWNED BY THIS HOSPITAL
    // ------------------------------------------------------------

    for (
        let i = 1;
        i <= totalEquipment.toNumber();
        i++
    ) {

        const equipment =
            await contract.equipments(i);

        if (
            equipment.owner.toLowerCase() !==
            wallet.toLowerCase()
        ) {
            continue;
        }

        ownedCount++;

        console.log(
            `\nEquipment #${i}`
        );

        console.log(
            "Owner:",
            equipment.owner
        );

        console.log(
            "Name:",
            equipment.name
        );

        console.log(
            "Hourly rate:",
            equipment.hourlyRate.toString()
        );

        console.log(
            "Caution deposit:",
            equipment.cautionDeposit.toString()
        );

        console.log(
            "Exists:",
            equipment.exists
        );
    }

    console.log(
        "\nTotal equipment owned:",
        ownedCount
    );

    console.log(
        "\n======================================\n"
    );
}

main().catch((error) => {

    console.error(
        "\n❌ Failed to check hospital:"
    );

    console.error(error);

    process.exit(1);
});