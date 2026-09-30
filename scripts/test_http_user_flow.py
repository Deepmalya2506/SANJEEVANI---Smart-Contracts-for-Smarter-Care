"""
SANJEEVANI — End-to-End HTTP API & Supabase DB Verification:
Tests the exact 4 user requirements via live HTTP API calls and Supabase verification:
  1. Register as hospital admin of a new hospital
  2. Register equipment in that hospital
  3. Borrow equipment from another hospital to my hospital
  4. Verify all data is created and extracted from Supabase DB
"""

import sys
import os
from uuid import uuid4, UUID
import requests

sys.path.insert(0, os.path.abspath("."))
from app.core.database import get_supabase_connection

BASE_URL = "http://127.0.0.1:8000"

def banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)

def main():
    banner("[LIVE HTTP API & SUPABASE DB] USER WORKFLOW TEST")

    # -------------------------------------------------------------------------
    # 1. Register as Hospital Admin of New Hospital
    # -------------------------------------------------------------------------
    banner("1. Register as Hospital Admin of New Hospital")
    suffix = uuid4().hex[:6].upper()
    hosp_name = f"Fortis Care Hospital {suffix}"
    admin_name = f"Dr. Ananya Roy {suffix}"
    admin_email = f"ananya_{suffix.lower()}@fortis.health"
    hfr_id = f"HFR_FORTIS_{suffix}"

    reg_payload = {
        "admin_name": admin_name,
        "email": admin_email,
        "hospital_name": hosp_name,
        "mvp_hfr_id": hfr_id,
        "latitude": 22.5180,
        "longitude": 88.3527,
        "address": "South Kolkata Healthcare Hub"
    }

    resp = requests.post(f"{BASE_URL}/hospitals", json=reg_payload, timeout=10)
    print(f"  POST /hospitals: HTTP {resp.status_code}")
    assert resp.status_code == 201, f"Failed registration: {resp.text}"
    reg_data = resp.json()
    my_hospital_id = reg_data["hospital_id"]
    my_user_id = reg_data["user_id"]
    print(f"  [SUCCESS] Hospital Registered!")
    print(f"      Hospital ID:   {my_hospital_id}")
    print(f"      Hospital Name: {reg_data['hospital_name']}")
    print(f"      Admin User ID: {my_user_id}")
    print(f"      Admin Email:   {reg_data['admin_email']}")

    # -------------------------------------------------------------------------
    # 2. Register Equipment in that Hospital
    # -------------------------------------------------------------------------
    banner("2. Register Equipment in that Hospital")
    eq_payload = {
        "hospital_id": my_hospital_id,
        "equipment_type": "Infusion pump",
        "name": "B. Braun Infusomat Space Pump",
        "serial_number": f"SN-INF-{suffix}",
        "condition_status": "OPERATIONAL",
        "shareable": True,
        "hourly_rate": 180.0,
        "latitude": 22.5180,
        "longitude": 88.3527,
        "metadata": {"flow_rate": "0.1-1200 ml/h", "battery_hours": 12}
    }

    resp = requests.post(f"{BASE_URL}/equipment/register", json=eq_payload, timeout=10)
    print(f"  POST /equipment/register: HTTP {resp.status_code}")
    assert resp.status_code == 201, f"Failed equipment registration: {resp.text}"
    eq_data = resp.json()
    my_asset_id = eq_data["asset_id"]
    print(f"  [SUCCESS] Equipment Asset Registered!")
    print(f"      Asset ID:       {my_asset_id}")
    print(f"      Equipment Name: {eq_data['name']}")
    print(f"      Equipment Type: {eq_data['equipment_type']}")
    print(f"      Status:         {eq_data['availability_status']}")
    print(f"      Hourly Rate:    Rs {eq_data['hourly_rate']}")

    # -------------------------------------------------------------------------
    # 3. Borrow Equipment from Other Hospitals to My Hospital
    # -------------------------------------------------------------------------
    banner("3. Borrow Equipment from Other Hospitals to My Hospital")

    # Discover lender hospital nearby or in network via GET /hospitals
    hosps_resp = requests.get(f"{BASE_URL}/hospitals", timeout=10)
    assert hosps_resp.status_code == 200, "Failed to list hospitals"
    other_hospitals = [h for h in hosps_resp.json() if h["id"] != my_hospital_id]
    assert len(other_hospitals) > 0, "No other registered hospital found to borrow from!"
    lender_hosp = other_hospitals[0]
    lender_id = lender_hosp["id"]
    lender_name = lender_hosp["name"]

    print(f"  [LENDER SELECTED]")
    print(f"      Lender Hospital: {lender_name} ({lender_id})")
    print(f"      Borrowing To:    {hosp_name} ({my_hospital_id})")

    sanction_payload = {
        "borrower_hospital_id": my_hospital_id,
        "lender_hospital_id": lender_id,
        "equipment_type": "Oxygen concentrator",
        "borrower_admin_email": admin_email,
        "duration_hours": 24,
        "amount_rupees": 2400.0,
        "notes": {
            "purpose": "ICU Bed 12 Supplemental Oxygenation",
            "borrower": hosp_name,
            "lender": lender_name,
        }
    }

    resp = requests.post(f"{BASE_URL}/api/v1/transactions/sanction", json=sanction_payload, timeout=20)
    print(f"  POST /api/v1/transactions/sanction: HTTP {resp.status_code}")
    assert resp.status_code == 200, f"Failed sanctioning transaction: {resp.text}"
    sanction_data = resp.json()
    loan_id = sanction_data["loan_id"]
    order_id = sanction_data["order_id"]
    locked_asset_id = sanction_data["asset_id"]

    print(f"  [SUCCESS] Equipment Loan Sanctioned!")
    print(f"      Loan ID:           {loan_id}")
    print(f"      Order ID:          {order_id}")
    print(f"      Locked Asset ID:   {locked_asset_id}")
    print(f"      Loan Status:       {sanction_data['loan_status']}")
    print(f"      Asset Lock Status: {sanction_data['asset_status']}")
    print(f"      Amount:            Rs {sanction_data['amount_rupees']} == {sanction_data['amount_paise']} paise")

    # Complete payment authorization
    pay_id = f"pay_test_{uuid4().hex[:10]}"
    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": pay_id,
                    "order_id": order_id,
                    "amount": sanction_data["amount_paise"],
                    "currency": "INR",
                    "status": "captured",
                    "email": admin_email
                }
            }
        }
    }
    from app.services.razorpay_client import apply_webhook
    webhook_res = apply_webhook(webhook_payload)
    print(f"  [PAYMENT CAPTURED] Status: {webhook_res['status']}")

    # -------------------------------------------------------------------------
    # 4. Extract and Verify All Data Created Directly from Supabase DB
    # -------------------------------------------------------------------------
    banner("4. Verify All Data Created & Extracted Directly from Supabase DB")

    conn = get_supabase_connection()
    with conn.cursor() as cur:
        # Check public.hospitals
        cur.execute("SELECT hospital_id, hospital_name, mvp_hfr_id, profile_status FROM public.hospitals WHERE hospital_id = %s", (my_hospital_id,))
        hosp_db = cur.fetchone()
        assert hosp_db is not None, "Hospital not found in Supabase DB!"
        print(f"  [OK] public.hospitals:")
        print(f"       ID: {hosp_db[0]} | Name: {hosp_db[1]} | HFR: {hosp_db[2]} | Status: {hosp_db[3]}")

        # Check public.users
        cur.execute("SELECT user_id, auth_user_id, admin_name, user_mail, profile_completed FROM public.users WHERE hospital_id = %s", (my_hospital_id,))
        user_db = cur.fetchone()
        assert user_db is not None, "Admin user not found in Supabase DB!"
        print(f"  [OK] public.users:")
        print(f"       User ID: {user_db[0]} | Auth User: {user_db[1]} | Name: {user_db[2]} | Email: {user_db[3]}")

        # Check public.equipment_assets (my hospital's registered equipment)
        cur.execute("SELECT asset_id, name, equipment_type, serial_number, availability_status, hourly_rate FROM public.equipment_assets WHERE hospital_id = %s", (my_hospital_id,))
        eq_db = cur.fetchone()
        assert eq_db is not None, "My hospital equipment asset not found in Supabase DB!"
        print(f"  [OK] public.equipment_assets (Registered Asset):")
        print(f"       Asset ID: {eq_db[0]} | Name: {eq_db[1]} | Type: {eq_db[2]} | SN: {eq_db[3]} | Status: {eq_db[4]} | Rate: Rs {eq_db[5]}")

        # Check public.equipment_assets (borrowed equipment state)
        cur.execute("SELECT asset_id, name, availability_status FROM public.equipment_assets WHERE asset_id = %s", (locked_asset_id,))
        borrowed_asset_db = cur.fetchone()
        assert borrowed_asset_db is not None, "Borrowed asset not found in Supabase DB!"
        assert borrowed_asset_db[2] == "ON_LOAN", f"Borrowed asset status should be ON_LOAN, found: {borrowed_asset_db[2]}"
        print(f"  [OK] public.equipment_assets (Borrowed Asset):")
        print(f"       Asset ID: {borrowed_asset_db[0]} | Name: {borrowed_asset_db[1]} | Status: {borrowed_asset_db[2]} (ON_LOAN)")

        # Check public.loans
        cur.execute("SELECT loan_id, asset_id, borrower_hospital_id, lender_hospital_id, loan_status, amount FROM public.loans WHERE loan_id = %s", (loan_id,))
        loan_db = cur.fetchone()
        assert loan_db is not None, "Loan record not found in Supabase DB!"
        assert loan_db[4] == "ACTIVE", f"Loan status should be ACTIVE, found: {loan_db[4]}"
        print(f"  [OK] public.loans:")
        print(f"       Loan ID: {loan_db[0]} | Status: {loan_db[4]} | Amount: Rs {loan_db[5]}")

        # Check public.payments
        cur.execute("SELECT payment_id, order_id, status, amount_rupees, amount_paise FROM public.payments WHERE order_id = %s", (order_id,))
        pay_db = cur.fetchone()
        assert pay_db is not None, "Payment record not found in Supabase DB!"
        assert pay_db[2] == "PAYMENT_CAPTURED", f"Payment status should be PAYMENT_CAPTURED, found: {pay_db[2]}"
        print(f"  [OK] public.payments:")
        print(f"       Payment ID: {pay_db[0]} | Order ID: {pay_db[1]} | Status: {pay_db[2]} | Amount: Rs {pay_db[3]} ({pay_db[4]} paise)")

        # Check public.loan_state_events
        cur.execute("SELECT event_id, previous_state, new_state, actor_type, source FROM public.loan_state_events WHERE loan_id = %s", (loan_id,))
        events_db = cur.fetchall()
        print(f"  [OK] public.loan_state_events:")
        for ev in events_db:
            print(f"       Event ID: {ev[0]} | {ev[1]} => {ev[2]} | Actor: {ev[3]} | Source: {ev[4]}")

        # Check public.notifications
        cur.execute("SELECT notification_id, channel, type, status FROM public.notifications WHERE hospital_id = %s OR loan_id = %s", (my_hospital_id, loan_id))
        notifs_db = cur.fetchall()
        print(f"  [OK] public.notifications ({len(notifs_db)} logged notifications):")
        for n in notifs_db:
            print(f"       Notification ID: {n[0]} | Channel: {n[1]} | Type: {n[2]} | Status: {n[3]}")

    conn.close()

    banner("[ALL 4 CRITERIA PASSED AND VALIDATED FROM SUPABASE DB]")

if __name__ == "__main__":
    main()
