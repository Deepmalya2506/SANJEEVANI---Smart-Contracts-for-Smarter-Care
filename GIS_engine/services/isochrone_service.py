import math

def generate_circle(center_lat, center_lon, radius_km, points=36):
    """
    Generates a circular polygon around a point
    """

    coords = []

    for i in range(points):
        angle = 2 * math.pi * i / points

        dx = radius_km * math.cos(angle)
        dy = radius_km * math.sin(angle)

        # Rough conversion (valid for small areas)
        new_lat = center_lat + (dy / 111)
        new_lon = center_lon + (dx / (111 * math.cos(math.radians(center_lat))))

        coords.append([new_lon, new_lat])

    coords.append(coords[0])  # close polygon

    return {
        "type": "Polygon",
        "coordinates": [coords]
    }


def time_to_radius_km(minutes, avg_speed_kmph=30):
    """
    Convert time → distance
    """
    return (minutes / 60) * avg_speed_kmph