// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract SanjeevaniEscrow {

    struct Equipment {
        uint256 id;
        string name;
        uint256 hourlyRate;
        uint256 cautionDeposit;
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

    uint256 public loanCounter;

    mapping(uint256 => Equipment) public equipments;
    mapping(uint256 => Loan) public loans;

}