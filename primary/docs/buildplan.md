# SANJEEVANI — Revised MVP Build Plan

<img src= "./landing_pg.jpeg" width=100%/>

<div align="center">

<h1 style="font-size: 40px;">S A N J E E V A N I</h1>  

<i>We care when even seconds count.</i>

</div>

**Status:** Canonical MVP architecture

**Purpose:** End-to-end implementation blueprint

**Scope:** Single-organization-admin MVP with real Supabase, GIS, blockchain and Razorpay integration

**Architecture principle:** Keep the system small, deterministic, secure and demonstrable. Build only what contributes directly to the hospital-to-hospital resource-sharing workflow.

---

# 1. Executive Definition

SANJEEVANI is a B2B SaaS platform with a Modular-Monolith architecture that connects participating hospitals into a trusted resource-sharing network.

It enables a hospital to:

1. establish verified facility identity,
2. register its available medical equipment,
3. discover equipment available at other participating hospitals,
4. ask the MCP assistant for the best feasible option,
5. evaluate geographic feasibility using PostGIS + H3 + OSRM + traffic masking,
6. approve a proposed resource exchange,
7. reserve the equipment transactionally,
8. commit important contractual state to a smart contract,
9. initiate real INR payment through Razorpay/UPI,
10. receive payment/blockchain confirmations,
11. track dispatch, delivery, activation, return and settlement,
12. receive email notifications for major transaction events,
13. view the complete transaction history.

The product is **not** a blockchain application with a hospital UI attached to it.

Blockchain is one trust layer inside a larger resource-exchange system.

---

# 2. Core Product Proposition

Existing hospital systems generally answer:

> What equipment does this hospital own?

SANJEEVANI attempts to answer:

> Which participating hospital can provide the required equipment, is it currently available, can it reach the requesting hospital within the required time, what are the transaction terms, and can the exchange be executed and audited safely?

The central workflow is:

```text
NEED
  ↓
DISCOVER
  ↓
VERIFY
  ↓
GEO-FEASIBILITY
  ↓
RANK
  ↓
PROPOSE
  ↓
USER APPROVAL
  ↓
RESERVE
  ↓
BLOCKCHAIN COMMITMENT
  ↓
PAYMENT
  ↓
CONFIRM
  ↓
DISPATCH
  ↓
DELIVERY
  ↓
ACTIVE
  ↓
RETURN
  ↓
SETTLEMENT
  ↓
ASSET AVAILABLE
```

---

# 3. MVP Scope

## 3.1 Included

The MVP includes:

* Supabase Authentication
* Supabase PostgreSQL
* PostGIS
* single hospital organization per registered account
* one active hospital administrator/user
* one primary wallet address per hospital
* one registered UPI/payment configuration per hospital
* hospital directory
* facility verification against the seeded directory
* equipment registration
* equipment availability
* marketplace discovery
* MCP assistant
* H3 candidate pruning
* OSRM road routing
* traffic-aware segmentation/masking through a pluggable traffic layer
* reservation system
* loan lifecycle
* smart-contract state guards
* blockchain event listeners
* Razorpay payment integration
* payment webhooks/reconciliation
* email notifications
* realtime transaction updates
* activity/audit timeline
* dispatch/delivery/return lifecycle
* dashboard
* monitoring
* idempotency and retry handling

---

# 4. Explicitly Removed from MVP

The following are deliberately excluded.

## Removed: complex RBAC

No:

```text
Manager
Finance Auditor
Operations Manager
Compliance Officer
Super Admin
```

MVP:

```text
Hospital
   └── Hospital Administrator / User
```

The database should remain capable of evolving toward multiple users later.

---

## Removed: full compliance microservice

Do not build an artificial compliance ecosystem with:

* BMMP attestation
* calibration authority
* complex regulatory signatures
* government API simulation

MVP only maintains:

```text
facility_verified
equipment information
equipment operational status
basic eligibility checks
```

Future compliance integrations can be added without redesigning the transaction model.

---

## Removed: Haversine as routing

Haversine may exist only as an optional low-level geometric utility if needed.

It is **not** the route engine.

The primary GIS path is:

```text
PostGIS
   ↓
H3
   ↓
candidate pruning
   ↓
OSRM
   ↓
baseline road ETA
   ↓
traffic segmentation/masking
   ↓
feasibility
```

---

## Removed: mock payment provider

The MVP uses real Razorpay integration.

There is no fake:

```text
payment_success = true
```

implementation.

Test mode may use Razorpay's supported test/sandbox mechanisms, but the application architecture must model the real payment lifecycle.

---

## Removed: crypto payments

INR payment is completely separate from blockchain.

```text
Blockchain
    =
contractual trust/state

Razorpay
    =
INR payment execution
```

---

## Removed: patient information

SANJEEVANI does not manage patient records.

No patient:

* name
* medical record
* diagnosis
* prescription
* clinical history

is required for the MVP.

---

# 5. System Boundaries

Each major system has exactly one primary responsibility.

| Component           | Responsibility                                    |
| ------------------- | ------------------------------------------------- |
| Supabase Auth       | Identity and sessions                             |
| Supabase PostgreSQL | Operational source of truth                       |
| PostGIS             | Spatial storage/query                             |
| H3                  | Geographic candidate pruning                      |
| OSRM                | Road-network routing                              |
| Traffic layer       | Current route feasibility adjustment/masking      |
| Backend             | Business rules and transactional workflow         |
| MCP                 | Natural-language orchestration and tool selection |
| Smart Contract      | Guarded contractual state transitions             |
| Blockchain listener | Detect and reconcile on-chain events              |
| Razorpay            | INR payment execution                             |
| Webhook handler     | Receive external payment state                    |
| Email service       | Transactional notifications                       |
| Realtime stream     | Frontend state updates                            |
| Frontend            | User interaction                                  |

---

# 6. High-Level Architecture

