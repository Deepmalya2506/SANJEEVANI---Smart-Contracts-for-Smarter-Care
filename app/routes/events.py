import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from psycopg.rows import dict_row

from app.core.database import get_supabase_connection
from app.schemas.inventory import LoanLifecycleEvent

router = APIRouter()


@router.post("/api/v1/events/loan-created")
def handle_loan_created(event: LoanLifecycleEvent):
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            # Validate loan existence
            cursor.execute(
                """
                SELECT loan_id, asset_id, lender_hospital_id, borrower_hospital_id, loan_status
                FROM public.loans
                WHERE loan_id = %s
                FOR UPDATE
                """,
                (event.loan_id,),
            )
            loan = cursor.fetchone()
            if not loan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan record not found.")

            previous_status = loan["loan_status"]

            # 1. Update loan status
            cursor.execute(
                """
                UPDATE public.loans
                SET loan_status = 'APPROVED', updated_at = now()
                WHERE loan_id = %s
                """,
                (event.loan_id,),
            )

            # 2. Lock asset to RESERVED
            cursor.execute(
                """
                UPDATE public.equipment_assets
                SET availability_status = 'RESERVED', updated_at = now()
                WHERE asset_id = %s
                """,
                (loan["asset_id"],),
            )

            # 3. Append state event
            cursor.execute(
                """
                INSERT INTO public.loan_state_events (
                    event_id, loan_id, previous_state, new_state, actor_type, actor_id, source
                )
                VALUES (%s, %s, %s, 'APPROVED', 'SYSTEM', %s, 'api.events.loan_created')
                """,
                (uuid4(), event.loan_id, previous_status, event.actor_id),
            )

            # 4. Append audit event
            cursor.execute(
                """
                INSERT INTO public.activity_events (
                    activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                )
                VALUES (%s, %s, %s, 'LOAN', %s, 'loan.approved', %s)
                """,
                (
                    uuid4(),
                    loan["lender_hospital_id"],
                    event.actor_id or loan["borrower_hospital_id"],
                    event.loan_id,
                    json.dumps({"asset_id": str(loan["asset_id"]), "note": event.note}),
                ),
            )

            connection.commit()

    return {"status": "success", "loan_status": "APPROVED", "asset_status": "RESERVED"}


@router.post("/api/v1/events/delivery-confirmed")
def handle_delivery_confirmed(event: LoanLifecycleEvent):
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT loan_id, asset_id, lender_hospital_id, borrower_hospital_id, loan_status
                FROM public.loans
                WHERE loan_id = %s
                FOR UPDATE
                """,
                (event.loan_id,),
            )
            loan = cursor.fetchone()
            if not loan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan record not found.")

            previous_status = loan["loan_status"]

            # 1. Update loan to ACTIVE
            cursor.execute(
                """
                UPDATE public.loans
                SET loan_status = 'ACTIVE', updated_at = now()
                WHERE loan_id = %s
                """,
                (event.loan_id,),
            )

            # 2. Mark asset as ON_LOAN
            cursor.execute(
                """
                UPDATE public.equipment_assets
                SET availability_status = 'ON_LOAN', updated_at = now()
                WHERE asset_id = %s
                """,
                (loan["asset_id"],),
            )

            # 3. State transition event
            cursor.execute(
                """
                INSERT INTO public.loan_state_events (
                    event_id, loan_id, previous_state, new_state, actor_type, actor_id, source
                )
                VALUES (%s, %s, %s, 'ACTIVE', 'BORROWER', %s, 'api.events.delivery_confirmed')
                """,
                (uuid4(), event.loan_id, previous_status, event.actor_id),
            )

            # 4. Activity log
            cursor.execute(
                """
                INSERT INTO public.activity_events (
                    activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                )
                VALUES (%s, %s, %s, 'LOAN', %s, 'loan.activated', %s)
                """,
                (
                    uuid4(),
                    loan["borrower_hospital_id"],
                    event.actor_id or loan["borrower_hospital_id"],
                    event.loan_id,
                    json.dumps({"asset_id": str(loan["asset_id"]), "note": event.note}),
                ),
            )

            connection.commit()

    return {"status": "success", "loan_status": "ACTIVE", "asset_status": "ON_LOAN"}


@router.post("/api/v1/events/loan-settled")
def handle_loan_settled(event: LoanLifecycleEvent):
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT loan_id, asset_id, lender_hospital_id, borrower_hospital_id, loan_status
                FROM public.loans
                WHERE loan_id = %s
                FOR UPDATE
                """,
                (event.loan_id,),
            )
            loan = cursor.fetchone()
            if not loan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan record not found.")

            previous_status = loan["loan_status"]

            # 1. Update loan status to SETTLED
            cursor.execute(
                """
                UPDATE public.loans
                SET loan_status = 'SETTLED', updated_at = now()
                WHERE loan_id = %s
                """,
                (event.loan_id,),
            )

            # 2. Release asset back to marketplace as AVAILABLE
            cursor.execute(
                """
                UPDATE public.equipment_assets
                SET availability_status = 'AVAILABLE', updated_at = now()
                WHERE asset_id = %s
                """,
                (loan["asset_id"],),
            )

            # 3. State transition event
            cursor.execute(
                """
                INSERT INTO public.loan_state_events (
                    event_id, loan_id, previous_state, new_state, actor_type, actor_id, source
                )
                VALUES (%s, %s, %s, 'SETTLED', 'SYSTEM', %s, 'api.events.loan_settled')
                """,
                (uuid4(), event.loan_id, previous_status, event.actor_id),
            )

            # 4. Activity log
            cursor.execute(
                """
                INSERT INTO public.activity_events (
                    activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                )
                VALUES (%s, %s, %s, 'LOAN', %s, 'loan.settled', %s)
                """,
                (
                    uuid4(),
                    loan["lender_hospital_id"],
                    event.actor_id or loan["lender_hospital_id"],
                    event.loan_id,
                    json.dumps({"asset_id": str(loan["asset_id"]), "note": event.note}),
                ),
            )

            connection.commit()

    return {"status": "success", "loan_status": "SETTLED", "asset_status": "AVAILABLE"}