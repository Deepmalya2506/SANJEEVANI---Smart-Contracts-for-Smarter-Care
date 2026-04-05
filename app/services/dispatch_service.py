from app.core.database import hospital_collection, inventory_collection
from app.services.gis_client import get_best_option
from app.services.blockchain_client import create_loan

def dispatch_logic(request_data):
    equipment_type = request_data["equipment_type"]
    quantity = request_data["quantity"]
    origin = request_data["location"]

    # Step 1: find hospitals with inventory
    inventory = inventory_collection.aggregate([
        {"$match": {"equipment_type": equipment_type, "status": "AVAILABLE"}},
        {"$group": {"_id": "$hospital_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": quantity}}}
    ])

    hospital_ids = [i["_id"] for i in inventory]

    hospitals = list(hospital_collection.find(
        {"id": {"$in": hospital_ids}},
        {"_id": 0}
    ))

    # Step 2: GIS call
    best = get_best_option(origin, hospitals)
    best_hospital = next(h for h in hospitals if h["id"] == best["hospital_id"])

    # Step 3: Blockchain
    loan = create_loan({
        "lender": best["hospital_id"]["wallet"],  # VERY IMPORTANT
        "equipment_id": equipment_type,
        "quantity": quantity,
        "duration": 4,
        "value": 8000  # must match contract logic
    })

    return {
        "selected_hospital": best,
        "loan": loan
    }