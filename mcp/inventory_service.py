from mcp.database import equipment_collection

async def reserve_equipment(lender, equipment_id, quantity):

    available = equipment_collection.find({
        "equipment_type": equipment_id,
        "status": "AVAILABLE"
    }).limit(quantity)

    reserved = []

    for item in available:
        equipment_collection.update_one(
            {"_id": item["_id"]},
            {"$set": {"status": "RESERVED"}}
        )
        reserved.append(item["_id"])

    print("Reserved equipment:", reserved)

    return reserved