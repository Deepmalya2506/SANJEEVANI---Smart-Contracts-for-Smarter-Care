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

    # Step 3: Blockchain
    loan = create_loan({
        "hospital_id": best["hospital_id"],
        "equipment_type": equipment_type,
        "quantity": quantity
    })

    return {
        "selected_hospital": best,
        "loan": loan
    }