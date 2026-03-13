from mcp.database import equipment_collection


async def reserve_equipment(hospital_id, equipment_type, quantity):

    equipment = await equipment_collection.find_one({
        "hospital_id": hospital_id,
        "equipment_type": equipment_type
    })

    available_assets = [
        asset for asset in equipment["assets"] #type:ignore
        if asset["status"] == "AVAILABLE"
    ]

    selected = available_assets[:quantity]

    for asset in selected:

        await equipment_collection.update_one(
            {
                "hospital_id": hospital_id,
                "assets.asset_uid": asset["asset_uid"]
            },
            {
                "$set": {
                    "assets.$.status": "RESERVED"
                }
            }
        )

    return selected