```text
                           ┌─────────────────────┐
                           │       USER          │
                           │ Hospital Admin      │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │      FRONTEND       │
                           │ React + TypeScript  │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │   SUPABASE AUTH      │
                           │ Session / JWT        │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │   SANJEEVANI API    │
                           │   FastAPI Backend   │
                           └──────────┬──────────┘
                                      │
             ┌────────────────────────┼─────────────────────────┐
             │                        │                         │
             ▼                        ▼                         ▼
      ┌─────────────┐          ┌─────────────┐          ┌──────────────┐
      │  Supabase   │          │     MCP     │          │ Notification │
      │ PostgreSQL  │          │ Orchestrator│          │ Email        │
      │ + PostGIS   │          └──────┬──────┘          └──────────────┘
      └──────┬──────┘                 │
             │                ┌───────┼────────┐
             │                │       │        │
             │                ▼       ▼        ▼
             │              Inventory GIS    Loan/Txn
             │                       │
             │                       ▼
             │              ┌────────────────┐
             │              │ H3 Candidate   │
             │              │ Pruning        │
             │              └───────┬────────┘
             │                      ▼
             │              ┌────────────────┐
             │              │ OSRM Routing   │
             │              └───────┬────────┘
             │                      ▼
             │              ┌────────────────┐
             │              │ Traffic Mask   │
             │              └───────┬────────┘
             │                      ▼
             │                  Feasibility
             │
             ├─────────────────────────────┐
             │                             │
             ▼                             ▼
      ┌───────────────┐             ┌───────────────┐
      │ Smart Contract│             │   Razorpay    │
      │ EVM Network   │             │ UPI Payment   │
      └───────┬───────┘             └───────┬───────┘
              │                             │
              ▼                             ▼
      Blockchain Events              Payment Webhooks
              │                             │
              └──────────────┬──────────────┘
                             ▼
                      Transaction Reconcile
                             │
                             ▼
                       Supabase State
                             │
                             ▼
                      Realtime Frontend
```

---

# 7. System of Record

This distinction is mandatory.

## Supabase PostgreSQL

```text
Operational truth
```

Contains:

* organizations
* users/profile mapping
* assets
* availability
* reservations
* loans
* payments
* dispatch
* delivery
* returns
* activity
* notifications
* integration references

---

## Blockchain

```text
Contractual / immutable transaction truth
```

Contains only compact transaction commitments and state.

---

## Razorpay

```text
Payment execution truth
```

SANJEEVANI stores references to payment objects and their reconciled state.

---

## GIS

```text
Spatial computation
```

GIS calculations do not become the business database.

---

## MCP

```text
Orchestration
```

MCP does not become the database or authority.

---

# 8. Hospital Directory Data Strategy

The collected government/public hospital dataset is suitable as a **facility-directory seed**, not as SANJEEVANI's live inventory.

The dataset contains useful fields including:

```text
Hospital_Name
Address_Original_First_Line
Location
State
District
Pincode
Location_Coordinates
Hospital_Care_Type
Discipline_Systems_of_Medicine
Emergency_Services
Specialties
Facilities
Total_Num_Beds
...
```

The sample also contains many placeholder values such as:

```text
0
0.0
NaN
```

and includes records that may not represent normal hospitals.

Therefore:

```text
RAW DATA
   ↓
NORMALIZATION
   ↓
RECORD CLASSIFICATION
   ↓
DUPLICATE DETECTION
   ↓
COORDINATE VALIDATION
   ↓
STATE/DISTRICT NORMALIZATION
   ↓
QUALITY FLAGGING
   ↓
PROCESSED DIRECTORY
   ↓
SUPABASE
```

---

# 9. Facility Directory Schema

Create:

```text
facility_directory
```

Recommended fields:

```text
id UUID PRIMARY KEY
source_record_id TEXT
hospital_name TEXT
address TEXT
location_text TEXT
state TEXT
district TEXT
pincode TEXT
latitude DOUBLE PRECISION
longitude DOUBLE PRECISION
geom GEOGRAPHY(Point, 4326)
hospital_care_type TEXT
discipline TEXT
emergency_services BOOLEAN / nullable
specialties TEXT / JSONB
facilities TEXT / JSONB
total_beds INTEGER / nullable
source TEXT
data_quality_status TEXT
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Do not overload this table with live SANJEEVANI information.

---

# 10. SANJEEVANI Hospital Organization

Separate:

```text
facility_directory
```

from:

```text
organizations
```

Relationship:

```text
facility_directory
        │
        │ verified directory identity
        ▼
organizations
        │
        ├── admin profile
        ├── wallet
        ├── UPI configuration
        ├── assets
        ├── reservations
        └── loans
```

Recommended:

```text
organizations
-------------------------
id UUID PK
facility_directory_id UUID FK
hospital_name TEXT
abdm_id TEXT UNIQUE
verification_status TEXT
wallet_address TEXT UNIQUE
profile_status TEXT
created_at
updated_at
```

The `abdm_id` is the SANJEEVANI facility identity reference.

---

# 11. Signup Workflow

```text
USER
 │
 ▼
Hospital Name + ABDM/HFR ID
 │
 ▼
facility_directory lookup
 │
 ├── NOT FOUND
 │      ↓
 │    REJECT
 │
 └── FOUND
       ↓
organizations lookup
       │
       ├── EXISTS
       │     ↓
       │  "Hospital already has
       │   a SANJEEVANI account."
       │
       └── NOT EXISTS
             ↓
       Create organization
             ↓
       Create Supabase Auth user
             ↓
       Session
             ↓
       Email verification
             ↓
       Profile setup
             ↓
       ACTIVE
```

The frontend must never decide whether a hospital is verified.

The backend performs the check.

---

# 12. Profile Completion Gate

After registration:

```text
ACCOUNT_CREATED
       ↓
EMAIL_VERIFICATION
       ↓
PROFILE_INCOMPLETE
       ↓
PROFILE_COMPLETED
       ↓
ACTIVE
```

Required profile data:

```text
name
date_of_birth
hospital identity proof
email
wallet address
UPI/payment configuration
```

The exact identity-proof storage mechanism should use secure object storage/reference rather than putting sensitive documents directly into normal database columns.

Transaction functionality remains locked until required profile setup is complete.

---

# 13. Authentication

Use:

```text
Supabase Auth
```

for:

* signup
* login
* logout
* session
* refresh
* email verification
* password recovery

Application authorization is derived from:

```text
JWT
 ↓
authenticated user
 ↓
organization mapping
 ↓
organization_id
```

The user does not submit:

```text
organization_id = "Hospital B"
```

and expect the backend to trust it.

---

# 14. Session Model

Frontend:

```text
Supabase session
        ↓
access token
        ↓
API request
```

Backend:

```text
JWT validation
      ↓
user_id
      ↓
organization lookup
      ↓
authorized request
```

Session expiry, refresh and logout are handled through Supabase Auth.

---

# 15. ERD

<img src= ".\ERD.png" />

---

# 16. Core Database Entities

## `organizations`

Represents a SANJEEVANI hospital.

---

## `profiles`

Represents the current hospital administrator/user profile.

---

## `facility_directory`

External/seeded facility identity.

---

## `equipment_types`

Canonical equipment categories.

Examples:

```text
Ventilator
Oxygen Concentrator
Patient Monitor
Infusion Pump
ECG Machine
```

---

## `assets`

A hospital-owned/shareable equipment unit.

Important:

```text
organization_id
equipment_type_id
asset_identifier
status
condition
shareable
daily_rate
deposit_amount
location
```

---

## `reservations`

Temporary inventory lock.

---

## `loans`

The business transaction generated from an approved reservation.

---

## `payments`

Razorpay transaction references and reconciled payment state.

---

## `blockchain_transactions`

On-chain transaction references.

---

## `dispatches`

Equipment movement state.

---

## `returns`

Return lifecycle.

---

## `activity_events`

Human-readable transaction timeline.

---

## `notification_events`

Email/realtime notification tracking.

---

# 17. Asset State Machine

```text
AVAILABLE
    │
    ▼
