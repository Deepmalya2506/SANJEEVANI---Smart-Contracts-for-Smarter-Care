import requests
from config import OSRM_BASE_URL, OSRM_ROUTE_URL

def get_distance_matrix(coordinates: list):
    """
    coordinates: list of (lon, lat)
    Example:
    [(88.3639, 22.5726), (88.3739, 22.5826)]
    """

    coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])

    url = f"{OSRM_BASE_URL}/table/v1/driving/{coords_str}?annotations=distance,duration"

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception("OSRM request failed")

    data = response.json()

    return {
        "distances": data.get("distances"),
        "durations": data.get("durations")
    }


def get_route(source, destination):
    """
    source, destination = (lon, lat)
    """

    coord_string = f"{source[0]},{source[1]};{destination[0]},{destination[1]}"

    url = OSRM_ROUTE_URL + coord_string + "?overview=full&geometries=geojson"

    response = requests.get(url)
    data = response.json()

    route = data["routes"][0]

    return {
        "geometry": route["geometry"],  # GeoJSON line
        "distance": route["distance"],
        "duration": route["duration"]
    }