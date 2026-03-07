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

    enum LoanStatus {
        REQUESTED,
        ACTIVE,
        RETURN_PENDING,
        COMPLETED,
        DISPUTE
    }

    struct Loan {
        uint256 loanId;
        address borrower;
        address lender;
        uint256 equipmentId;
        uint256 quantity;
        uint256 startTime;
        uint256 expectedDuration; // seconds
        uint256 depositAmount;
        uint256 rentAmount;
        LoanStatus status;
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

    event LoanCreated(
        uint256 loanId,
        address borrower,
        address lender,
        uint256 equipmentId,
        uint256 quantity,
        uint256 depositAmount
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

    function createLoanRequest(
        address _lender,
        uint256 _equipmentId,
        uint256 _quantity,
        uint256 _durationHours
    ) public payable {

        require(equipments[_equipmentId].exists, "Equipment not registered");
        require(_quantity > 0, "Invalid quantity");

        Equipment memory eq = equipments[_equipmentId];

        uint256 rent = eq.hourlyRate * _quantity * _durationHours;
        uint256 deposit = eq.cautionDeposit * _quantity;

        uint256 totalRequired = rent + deposit;

        require(msg.value == totalRequired, "Incorrect deposit amount");

        loanCounter++;

        loans[loanCounter] = Loan({
            loanId: loanCounter,
            borrower: msg.sender,
            lender: _lender,
            equipmentId: _equipmentId,
            quantity: _quantity,
            startTime: block.timestamp,
            expectedDuration: _durationHours * 1 hours,
            depositAmount: deposit,
            rentAmount: rent,
            status: LoanStatus.ACTIVE
        });

        emit LoanCreated(
            loanCounter,
            msg.sender,
            _lender,
            _equipmentId,
            _quantity,
            deposit
        );
    }
}