RESERVED
    │
    ├── reservation expires ──► AVAILABLE
    │
    ▼
LOAN_ACTIVE
    │
    ▼
DISPATCHED
    │
    ▼
DELIVERED
    │
    ▼
IN_USE
    │
    ▼
RETURN_PENDING
    │
    ▼
RETURNED
    │
    ▼
AVAILABLE
```

Maintenance state may branch independently:

```text
AVAILABLE
    ↓
MAINTENANCE
    ↓
AVAILABLE
```

An asset cannot be simultaneously:

```text
AVAILABLE
+
RESERVED
```

---

# 18. Reservation State Machine

```text
PENDING
   │
   ├── rejected/cancelled
   ▼
CANCELLED

PENDING
   │
   ▼
RESERVED
   │
   ├── timeout
   ▼
EXPIRED

RESERVED
   │
   ▼
CONVERTED_TO_LOAN
```

Reservation expiry is enforced server-side.

A scheduled worker must periodically identify expired reservations and release assets.

---

# 19. Loan State Machine

```text
PROPOSED
   │
   ▼
APPROVED
   │
   ▼
RESERVED
   │
   ▼
BLOCKCHAIN_PENDING
   │
   ├── failed ──► BLOCKCHAIN_FAILED
   │
   ▼
BLOCKCHAIN_CONFIRMED
   │
   ▼
PAYMENT_PENDING
   │
   ├── failed ──► PAYMENT_FAILED
   │
   ▼
CONFIRMED
   │
   ▼
DISPATCHED
   │
   ▼
DELIVERED
   │
   ▼
ACTIVE
   │
   ▼
RETURN_REQUESTED
   │
   ▼
RETURNED
   │
   ▼
SETTLEMENT_PENDING
   │
   ▼
SETTLED
```

Every transition must be validated.

No arbitrary:

```text
PATCH /loans/{id}
```

should allow the frontend to set:

```text
status = SETTLED
```

---

# 20. Endpoint Design

All APIs use:

```text
/api/v1
```

Every protected endpoint requires authentication.

---

# 21. AUTH SERVICE

### `POST /api/v1/auth/signup`

**Purpose:** Begin hospital registration.

**Arguments:**

```text
hospital_name
abdm_id
email
password
```

**Returns:**

```text
organization_id
user_id
profile_status
email_verification_required
```

---

### `GET /api/v1/auth/me`

Returns:

```text
user_id
organization_id
email
profile_status
session_status
```

---

### `POST /api/v1/auth/logout`

Terminates application session.

---

### `POST /api/v1/auth/resend-verification`

Resends verification email.

---

### `POST /api/v1/auth/forgot-password`

Starts password recovery.

---

# 22. ORGANIZATION / PROFILE SERVICE

### `GET /api/v1/organizations/me`

Returns:

```text
organization
facility identity
verification status
profile status
wallet
payment configuration status
```

---

### `PATCH /api/v1/organizations/me`

Updates editable hospital profile fields.

---

### `POST /api/v1/organizations/me/complete-profile`

Finalizes profile prerequisites.

---

### `POST /api/v1/organizations/me/wallet`

Registers/updates wallet address.

Validation:

```text
valid address
not already owned by another organization
```

---

### `POST /api/v1/organizations/me/payment-account`

Registers the hospital's supported Razorpay/payment configuration.

Sensitive credentials must never be returned to the frontend.

---

# 23. FACILITY DIRECTORY SERVICE

### `GET /api/v1/facilities/search`

Arguments:

```text
query
state?
district?
limit?
```

Returns:

```text
facility_id
hospital_name
address
state
district
pincode
latitude
longitude
verification/quality status
```

---

### `GET /api/v1/facilities/{facility_id}`

Returns public facility information.

---

### `POST /api/v1/facilities/verify-signup`

Internal signup verification operation.

Returns:

```text
exists
facility_id
canonical_name
abdm_id_match
```

---

# 24. EQUIPMENT SERVICE

### `POST /api/v1/equipment/types`

Creates a canonical equipment type.

---

### `GET /api/v1/equipment/types`

Returns equipment categories.

---

### `POST /api/v1/equipment/assets`

Registers a hospital-owned asset.

Arguments:

```text
equipment_type_id
asset_identifier
condition
shareable
daily_rate
deposit_amount
description
```

Returns:

```text
asset_id
status
created_at
```

---

### `GET /api/v1/equipment/assets`

Returns assets belonging to authenticated organization.

---

### `GET /api/v1/equipment/assets/{asset_id}`

Returns asset details subject to authorization.

---

### `PATCH /api/v1/equipment/assets/{asset_id}`

Updates allowed asset metadata.

---

### `POST /api/v1/equipment/assets/{asset_id}/availability`

Changes operational availability through a validated command.

---

# 25. MARKETPLACE SERVICE

### `GET /api/v1/marketplace`

Arguments:

```text
equipment_type
location?
available_from?
available_until?
max_price?
```

Returns:

```text
asset_id
equipment_type
lender_hospital
availability
price
deposit
location
verification
```

No private hospital information is exposed.

---

### `GET /api/v1/marketplace/{asset_id}`

Returns the public listing.

---

# 26. GIS SERVICE

The GIS service has three logical stages.

```text
1. Candidate pruning
2. Road routing
3. Traffic feasibility
```

---

## `POST /api/v1/gis/candidates`

Arguments:

```text
origin_lat
origin_lon
equipment_type_id
max_eta_minutes?
search_h3_resolution?
```

Returns:

```text
candidate hospitals
candidate assets
H3 cell
approximate spatial relation
```

---

## `POST /api/v1/gis/routes`

Arguments:

```text
origin
destination[]
profile
```

Returns:

```text
distance_km
duration_seconds
geometry
route_provider
```

---

## `POST /api/v1/gis/feasibility`

Arguments:

```text
origin
candidate_ids
max_eta_minutes
traffic_mode
```

Returns:

```text
candidate_id
baseline_eta
traffic_adjusted_eta
distance
route_status
traffic_status
feasible
route_geometry
```

---

## `POST /api/v1/gis/best-options`

Returns ranked feasible equipment sources.

```text
candidate
asset
eta
distance
availability
price
traffic_status
feasibility_score
```

---

# 27. GIS Pipeline

```text
Request
   │
   ▼
