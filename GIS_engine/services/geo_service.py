from services.osrm_service import get_distance_matrix

def find_nearest(user_location, hospitals):
    """
    user_location: (lon, lat)
    hospitals: list of {id, lon, lat}
    """

    # Build coordinate list (user first, then hospitals)
    coords = [user_location] + [(h.lon, h.lat) for h in hospitals]

    matrix = get_distance_matrix(coords)

    distances = matrix["distances"][0][1:]  # user → hospitals
    durations = matrix["durations"][0][1:]

    results = []

    for i, hospital in enumerate(hospitals):
        results.append({
            "hospital_id": hospital.id,
            "distance_m": distances[i],
            "duration_s": durations[i]
        })

    # Sort by distance (or duration)
    results.sort(key=lambda x: x["duration_s"])  # smarter: time-based

    best = results[0]

    return {
        "nearest": best["hospital_id"],
        "distance_km": round(best["distance_m"] / 1000, 2),
        "eta_min": round(best["duration_s"] / 60, 2),
        "all_options": results
    }