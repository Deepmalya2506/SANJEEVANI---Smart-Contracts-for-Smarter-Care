from app.core.database import hospital_collection, inventory_collection
from app.services.gis_client import get_best_option
from app.services.blockchain_client import create_loan

def dispatch_logic(request_data):
    equipment_type = request_data["equipment_type"]
    quantity = request_data["quantity"]
    origin = {
        "lat": request_data["location"]["lat"],
        "lon": request_data["location"]["lon"]
    }

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

    if not hospitals:
        return {"error": "No hospitals available"}

    # Step 2: GIS call

    # transform hospitals for GIS
    gis_hospitals = [
        {
            "id": h["id"],
            "lat": h["location"]["lat"],
            "lon": h["location"]["lon"]
        }
        for h in hospitals
    ]

    best = get_best_option(origin, gis_hospitals)

    best_data = best["data"]
    best_id = best_data["best_hospital"]

    print("GIS REQUEST:", {
        "origin": origin,
        "hospitals": gis_hospitals
    })

    print("GIS RESPONSE:", best)

    best_hospital = next(
        h for h in hospitals if h["id"] == best_id
    )

    # Step 3: Blockchain
    loan = create_loan({
        "lender": best_hospital["wallet"],  # ✅ correct
        "equipment_id": equipment_type,
        "quantity": quantity,
        "duration": 4,
        "value": 8000
    })

    return {
        "selected_hospital": best_data,
        "loan": loan
    }