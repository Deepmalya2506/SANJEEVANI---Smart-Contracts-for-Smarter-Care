import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const SanjeevaniModule = buildModule("SanjeevaniModule", (m) => {

  const sanjeevani = m.contract("SanjeevaniEscrow", []);

  return { sanjeevani };

});

export default SanjeevaniModule;
//0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9