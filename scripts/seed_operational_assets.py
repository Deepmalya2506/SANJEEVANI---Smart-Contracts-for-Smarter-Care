import uuid
from app.core.database import get_supabase_connection
from psycopg.rows import dict_row

def seed_assets():
    conn = get_supabase_connection()
    cur = conn.cursor(row_factory=dict_row)

    cur.execute("SELECT hospital_id, hospital_name, mvp_hfr_id FROM public.hospitals")
    hospitals = cur.fetchall()

    equipment_templates = [
        ("Oxygen concentrator", "Philips EverFlo 5L", "SN-O2-", 120.0),
        ("Portable ventilator", "Hamilton-T1 Transport Ventilator", "SN-VN-", 350.0),
        ("Patient monitor", "Mindray BeneVision N12", "SN-PM-", 80.0),
        ("Infusion pump", "B. Braun Space Infusion Pump", "SN-IP-", 45.0),
    ]

    inserted = 0
    for h in hospitals:
        cur.execute("SELECT latitude, longitude FROM public.abdm_mock_hfr WHERE mvp_hfr_id = %s", (h["mvp_hfr_id"],))
        loc = cur.fetchone()
        lat = float(loc["latitude"]) if loc and loc["latitude"] else 11.6358
        lon = float(loc["longitude"]) if loc and loc["longitude"] else 92.7121

        for eq_type, model_name, sn_prefix, rate in equipment_templates:
            # Check if this hospital already has an available asset of this type
            cur.execute(
                "SELECT asset_id FROM public.equipment_assets WHERE hospital_id = %s AND equipment_type = %s",
                (h["hospital_id"], eq_type)
            )
            if cur.fetchone() is not None:
                continue

            asset_id = uuid.uuid4()
            full_name = f"{h['hospital_name']} {model_name}"
            sn = f"{sn_prefix}{uuid.uuid4().hex[:6].upper()}"

            cur.execute("""
                INSERT INTO public.equipment_assets (
                    asset_id, hospital_id, equipment_type, name, serial_number,
                    condition_status, availability_status, shareable, location, hourly_rate, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    'OPERATIONAL', 'AVAILABLE', true,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s, now(), now()
                )
            """, (asset_id, h["hospital_id"], eq_type, full_name, sn, lon, lat, rate))
            inserted += 1

    conn.commit()
    print(f"Successfully seeded {inserted} equipment assets into Supabase across {len(hospitals)} hospitals.")
    conn.close()

if __name__ == "__main__":
    seed_assets()
