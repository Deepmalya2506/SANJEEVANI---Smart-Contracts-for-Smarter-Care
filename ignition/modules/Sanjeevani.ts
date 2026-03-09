import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const SanjeevaniModule = buildModule("SanjeevaniModule", (m) => {

  const sanjeevani = m.contract("SanjeevaniEscrow", []);

  return { sanjeevani };

});

export default SanjeevaniModule;
