// SPDX-License-Identifier: MIT

pragma solidity ^0.8.28;

contract SanjeevaniEscrow {

    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // ============================================================
    // USER / HOSPITAL REGISTRATION
    // ============================================================

    mapping(address => bool) public registeredUsers;

    mapping(address => uint256) public equipmentCountByOwner;

    event UserRegistered(
        address indexed user
    );

    // ============================================================
    // EQUIPMENT
    // ============================================================

    struct Equipment {
        uint256 id;
        uint256 equipmentType;
        address owner;
        string name;
        uint256 hourlyRate;
        uint256 cautionDeposit;
        bool exists;
    }

    uint256 public equipmentCounter;

    mapping(uint256 => Equipment) public equipments;

    event EquipmentRegistered(
        uint256 id,
        uint256 equipmentType,
        string name,
        uint256 hourlyRate,
        uint256 cautionDeposit
    );

    // ============================================================
    // LOANS
    // ============================================================

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
        uint256 expectedDuration;
        uint256 depositAmount;
        uint256 rentAmount;
        LoanStatus status;
    }

    uint256 public loanCounter;

    mapping(uint256 => Loan) public loans;

    event LoanCreated(
        uint256 indexed loanId,
        address indexed borrower,
        address indexed lender,
        uint256 equipmentId,
        uint256 quantity,
        uint256 depositAmount
    );

    event DeliveryConfirmed(
        uint256 indexed loanId,
        address indexed borrower,
        address indexed lender
    );

    event ReturnRequested(
        uint256 indexed loanId
    );

    event LoanSettled(
        uint256 indexed loanId,
        uint256 rentPaid,
        uint256 depositReturned
    );

    // ============================================================
    // MODIFIERS
    // ============================================================

    modifier onlyRegisteredUser() {
        require(
            registeredUsers[msg.sender],
            "User not registered"
        );
        _;
    }

    modifier onlyRegisteredParticipant() {
        require(
            registeredUsers[msg.sender],
            "User not registered"
        );

        require(
            equipmentCountByOwner[msg.sender] > 0,
            "Register equipment first"
        );

        _;
    }

    // ============================================================
    // USER REGISTRATION
    // ============================================================

    function registerUser() public {

        require(
            !registeredUsers[msg.sender],
            "User already registered"
        );

        registeredUsers[msg.sender] = true;

        emit UserRegistered(msg.sender);
    }

    // ============================================================
    // EQUIPMENT REGISTRATION
    // ============================================================

    function registerEquipment(
        uint256 _equipmentType,
        string memory _name,
        uint256 _hourlyRate,
        uint256 _cautionDeposit
    ) public {

        require(
            registeredUsers[msg.sender],
            "Hospital not registered"
        );

        require(
            _equipmentType > 0,
            "Invalid equipment type"
        );

        equipmentCounter++;

        equipments[equipmentCounter] = Equipment({
            id: equipmentCounter,
            equipmentType: _equipmentType,
            owner: msg.sender,
            name: _name,
            hourlyRate: _hourlyRate,
            cautionDeposit: _cautionDeposit,
            exists: true
        });

        equipmentCountByOwner[msg.sender]++;

        emit EquipmentRegistered(
            equipmentCounter,
            _equipmentType,
            _name,
            _hourlyRate,
            _cautionDeposit
        );
    }

    // ============================================================
    // CREATE LOAN
    // ============================================================

    function createLoanRequest(
        address _lender,
        uint256 _equipmentId,
        uint256 _quantity,
        uint256 _durationHours
    )
        public
        payable
        onlyRegisteredParticipant
    {
        require(
            registeredUsers[msg.sender],
            "Borrower not registered"
        );

        require(
            registeredUsers[_lender],
            "Lender not registered"
        );

        require(
            equipments[_equipmentId].exists,
            "Equipment not registered"
        );

        require(
            _quantity > 0,
            "Invalid quantity"
        );

        Equipment memory eq = equipments[_equipmentId];

        require(
            eq.owner == _lender,
            "Lender does not own equipment"
        );

        require(
            _lender != msg.sender,
            "Cannot borrow from yourself"
        );

        uint256 rent =
            eq.hourlyRate *
            _quantity *
            _durationHours;

        uint256 deposit =
            eq.cautionDeposit *
            _quantity;

        uint256 totalRequired =
            rent +
            deposit;

        require(
            msg.value == totalRequired,
            "Incorrect deposit amount"
        );

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
            status: LoanStatus.REQUESTED
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

    // ============================================================
    // CONFIRM DELIVERY
    // ============================================================

    function confirmDelivery(
        uint256 _loanId
    )
        public
    {
        Loan storage loan = loans[_loanId];

        require(
            loan.loanId != 0,
            "Loan does not exist"
        );

        require(
            msg.sender == loan.borrower ||
            msg.sender == loan.lender,
            "Unauthorized"
        );

        require(
            loan.status == LoanStatus.REQUESTED,
            "Invalid state"
        );

        loan.status = LoanStatus.ACTIVE;

        emit DeliveryConfirmed(
            loan.loanId,
            loan.borrower,
            loan.lender
        );
    }

    // ============================================================
    // MARK RETURNED
    // ============================================================

    function markReturned(
        uint256 _loanId
    )
        public
    {
        Loan storage loan = loans[_loanId];

        require(
            loan.loanId != 0,
            "Loan not found"
        );

        require(
            msg.sender == loan.borrower,
            "Only borrower can return"
        );

        require(
            loan.status == LoanStatus.ACTIVE,
            "Loan not active"
        );

        loan.status = LoanStatus.RETURN_PENDING;

        emit ReturnRequested(_loanId);
    }

    // ============================================================
    // SETTLE LOAN
    // ============================================================

    function settleLoan(
        uint256 _loanId
    )
        public
    {
        Loan storage loan = loans[_loanId];

        require(
            loan.loanId != 0,
            "Loan not found"
        );

        require(
            msg.sender == loan.borrower ||
            msg.sender == loan.lender,
            "Unauthorized"
        );

        require(
            loan.status == LoanStatus.RETURN_PENDING,
            "Loan not ready for settlement"
        );

        uint256 totalDeposit =
            loan.depositAmount;

        uint256 rent =
            loan.rentAmount;

        address lender =
            loan.lender;

        address borrower =
            loan.borrower;

        // Pay rent to lender
        payable(lender).transfer(rent);

        // Return deposit to borrower
        payable(borrower).transfer(totalDeposit);

        loan.status =
            LoanStatus.COMPLETED;

        emit LoanSettled(
            _loanId,
            rent,
            totalDeposit
        );
    }
}

/*

registerEquipment()
        ↓
EquipmentRegistered

createLoanRequest()
        ↓
LoanCreated

confirmDelivery()
        ↓
DeliveryConfirmed

markReturned()
        ↓
ReturnRequested

settleLoan()
        ↓
LoanSettled

*/