PostGIS spatial query
   │
   ▼
H3 candidate pruning
   │
   ▼
Candidate hospitals
   │
   ▼
OSRM road routing
   │
   ▼
Baseline distance + ETA
   │
   ▼
Traffic segmentation/masking
   │
   ▼
Traffic-adjusted feasibility
   │
   ▼
Ranking
   │
   ▼
MCP proposal
```

H3 does not calculate routes.

OSRM does not provide real-time traffic by itself.

The traffic component is therefore an independent layer.

---

# 28. Traffic Masking

Traffic should not be represented as:

```text
OSRM = live traffic
```

Instead:

```text
OSRM baseline route
        +
traffic provider/segment data
        ↓
traffic mask
        ↓
adjusted route feasibility
```

The GIS API should expose:

```text
traffic_status:
NORMAL
SLOW
HEAVY
BLOCKED
UNKNOWN
```

If real-time traffic data is unavailable:

```text
traffic_status = UNKNOWN
```

rather than fabricating traffic values.

---

# 29. MCP SERVICE

MCP is the natural-language orchestration layer.

The LLM does not directly access PostgreSQL.

It calls typed tools.

Core tools:

```text
search_equipment
verify_asset
find_feasible_routes
rank_options
create_loan_proposal
reserve_asset
get_transaction_status
request_payment
```

---

# 30. MCP Request Flow

User:

> Find a ventilator within 30 minutes.

```text
USER
 ↓
MCP
 ↓
parse requirement
 ↓
search_equipment
 ↓
GIS candidates
 ↓
OSRM
 ↓
traffic feasibility
 ↓
availability
 ↓
transaction terms
 ↓
rank
 ↓
PROPOSAL
 ↓
USER APPROVAL
```

MCP cannot silently execute consequential actions.

---

# 31. MCP Tools

### `search_equipment`

Read-only.

---

### `find_feasible_routes`

Read-only.

---

### `rank_options`

Read-only.

---

### `create_loan_proposal`

Creates a proposal but does not reserve or pay.

---

### `reserve_asset`

Consequential action.

Requires explicit user approval.

---

### `request_payment`

Consequential action.

Requires explicit user approval.

---

### `get_transaction_status`

Read-only.

---

# 32. MCP Security Rule

The following are never automatic:

```text
reserve
pay
cancel
dispatch
settle
```

The required pattern is:

```text
MCP
 ↓
PROPOSAL
 ↓
USER APPROVAL
 ↓
COMMAND
```

---

# 33. Reservation Service

### `POST /api/v1/reservations`

Arguments:

```text
asset_id
loan_terms
start_time
end_time
```

Server verifies:

```text
asset exists
asset belongs to another eligible organization
asset is shareable
asset is AVAILABLE
terms valid
requested period valid
```

Then performs a transactional reservation.

Returns:

```text
reservation_id
asset_id
status
expires_at
loan_id
```

---

### `GET /api/v1/reservations/{id}`

Returns complete reservation state.

---

### `POST /api/v1/reservations/{id}/cancel`

Cancels according to state rules.

---

### Reservation Expiry Worker

Periodically:

```text
find expired reservations
        ↓
verify current state
        ↓
release asset
        ↓
mark reservation EXPIRED
        ↓
emit reservation.expired
```

---

# 34. LOAN SERVICE

### `POST /api/v1/loans`

Creates a loan from an approved proposal/reservation.

---

### `GET /api/v1/loans`

Lists loans involving the authenticated organization.

---

### `GET /api/v1/loans/{loan_id}`

Returns:

```text
loan
borrower
lender
asset
terms
reservation
payment
blockchain state
dispatch state
return state
```

---

### `POST /api/v1/loans/{loan_id}/approve`

Approves a proposed transaction.

---

### `POST /api/v1/loans/{loan_id}/dispatch`

Marks dispatch after required prerequisites.

---

### `POST /api/v1/loans/{loan_id}/delivery-confirm`

Confirms delivery.

---

### `POST /api/v1/loans/{loan_id}/activate`

Moves delivered asset to ACTIVE.

---

### `POST /api/v1/loans/{loan_id}/return-request`

Requests return.

---

### `POST /api/v1/loans/{loan_id}/return-confirm`

Confirms physical return.

---

### `POST /api/v1/loans/{loan_id}/settle`

Attempts final settlement after all required conditions are satisfied.

---

# 35. IMPORTANT: State Transition Commands

Do not implement:

```text
PATCH /loans/{id}
{
    "status": "SETTLED"
}
```

Instead use commands:

```text
approve
dispatch
delivery-confirm
activate
return-request
return-confirm
settle
```

The backend checks:

```text
current state
actor authorization
required dependencies
payment state
blockchain state
asset state
```

before allowing the transition.

---

# 36. BLOCKCHAIN SERVICE

The smart contract is not a database dump.

It represents the contractual transaction state.

Store/commit:

```text
loan_id/reference
borrower wallet
lender wallet
asset reference/hash
reservation reference
terms hash
current contractual state
payment reference/hash
timestamps
```

Never store:

```text
patient information
passwords
private keys
UPI credentials
complete inventory
large GIS geometry
identity documents
```

---

# 37. Smart Contract State Guard

The contract must enforce legal transitions.

Conceptually:

```text
PROPOSED
   ↓
APPROVED
   ↓
RESERVED
   ↓
COMMITTED
   ↓
PAID
   ↓
DISPATCHED
   ↓
DELIVERED
   ↓
ACTIVE
   ↓
RETURNED
   ↓
SETTLED
```

Invalid transitions must revert.

For example:

```text
SETTLED → DISPATCHED
```

must fail.

Likewise:

```text
PROPOSED → SETTLED
```

must fail.

---

# 38. Blockchain Events

The contract emits events such as:

```text
LoanCreated
LoanApproved
ReservationCommitted
PaymentMarked
DispatchConfirmed
DeliveryConfirmed
LoanActivated
ReturnConfirmed
LoanSettled
```

The blockchain listener consumes these events.

---

# 39. Blockchain Listener

```text
Blockchain
    ↓
event emitted
    ↓
listener
    ↓
verify transaction/event
    ↓
idempotency check
    ↓
update Supabase
    ↓
emit domain event
    ↓
notification
    ↓
realtime frontend
```

The listener must tolerate:

* duplicate events
* delayed events
* failed RPC calls
* temporary network failure
* chain reorganization on public networks
* transaction replacement where applicable

The database should never blindly trust an event without validating its source and transaction.

---

# 40. Blockchain and Database Consistency

The architecture is intentionally asynchronous.

Example:

```text
Loan approved
      ↓
DB = BLOCKCHAIN_PENDING
      ↓
transaction submitted
      ↓
blockchain transaction hash stored
      ↓
chain confirms
      ↓
listener receives event
      ↓
DB = BLOCKCHAIN_CONFIRMED
```

Do not pretend PostgreSQL and blockchain can be committed atomically as one ACID transaction.

They cannot.

Use:

```text
state machine
+
idempotency
+
event reconciliation
```

instead.

---

# 41. BLOCKCHAIN MVP NETWORK

Development:

```text
Hardhat local EVM
```

Optional public demonstration:

```text
Ethereum Sepolia
```

The contract address and deployment metadata must be versioned as deployment configuration, not manually copied into random application files.

Production architecture can later evolve to a permissioned EVM consortium.

---

# 42. WALLET

MVP:

```text
one primary wallet per organization
```

The wallet represents the hospital's blockchain identity.

It is not the hospital's UPI account.

```text
Hospital
 ├── wallet_address
 │      ↓
 │   blockchain identity
 │
 └── payment account
        ↓
     INR / UPI
```

Private keys must never be stored in Supabase as plaintext.

---

# 43. PAYMENT SERVICE

Razorpay is the INR payment gateway.

Payment flow:

```text
Loan approved
      ↓
calculate payable amount
      ↓
create Razorpay payment/order request
      ↓
user opens Razorpay payment flow
      ↓
UPI Intent / QR / supported method
      ↓
payment
      ↓
Razorpay webhook
      ↓
verify signature
      ↓
reconcile
      ↓
payment.completed
```

The exact payment method exposed to the user must follow the payment products actually enabled on the Razorpay account.

Do not build around an assumption that an arbitrary UPI ID can always be charged through a deprecated/unsupported collect workflow.

---

# 44. MVP Payment Model

For MVP:

```text
Borrower Hospital
        │
        │ INR payment
        ▼
Razorpay
```

Do not claim that SANJEEVANI has solved institutional marketplace settlement.

The MVP demonstrates:

```text
real payment infrastructure
+
real payment state
+
real webhook
+
real reconciliation
```

The eventual:

```text
Hospital A → platform/escrow → Hospital B
```

marketplace settlement architecture remains a later phase requiring the appropriate Razorpay product, onboarding, KYC and settlement model.

---

# 45. Dynamic Demonstration Amount

The UI may show the full economic transaction:

```text
Equipment rental
₹X
Deposit
₹Y
Estimated total
₹Z
```

For a controlled demonstration, the actual payable amount can be deliberately configured to a small value.

Example:

```text
demo_charge = ₹1 / ₹2 / ₹3
```

based on:

```text
equipment type
loan duration
reservation duration
```

The system must clearly distinguish:

```text
displayed transaction economics
```

from:

```text
actual payable amount
```

so that the demo does not falsely imply the ₹1 payment represents the actual commercial settlement.

---

# 46. Payment Endpoints

### `POST /api/v1/payments/create`

Creates a payment request/order.

Returns:

```text
payment_id
provider
provider_order_id
amount
currency
status
checkout/reference data
```

---

### `GET /api/v1/payments/{payment_id}`

Returns reconciled payment state.

---

### `POST /api/v1/payments/webhook/razorpay`

Receives Razorpay webhook.

Requirements:

```text
signature verification
idempotency
event validation
payment lookup
state transition validation
```

---

### `POST /api/v1/payments/{payment_id}/reconcile`

Internal/admin-safe reconciliation operation for exceptional cases.

---

# 47. Payment State Machine

```text
CREATED
   ↓
INITIATED
   ↓
PENDING
   ├── FAILED
   ├── CANCELLED
   └── COMPLETED
```

A payment webhook must not directly set a loan to `SETTLED`.

It only updates the payment state.

The loan workflow decides what that payment state permits.

---

# 48. EMAIL SERVICE

Email is transactional, not marketing.

Major events generate email requests.

Required notifications:

```text
Account registered
Email verification
Profile completed
Loan proposed
Loan approved
Reservation created
Reservation expiring
Blockchain commitment confirmed
Payment requested
Payment completed
Payment failed
Loan confirmed
Dispatch confirmed
Delivery confirmed
Return requested
Return confirmed
Loan settled
```

---

# 49. Email Architecture

Do not send email synchronously inside every business transaction.

Instead:

```text
business event
      ↓
notification event
      ↓
email worker
      ↓
email provider
      ↓
delivery result
```

Database stores:

```text
notification_id
event_type
recipient
status
provider_message_id
attempt_count
sent_at
```

This permits retry without repeating business operations.

---

# 50. Realtime Frontend

Supabase Realtime can expose permitted changes to authenticated clients.

Example:

```text
loan state changed
      ↓
Supabase realtime
      ↓
frontend
      ↓
Monitor page updates
```

Realtime is for UI freshness.

It is not the source of truth.

The backend/database remains authoritative.

---

# 51. Activity Timeline

Every major domain event becomes an activity record.

Example:

```text
10:01  Loan proposed
10:02  User approved
10:02  Reservation created
10:02  Blockchain transaction submitted
10:03  Blockchain confirmed
10:03  Payment requested
10:04  Payment completed
10:04  Loan confirmed
10:20  Dispatch confirmed
10:46  Delivery confirmed
11:00  Loan activated
...
```

Activity records should be append-oriented.

---

# 52. DOMAIN EVENTS

Canonical events:

```text
user.registered
user.email_verified

organization.created
organization.profile_completed

asset.created
asset.availability_changed

loan.proposed
loan.approved

reservation.created
reservation.expired
reservation.cancelled

blockchain.commit_requested
blockchain.submitted
blockchain.confirmed
blockchain.failed

payment.requested
payment.initiated
payment.completed
payment.failed

loan.confirmed
loan.dispatched
loan.delivered
loan.activated
loan.return_requested
loan.returned
loan.settled

notification.email_requested
```

---

# 53. EVENT RULE

An endpoint performs an operation.

An event describes something that happened.

Example:

```text
POST /loans/{id}/approve
```

causes:

```text
loan.approved
```

The event can trigger:

```text
blockchain commitment
activity
email
realtime update
```

without the loan endpoint containing all those implementation details.

---

# 54. IDEMPOTENCY

Mandatory for:

```text
reservation creation
payment webhook
blockchain listener
loan transitions
email dispatch
```

Example:

```text
payment.completed
```

arrives twice.

The second event must not:

```text
create another payment
settle another loan
send duplicate business actions
```

Use stable provider/event identifiers.

---

# 55. RETRY POLICY

External integrations are unreliable.

Retries are required for:

```text
OSRM
traffic API
Razorpay API
email provider
blockchain RPC
```

Retries should use:

```text
bounded retries
exponential backoff
idempotency
dead-letter/error state
```

Do not retry permanently invalid requests.

---

# 56. SITEMAP

## Public

```text
/
├── /
│   └── Landing
│
├── /how-it-works
│
├── /network
│
├── /faq
│
├── /login
│
└── /signup
```

---

## Authenticated

```text
/app
│
├── /dashboard
│
├── /assistant
│
├── /marketplace
│
├── /map
│
├── /monitor
│
├── /activity
│
├── /inventory
│
├── /profile
│
└── /settings
```

---

# 57. Dashboard

Dashboard shows only real data.

Sections:

```text
Available equipment
Active loans
Pending approvals
Pending payments
Upcoming returns
Recent activity
Network snapshot
```

No fabricated statistics.

---

# 58. Assistant

Primary MCP interface.

Example:

```text
Find a ventilator within 30 minutes.
```

Displays:

```text
Best option
Hospital
Equipment
Availability
ETA
Distance
Traffic
Price
Deposit
Verification
```

Then:

```text
[View route]
[View details]
[Approve]
```

---

# 59. Marketplace

Manual discovery interface.

```text
Search
Filter
Sort
View equipment
View hospital
View route
```

Marketplace answers:

> What is available?

MCP answers:

> Which option is best for my requirement?

---

# 60. Map

Map should be meaningful.

For an active search:

```text
origin
candidate hospitals
route
traffic state
ETA
```

For no active route:

```text
No active route.
```

Do not render a decorative map simply to demonstrate GIS.

---

# 61. Monitor

Displays the lifecycle of a transaction:

```text
Proposal
Reservation
Blockchain
Payment
Confirmation
Dispatch
Delivery
Active
Return
Settlement
```

Both participating hospitals see only information authorized for them.

---

# 62. Inventory

Hospital's own assets:

```text
Asset
Equipment type
Condition
Availability
Price
Reservation
Current state
```

---

# 63. Activity

Chronological system activity.

---

# 64. Profile

```text
Hospital identity
Facility verification
Administrator profile
Wallet
Payment configuration
```

---

# 65. Settings

MVP settings should remain minimal:

```text
Account
Email
Session
Notifications
Security
```

Do not add complex organization administration.

---

# 66. Complete Demo Workflow

## Stage 1 — Hospital Registration

Hospital A:

```text
Signup
 ↓
Hospital Name
 ↓
ABDM/HFR ID
 ↓
Directory verification
 ↓
duplicate check
 ↓
organization created
```

---

## Stage 2 — Profile

```text
Email verification
 ↓
Name
Identity proof
Wallet
Payment configuration
 ↓
Profile completed
```

---

## Stage 3 — Inventory

Hospital B:

```text
Register ventilator
 ↓
Condition = operational
 ↓
Shareable = true
 ↓
Available
```

---

## Stage 4 — Request

Hospital A:

> Find a ventilator within 30 minutes.

---

## Stage 5 — MCP

```text
MCP
 ↓
search equipment
 ↓
available assets
 ↓
PostGIS
 ↓
H3
 ↓
OSRM
 ↓
traffic masking
 ↓
rank
```

---

## Stage 6 — Proposal

```text
Hospital B
Ventilator #V-102

ETA: 24 minutes
Distance: 13.2 km
Traffic: Moderate
Availability: Available
Rental: ₹X
Deposit: ₹Y
```

---

## Stage 7 — User Approval

User clicks:

```text
Approve reservation
```

Only now does the system execute consequential actions.

---

# 67. Reservation

```text
BEGIN TRANSACTION

verify asset AVAILABLE

create reservation

asset → RESERVED

create loan

COMMIT
```

Then:

```text
reservation.created
```

is emitted.

---

# 68. Blockchain

Backend requests:

```text
loan commitment
```

Smart contract verifies:

```text
valid participants
valid asset reference
valid terms hash
valid current state
valid transition
```

Transaction submitted.

Database:

```text
BLOCKCHAIN_PENDING
```

---

# 69. Blockchain Confirmation

Listener receives:

```text
LoanApproved / ReservationCommitted
```

After validation:

```text
BLOCKCHAIN_CONFIRMED
```

Then:

```text
email
activity
realtime
```

are triggered.

---

# 70. Payment

Payment request is created.

User sees:

```text
Pay ₹2
```

or the configured demonstration amount.

Razorpay flow:

```text
Razorpay
 ↓
UPI Intent / QR / supported payment method
 ↓
user confirms on device
 ↓
Razorpay
 ↓
webhook
```

---

# 71. Payment Reconciliation

Webhook:

```text
signature verified
 ↓
event identified
 ↓
payment identified
 ↓
idempotency check
 ↓
payment state updated
 ↓
payment.completed
```

Then loan becomes eligible for:

```text
CONFIRMED
```

only if all other required conditions are satisfied.

---

# 72. Dispatch

Authorized user confirms dispatch:

```text
CONFIRMED
 ↓
DISPATCHED
```

Activity and email generated.

---

# 73. Delivery

Recipient confirms:

```text
DISPATCHED
 ↓
DELIVERED
```

Then:

```text
DELIVERED
 ↓
ACTIVE
```

---

# 74. Return

Borrower requests return:

```text
ACTIVE
 ↓
RETURN_REQUESTED
```

After physical confirmation:

```text
RETURNED
```

---

# 75. Settlement

Settlement command checks:

```text
returned
payment complete
blockchain state valid
no unresolved exception
```

Then:

```text
SETTLEMENT_PENDING
 ↓
SETTLED
```

Asset:

```text
AVAILABLE
```

---

# 76. Final End-to-End Event Chain

```text
signup
  ↓
organization.created
  ↓
email_verified
  ↓
profile_completed
  ↓
asset.created
  ↓
loan.proposed
  ↓
USER APPROVAL
  ↓
reservation.created
  ↓
blockchain.commit_requested
  ↓
blockchain.confirmed
  ↓
payment.requested
  ↓
payment.completed
  ↓
loan.confirmed
  ↓
loan.dispatched
  ↓
loan.delivered
  ↓
loan.activated
  ↓
loan.return_requested
  ↓
loan.returned
  ↓
loan.settled
  ↓
asset AVAILABLE
```

---

# 77. Failure Paths

SANJEEVANI must explicitly handle failure.

## No hospital found

```text
MCP
 ↓
No suitable equipment
```

Return:

```text
No feasible equipment found within requested constraints.
```

---

## Route unavailable

```text
OSRM failure
```

Do not fabricate ETA.

Return:

```text
Route calculation unavailable.
```

---

## Traffic unavailable

Use:

```text
traffic_status = UNKNOWN
```

and clearly distinguish:

```text
baseline ETA
```

from:

```text
traffic-adjusted ETA
```

---

## Asset becomes unavailable

During reservation:

```text
transaction fails
```

No loan should be created.

---

## Reservation expires

```text
RESERVED
 ↓
