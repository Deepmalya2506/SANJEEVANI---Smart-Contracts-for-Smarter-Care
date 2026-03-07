import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const SanjeevaniModule = buildModule("SanjeevaniModule", (m) => {

  const sanjeevani = m.contract("SanjeevaniEscrow", []);

  return { sanjeevani };

});

export default SanjeevaniModule;
//0x5FbDB2315678afecb367f032d93F642f64180aa3