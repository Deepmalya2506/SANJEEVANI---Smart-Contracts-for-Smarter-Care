import h3
from typing import Any

def latlng_to_h3(lat: float, lon: float, resolution: int = 7) -> str:
    """Converts latitude and longitude to an H3 hexagon index string at the given resolution."""
    return h3.latlng_to_cell(lat, lon, resolution)

def h3_to_latlng(h3_index: str) -> tuple[float, float]:
    """Converts an H3 hexagon index string back to (lat, lon) centroid coordinates."""
    return h3.cell_to_latlng(h3_index)

def h3_to_geojson_polygon(h3_index: str) -> list[list[float]]:
    """
    Returns the closed GeoJSON ring coordinates [[lon, lat], ...] for an H3 cell.
    Note: GeoJSON order is [lon, lat], whereas h3 boundary is (lat, lon).
    """
    boundary = h3.cell_to_boundary(h3_index)
    coords = [[point[1], point[0]] for point in boundary]
    if coords and coords[0] != coords[-1]:
        coords.append(coords[0])  # Close the ring
    return coords

def group_candidates_by_h3(
    candidates: list[dict[str, Any]],
    resolution: int = 7,
) -> dict[str, list[dict[str, Any]]]:
    """
    Groups candidate facilities into discrete H3 hexagonal spatial bins.
    Adds 'h3_cell' key to each candidate record.
    """
    hex_bins: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        lat = float(candidate.get("lat") if candidate.get("lat") is not None else candidate.get("latitude"))
        lon = float(candidate.get("lon") if candidate.get("lon") is not None else candidate.get("longitude"))
        cell = latlng_to_h3(lat, lon, resolution)
        candidate["h3_cell"] = cell
        if cell not in hex_bins:
            hex_bins[cell] = []
        hex_bins[cell].append(candidate)
    return hex_bins

def prune_redundant_candidates(
    candidates: list[dict[str, Any]],
    resolution: int = 7,
    max_per_cell: int = 2,
) -> list[dict[str, Any]]:
    """
    Eliminates redundant candidates in identical H3 cells to reduce OSRM routing overhead.
    Within each cell, prioritizes facilities with higher available asset counts or lower hourly rates.
    """
    hex_bins = group_candidates_by_h3(candidates, resolution=resolution)
    pruned: list[dict[str, Any]] = []

    for cell, items in hex_bins.items():
        sorted_items = sorted(
            items,
            key=lambda x: (
                -int(x.get("available_units", x.get("available_count", 1))),
                float(x.get("avg_hourly_rate", x.get("hourly_rate", 0)) or 0),
            ),
        )
        pruned.extend(sorted_items[:max_per_cell])

    return pruned

def get_h3_coverage_geojson(
    center_lat: float,
    center_lon: float,
    k_rings: int = 3,
    resolution: int = 7,
) -> dict[str, Any]:
    """
    Generates a GeoJSON FeatureCollection containing all H3 hex cells up to k_rings
    around the origin location. Used by MapLibre to display the reachability footprint.
    """
    center_cell = latlng_to_h3(center_lat, center_lon, resolution)
    cells = h3.grid_disk(center_cell, k_rings)

    features = []
    for cell in cells:
        distance_ring = h3.grid_distance(center_cell, cell)
        polygon = h3_to_geojson_polygon(cell)
        features.append({
            "type": "Feature",
            "properties": {
                "h3_index": cell,
                "ring": distance_ring,
                "is_center": (cell == center_cell),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon],
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }
