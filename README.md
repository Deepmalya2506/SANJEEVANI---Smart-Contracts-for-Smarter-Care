<div align="center">

# SANJEEVANI

### Smart Contracts for Smarter Care

<img src="./docs/images/image.png" alt="Sanjeevani Landing Page" width="100%"/>

Healthcare logistics powered by Smart Contracts, MCP Nodes, and GIS Routing.

[Features](#features) •
[Architecture](#architecture) •
[Installation](#installation) •
[Roadmap](#roadmap)

</div>

---

## Overview

Sanjeevani is a decentralized healthcare logistics platform designed to solve critical medical equipment shortages during emergencies.

Hospitals often face delays in accessing life-saving equipment due to disconnected inventory systems, manual coordination, and inefficient resource allocation.

Sanjeevani creates a trusted healthcare network where hospitals can:

- Share medical equipment securely
- Track resources in real time
- Automate lending agreements using smart contracts
- Optimize emergency dispatch using GIS routing
- Coordinate seamlessly through MCP-powered orchestration

---

## Problem Statement

Healthcare systems today suffer from:

- No real-time visibility of medical equipment across hospitals
- Manual coordination through phone calls and spreadsheets
- Delayed emergency response caused by disconnected systems
- Equipment shortages despite nearby availability
- Lack of a trusted framework for inter-hospital lending

These inefficiencies can directly impact patient outcomes during critical situations.

---

## Solution

Sanjeevani introduces a sovereign healthcare logistics network powered by:

### Smart Contracts

Automate equipment lending, borrowing, validation, and settlement between hospitals.

### MCP Orchestration

Model Context Protocol (MCP) enables seamless communication and coordination between healthcare nodes.

### GIS Routing

Provides intelligent route optimization for transporting medical equipment during emergencies.

### Real-Time Resource Visibility

Hospitals can discover available equipment across participating nodes instantly.

---

## Features

### Smart Contract Layer

- Automated equipment lending agreements
- Transparent transaction history
- Tamper-resistant audit trail
- Trustless verification

### MCP Infrastructure

- Inter-node communication
- Context-aware orchestration
- Scalable healthcare network architecture

### GIS Intelligence

- Dynamic route optimization
- Emergency dispatch planning
- Distance and ETA estimation

### Emergency Resource Exchange

- Equipment discovery
- Resource allocation
- Hospital-to-hospital collaboration

---

## System Architecture

![Architecture Diagram](./docs/images/systemarch.png)

---

## Tech Stack

### Frontend

- Lightweight HTML and JavaScript client in `visuals/`

### Backend

- Python
- FastAPI
- Uvicorn

### Blockchain

- Smart Contracts
- Ethereum Compatible Networks

### GIS & Mapping

- OpenStreetMap
- OSRM routing service

### Protocol Layer

- Model Context Protocol (MCP)

---

## Installation

The current repository contains three local services:

| Service         | URL                     | Purpose                                          |
| --------------- | ----------------------- | ------------------------------------------------ |
| FastAPI backend | `http://127.0.0.1:8000` | Hospitals, inventory, dispatch                   |
| GIS engine      | `http://127.0.0.1:8001` | Routing and nearest-hospital selection           |
| MCP server      | `http://127.0.0.1:9001` | Natural-language orchestration and approval flow |

It also uses MongoDB and a local Ganache JSON-RPC node at `http://127.0.0.1:7545`.

### Prerequisites

- Windows PowerShell
- Node.js and npm
- Python 3.11 or newer
- Ganache Desktop or another Ethereum-compatible node listening on port `7545`
- A MongoDB database reachable using `MONGO_URI`
- Internet access for the public OSRM routing service and Groq API

### Clone and Install

```powershell
git clone <repository-url>
Set-Location SANJEEVANI---Smart-Contracts-for-Smarter-Care

npm install

py -3 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The Python blockchain integration requires `web3`. If it is not already listed in your local requirements file, install it with:

```powershell
pip install web3
```

### Configure Environment

Create a `.env` file in the repository root. Do not commit it.

```env
MONGO_URI=<your MongoDB connection string>
DB_NAME=sanjeevani
GIS_URL=http://127.0.0.1:8001
BLOCKCHAIN_URL=http://127.0.0.1:7545
CONTRACT_ADDRESS=<deployed contract address>
GROQ_API_KEY=<your Groq API key>
```

The MCP server also accepts `BLOCKCHAIN_RPC_URL`; when it is absent, it uses `BLOCKCHAIN_URL`.

### Start the Blockchain

Start Ganache and configure its RPC server to use port `7545`. Keep Ganache running while using the backend or MCP server.

Compile and deploy the contract from the repository root:

```powershell
npx hardhat compile
npx hardhat run scripts/deploy.ts --network localhost
```

Copy the deployed address into both `.env` as `CONTRACT_ADDRESS` and `scripts/config.ts`. Then register the equipment used by the workflow:

```powershell
npx hardhat run scripts/registerEquipment.ts --network localhost
```

Equipment IDs currently used by the system are:

| ID  | Equipment       | Hourly rate | Caution deposit |
| --- | --------------- | ----------: | --------------: |
| `1` | Oxygen Cylinder |       `500` |          `2000` |
| `2` | Ventilator      |      `2000` |         `15000` |
| `3` | Defibrillator   |      `1200` |          `5000` |

If Ganache is reset, redeploy the contract, update the address, and register the equipment again.

### Start the GIS Engine

Open a new PowerShell terminal from the repository root:

```powershell
\.venv\Scripts\Activate.ps1
python -m uvicorn GIS_engine.main:app --host 127.0.0.1 --port 8001 --reload
```

The GIS engine calls `router.project-osrm.org`, so its routing features need internet access.

### Start the FastAPI Backend

Open another PowerShell terminal:

```powershell
\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend needs MongoDB, Ganache, and the GIS engine running. Seed hospitals and inventory through the backend endpoints before dispatching. Hospital records require an `id`, `wallet`, and `location`; inventory records require a matching `hospital_id`, numeric `equipment_type`, and `status` set to `AVAILABLE`.

### Start the MCP Server

Open a fourth PowerShell terminal:

```powershell
\.venv\Scripts\Activate.ps1
python -m uvicorn mcp_server.wrapper:app --host 127.0.0.1 --port 9001 --reload
```

Check that it is running:

```powershell
Invoke-RestMethod http://127.0.0.1:9001/health
```

The MCP chat endpoint expects `query`, not `message`:

```powershell
$body = @{
	query = "List the available hospitals"
	hospital_id = "h1"
} | ConvertTo-Json

Invoke-RestMethod `
	-Uri http://127.0.0.1:9001/chat `
	-Method Post `
	-ContentType "application/json" `
	-Body $body | ConvertTo-Json -Depth 10
```

### Test the Borrow Workflow

Borrowing requests require two chat calls because the MCP pauses for explicit approval. First send the request:

```powershell
$body = @{
	query = "Borrow me an oxygen cylinder from the nearest available hospital. My location is (25.2, 25.8)."
	hospital_id = "h1"
} | ConvertTo-Json

$proposal = Invoke-RestMethod `
	-Uri http://127.0.0.1:9001/chat `
	-Method Post `
	-ContentType "application/json" `
	-Body $body

$proposal | ConvertTo-Json -Depth 10
```

The response should contain `approval_required: true` and a `session_id`. Approve that proposal using the same session:

```powershell
$approval = @{
	query = "yes"
	session_id = $proposal.session_id
	hospital_id = "h1"
} | ConvertTo-Json

Invoke-RestMethod `
	-Uri http://127.0.0.1:9001/chat `
	-Method Post `
	-ContentType "application/json" `
	-Body $approval | ConvertTo-Json -Depth 10
```

A successful approval returns a transaction hash and loan ID. The smart contract loan counter should increase by one.

### Direct API Checks

Check the backend and GIS services independently:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/hospitals

$dispatch = @{
	equipment_type = 1
	quantity = 1
	location = @{ lat = 25.2; lon = 27.2 }
} | ConvertTo-Json

Invoke-RestMethod `
	-Uri http://127.0.0.1:8000/dispatch `
	-Method Post `
	-ContentType "application/json" `
	-Body $dispatch | ConvertTo-Json -Depth 10
```

---

## Project Structure

```text
app/                  FastAPI backend and REST routes
GIS_engine/           Routing and distance services
mcp_server/           Natural-language agent and chat API
contracts/            Solidity escrow contract
scripts/              Deployment and contract lifecycle scripts
listeners/             Blockchain event listener
visuals/               Lightweight chat UI assets
docs/                  Architecture and product images
```

---

## Future Roadmap

### Phase 1

- Real-time inventory dashboard
- Hospital onboarding

### Phase 2

- Smart contract deployment
- Automated equipment lending

### Phase 3

- GIS emergency dispatch optimization
- Predictive equipment demand forecasting

### Phase 4

- AI-powered healthcare logistics agent
- Autonomous resource allocation

---

## Gallery

### Inventory Dashboard

![Dashboard](./docs/images/Dashboard.png)

### GIS Routing

![GIS Routing](./docs/images/GIS.jpeg)

---

## Potential Impact

Sanjeevani aims to create a healthcare ecosystem where critical medical equipment can be discovered, shared, and delivered rapidly during emergencies.

By combining smart contracts, intelligent routing, and interoperable healthcare infrastructure, the platform helps ensure that life-saving resources reach patients when they are needed most.

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---

<div align="center">

Smarter Care Health For Smart Health

</div>