EXPIRED
 ↓
AVAILABLE
```

---

## Blockchain transaction fails

```text
BLOCKCHAIN_PENDING
 ↓
BLOCKCHAIN_FAILED
```

Payment should not be treated as fully confirmed unless business rules explicitly permit it.

---

## Payment fails

```text
PAYMENT_PENDING
 ↓
PAYMENT_FAILED
```

Loan remains unconfirmed.

---

## Webhook duplicated

Ignored after idempotency check.

---

## Email fails

Business transaction remains valid.

Email failure must not roll back:

```text
loan
payment
reservation
```

Instead:

```text
notification = FAILED
retry
```

---

# 78. Security

Minimum mandatory security:

```text
HTTPS
Supabase Auth
JWT validation
organization-level authorization
database constraints
Supabase RLS where appropriate
input validation
rate limiting
secret management
webhook signature validation
wallet signing isolation
idempotency
audit/activity trail
```

---

# 79. Multi-Tenancy

Every private query must resolve through:

```text
authenticated_user
       ↓
organization_id
       ↓
authorized records
```

Hospital A cannot read:

```text
Hospital B's
users
private transactions
private revenue
private audit information
```

Public network information may expose:

```text
hospital name
location
available equipment
price
general availability
verification status
```

only where intended.

---

# 80. Data Privacy

Never store patient information.

Never put the following on blockchain:

```text
patient records
passwords
identity documents
payment credentials
private UPI information
complete hospital database
large GIS payloads
```

---

# 81. API Metadata Standard

Every endpoint should define:

```text
Method
Path
Authentication
Authorization
Purpose
Request schema
Response schema
Errors
Idempotency requirement
Emitted events
External dependencies
```

Example:

```text
POST /api/v1/reservations

Auth:
Required

Authorization:
Authenticated organization

Idempotency:
Required

Request:
asset_id
start_time
end_time
loan_terms

Response:
reservation_id
loan_id
status
expires_at

Events:
reservation.created

Dependencies:
Supabase
```

This metadata should ultimately be represented in:

```text
contracts/api/openapi.yaml
```

---

# 82. Standard Error Model

All APIs should return a predictable structure:

```text
error
code
message
request_id
details
```

Examples:

```text
ASSET_UNAVAILABLE
RESERVATION_EXPIRED
INVALID_STATE_TRANSITION
PAYMENT_FAILED
BLOCKCHAIN_PENDING
FACILITY_NOT_VERIFIED
ORGANIZATION_ALREADY_REGISTERED
PROFILE_INCOMPLETE
UNAUTHORIZED
```

---

# 83. Observability

Every request should have:

```text
request_id
```

External calls should record:

```text
provider
request/reference ID
latency
status
error
```

Important integrations:

```text
OSRM
traffic provider
Razorpay
blockchain RPC
email provider
```

must be observable.

---

# 84. Recommended Repository Structure

```text
SANJEEVANI/
│
├── frontend/
│
├── backend/
│   ├── auth/
│   ├── organizations/
│   ├── facilities/
│   ├── equipment/
│   ├── marketplace/
│   ├── reservations/
│   ├── loans/
│   ├── payments/
│   ├── blockchain/
│   ├── notifications/
│   ├── activity/
│   └── realtime/
│
├── GIS/
│   ├── postgis/
│   ├── h3/
│   ├── routing/
│   ├── traffic/
│   └── scoring/
│
├── MCP/
│   ├── tools/
│   ├── resources/
│   ├── prompts/
│   └── orchestration/
│
├── blockchain/
│   ├── contracts/
│   ├── scripts/
│   ├── deployments/
│   └── tests/
│
├── primary/
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── visualization/
│   ├── notebooks/
│   └── docs/
│
├── contracts/
│   ├── api/
│   ├── database/
│   ├── events/
│   └── states/
│
├── docs/
│   ├── architecture.md
│   ├── workflow.md
│   ├── sitemap.md
│   └── security.md
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── assets/
│
├── .env.example
├── .gitignore
└── README.md
```

---

# 85. Technology Stack

Keep the stack intentionally small.

## Frontend

```text
React
TypeScript
```

---

## Backend

```text
FastAPI
Python
```

---

## Database

```text
Supabase
PostgreSQL
PostGIS
```

---

## Authentication

```text
Supabase Auth
```

---

## GIS

```text
PostGIS
H3
OSRM
Traffic provider abstraction
```

---

## AI / Orchestration

```text
MCP
LLM provider
```

The LLM provider should remain replaceable.

---

## Blockchain

```text
Solidity
Hardhat
EVM
```

---

## Payments

```text
Razorpay
UPI-supported payment flow
```

---

## Notifications

```text
Transactional email provider
```

---

## Realtime

```text
Supabase Realtime
```

---

# 86. Components Deliberately NOT Required

Do not introduce:

```text
Kafka
Redis cluster
Kubernetes
microservice mesh
Apache Spark
separate authentication service
separate PostgreSQL server
separate compliance blockchain
patient EMR system
custom routing engine
custom payment processor
```

unless an actual requirement later justifies them.

The MVP should be sophisticated in **architecture**, not bloated in infrastructure.

---

# 87. Build Phases

## Phase 0 — Foundation

Build:

```text
repository
environment
Supabase
database schema
RLS
contracts
API specification
event specification
state machines
CI
```

Definition of done:

```text
empty system boots
database migrates
authentication works
API health check works
frontend connects
```

---

# 88. Phase 1 — Real Hospital Directory

Process:

```text
raw dataset
 ↓
clean
 ↓
validate
 ↓
deduplicate
 ↓
quality report
 ↓
processed_hospitals.csv
 ↓
