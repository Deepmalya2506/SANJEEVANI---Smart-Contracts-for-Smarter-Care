from tools import search_eqipment, create_loan

def handle_request():
    print("agent received request")

    hostpitals = search_eqipment("Oxygen Cylinder",10)
    best = sorted(hostpitals, key=lambda x: x["distance"])[0]
    loan = create_loan (
        borrower="Hospital A",
        lender = best["hospital"],
        equipement="Oxygen Cylinder",
        qty = 10
    )
    
    return loan