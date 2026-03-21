import folium

def create_route_map(geometry):
    """
    geometry: GeoJSON LineString
    """

    coords = geometry["coordinates"]

    # Convert (lon, lat) → (lat, lon)
    lat_lon_coords = [(lat, lon) for lon, lat in coords]

    # Center map at first point
    start = lat_lon_coords[0]

    m = folium.Map(location=start, zoom_start=14)

    # Draw route
    folium.PolyLine(
        lat_lon_coords,
        color="blue",
        weight=5,
        opacity=0.8
    ).add_to(m)

    # Mark start & end
    folium.Marker(lat_lon_coords[0], tooltip="Start").add_to(m)
    folium.Marker(lat_lon_coords[-1], tooltip="Destination").add_to(m)

    return m