from GIS_engine.services.osrm_service import get_distance_matrix

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

def find_best_option(origin, hospitals):
    """
    origin = (lon, lat)
    hospitals = list of {id, lat, lon}
    """

    # Build coordinate list → origin + all hospitals
    coords = [(origin[0], origin[1])]
    for h in hospitals:
        coords.append((h["lon"], h["lat"]))

    # Call OSRM matrix
    result = get_distance_matrix(coords)

    durations = result["durations"][0]  # first row → origin to others
    distances = result["distances"][0]

    best_index = None
    best_time = float('inf')

    for i in range(1, len(durations)):
        if durations[i] is not None and durations[i] < best_time:
            best_time = durations[i]
            best_index = i

    if best_index is None:
        raise ValueError("No valid durations found. Unable to determine the best hospital.")

    best_hospital = hospitals[best_index - 1]

    return {
        "best_hospital": best_hospital["id"],
        "eta_min": best_time / 60,
        "distance_km": distances[best_index] / 1000,
        "all_options": [
            {
                "hospital_id": hospitals[i - 1]["id"],
                "distance_m": distances[i],
                "duration_s": durations[i]
            }
            for i in range(1, len(hospitals) + 1)
        ]
    }