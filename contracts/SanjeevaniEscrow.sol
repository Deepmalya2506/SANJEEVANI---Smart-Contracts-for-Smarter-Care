// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract SanjeevaniEscrow {

    address public owner;

    constructor() {
        owner = msg.sender;
    }

    struct Equipment {
        uint256 id;
        string name;
        uint256 hourlyRate;
        uint256 cautionDeposit;
        bool exists;
    }

    struct Loan {
        uint256 loanId;
        address borrower;
        address lender;
        uint256 equipmentId;
        uint256 quantity;
        uint256 startTime;
        uint256 expectedDuration;
        uint256 depositAmount;
        bool active;
    }

    uint256 public equipmentCounter;
    uint256 public loanCounter;

    mapping(uint256 => Equipment) public equipments;
    mapping(uint256 => Loan) public loans;

    event EquipmentRegistered(
        uint256 id,
        string name,
        uint256 hourlyRate,
        uint256 cautionDeposit
    );

    function registerEquipment(
        string memory _name,
        uint256 _hourlyRate,
        uint256 _cautionDeposit
    ) public {

        equipmentCounter++;

        equipments[equipmentCounter] = Equipment({
            id: equipmentCounter,
            name: _name,
            hourlyRate: _hourlyRate,
            cautionDeposit: _cautionDeposit,
            exists: true
        });

        emit EquipmentRegistered(
            equipmentCounter,
            _name,
            _hourlyRate,
            _cautionDeposit
        );
    }
}