Supabase facility_directory
```

Definition of done:

```text
facility lookup works
facility coordinates valid
facility records queryable
```

---

# 89. Phase 2 — Authentication & Profile

Implement:

```text
signup
facility verification
duplicate hospital detection
Supabase Auth
session
email verification
profile completion
wallet
payment configuration
```

Definition of done:

A new hospital can independently create and activate its SANJEEVANI account.

---

# 90. Phase 3 — Inventory

Implement:

```text
equipment types
assets
availability
condition
pricing
shareability
```

Definition of done:

Hospital B can publish a real available equipment asset.

---

# 91. Phase 4 — GIS

Implement:

```text
PostGIS
H3
OSRM
traffic abstraction
route scoring
```

Definition of done:

Given:

```text
origin + equipment requirement
```

SANJEEVANI returns:

```text
feasible hospitals
route
distance
ETA
traffic state
```

---

# 92. Phase 5 — MCP

Implement:

```text
natural-language request
tool selection
tool execution
proposal generation
human approval
```

Definition of done:

User can say:

> Find a ventilator within 30 minutes.

and receive a meaningful ranked proposal.

---

# 93. Phase 6 — Reservation & Loan

Implement:

```text
reservation transaction
expiry worker
loan creation
state transitions
activity events
```

Definition of done:

Two concurrent requests cannot reserve the same asset.

---

# 94. Phase 7 — Blockchain

Implement:

```text
smart contract
state guards
deployment
transaction service
event listener
reconciliation
```

Definition of done:

Every required contractual loan transition generates a verifiable blockchain event and invalid transitions are rejected.

---

# 95. Phase 8 — Razorpay

Implement:

```text
payment creation
checkout/payment flow
webhook
signature verification
idempotency
reconciliation
payment state machine
```

Definition of done:

A real Razorpay test-mode transaction can move through:

```text
created
→ initiated
→ pending
→ completed/failed
```

without mocking business success.

---

# 96. Phase 9 — Dispatch / Delivery / Return

Implement:

```text
dispatch
delivery
activation
return
settlement
```

Definition of done:

One loan can complete the full lifecycle.

---

# 97. Phase 10 — Notifications + Realtime

Implement:

```text
email events
email worker
retries
Supabase realtime
activity stream
```

Definition of done:

Major events become visible to the user without manual refresh and important events generate email.

---

# 98. Phase 11 — Full E2E Test

The golden test is:

```text
REGISTER HOSPITAL A
        ↓
REGISTER HOSPITAL B
        ↓
B REGISTERS VENTILATOR
        ↓
A REQUESTS VENTILATOR
        ↓
MCP
        ↓
GIS
        ↓
H3
        ↓
OSRM
        ↓
TRAFFIC
        ↓
PROPOSAL
        ↓
A APPROVES
        ↓
RESERVATION
        ↓
BLOCKCHAIN
        ↓
BLOCKCHAIN EVENT
        ↓
PAYMENT REQUEST
        ↓
RAZORPAY
        ↓
UPI PAYMENT
        ↓
WEBHOOK
        ↓
PAYMENT CONFIRMED
        ↓
LOAN CONFIRMED
        ↓
DISPATCH
        ↓
DELIVERY
        ↓
ACTIVE
        ↓
RETURN
        ↓
SETTLEMENT
        ↓
ASSET AVAILABLE
```

Every step must produce the expected database/event/UI result.

---

# 99. Golden Failure Tests

Test at least:

```text
duplicate hospital signup
invalid ABDM ID
unverified email
incomplete profile
duplicate wallet
asset already reserved
reservation expiry
simultaneous reservations
OSRM unavailable
traffic unavailable
blockchain transaction failure
duplicate blockchain event
payment failure
duplicate Razorpay webhook
email failure
invalid state transition
unauthorized organization access
expired session
```

---

# 100. Final Architecture Principle

SANJEEVANI should follow:

```text
DATABASE
    ↓
operational truth

BLOCKCHAIN
    ↓
contractual integrity

RAZORPAY
    ↓
payment execution

GIS
    ↓
spatial feasibility

MCP
    ↓
reasoning/orchestration

FRONTEND
    ↓
human interaction
```

No component should impersonate another component's responsibility.

---

# 101. Final MVP Definition

SANJEEVANI MVP is complete when a hospital can:

```text
REGISTER
   ↓
VERIFY
   ↓
COMPLETE PROFILE
   ↓
REGISTER EQUIPMENT
   ↓
DISCOVER NETWORK
   ↓
ASK MCP
   ↓
GET GIS-FEASIBLE OPTIONS
   ↓
APPROVE
   ↓
RESERVE
   ↓
COMMIT ON BLOCKCHAIN
   ↓
PAY THROUGH RAZORPAY
   ↓
RECEIVE CONFIRMATION
   ↓
DISPATCH
   ↓
DELIVER
   ↓
ACTIVATE
   ↓
RETURN
   ↓
SETTLE
```

while the system simultaneously maintains:

```text
Supabase operational state
+
smart-contract guarded state
+
Razorpay payment state
+
GIS feasibility
+
activity history
+
email notifications
+
realtime UI state
```

---

# 102. What SANJEEVANI Does NOT Claim

SANJEEVANI does not claim to:

* replace ABDM/HFR,
* replace hospital ERP systems,
* replace e-Upkaran,
* provide medical diagnosis,
* guarantee clinical outcomes,
* provide government verification beyond the directory source actually available,
* solve institutional marketplace settlement,
* make blockchain the primary database,
* provide real-time traffic if the configured traffic provider does not provide it,
* guarantee an equipment delivery time,
* guarantee equipment safety beyond the data supplied by participating hospitals.

The defensible proposition is:

> **SANJEEVANI transforms independently operated hospital inventories into a coordinated resource-sharing network, using verified facility identity, live equipment availability, AI orchestration, geospatial feasibility, transactional reservation, blockchain-backed contractual state and conventional digital payment infrastructure.**

---

# 103. Final Architecture Snapshot

```text
                         SANJEEVANI
                 We care when even seconds count
                              │
                              ▼
                       ┌──────────────┐
                       │   FRONTEND   │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ SUPABASE AUTH│
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ SANJEEVANI   │
                       │   BACKEND    │
                       └──────┬───────┘
                              │
         ┌────────────────────┼──────────────────────┐
         │                    │                      │
         ▼                    ▼                      ▼
     SUPABASE               MCP                NOTIFICATION
   PostgreSQL               │                     EMAIL
    + PostGIS               │
         │          ┌────────┼────────┐
         │          │        │        │
         │          ▼        ▼        ▼
         │       INVENTORY  GIS    TRANSACTION
         │                   │
         │              ┌────┴─────┐
         │              │          │
         │             H3         OSRM
         │              │          │
         │              └────┬─────┘
         │                   ▼
         │              TRAFFIC
         │                   │
         │                   ▼
         │               RANKING
         │
         ├──────────────────────┐
         │                      │
         ▼                      ▼
   SMART CONTRACT            RAZORPAY
         │                      │
         ▼                      ▼
   BLOCKCHAIN EVENTS       PAYMENT WEBHOOK
         │                      │
         └───────────┬──────────┘
                     ▼
               RECONCILIATION
                     │
                     ▼
                SUPABASE STATE
                     │
                     ▼
              REALTIME FRONTEND
```

---

# 104. The Final Rule

The MVP should be judged by one question:

> **Can SANJEEVANI take a real hospital equipment request and reliably move it from discovery to a guarded, paid, auditable and completed inter-hospital transaction?**

If yes, the architecture has done its job.

If a component does not contribute to that workflow, it does not belong in the MVP.
