# build a simluation of MCP logic to create basic agent for automation

def search_eqipment(name, quantity):
    print(f"Searching for the {name} by calling mcp")
    return [
        {"hospital" : "Hospital B", "distance" : "5", "available" : "20"},
        {"hospital" : "Hospital A", "distance" : "10", "available" : "50"}
    ]
# a different functions
def create_loan(borrower, lender, equipement, qty):
    print("Calling MCP: create_loan")
    
    return {
        "loan_id": 1,
        "status": "CREATED"
    }
# later i will use

#import requests

#requests.post("http://localhost:8000/search", json=...)
