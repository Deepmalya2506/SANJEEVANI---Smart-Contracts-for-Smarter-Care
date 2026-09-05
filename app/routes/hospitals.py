from fastapi import APIRouter
from app.core.database import get_supabase_connection, hospital_collection
from app.schemas.hospital import HFRVerificationRequest, HFRVerificationResponse, HospitalCreate
from psycopg.rows import tuple_row

router = APIRouter()


@router.post("/api/v1/facilities/verify-signup", response_model=HFRVerificationResponse)
def verify_hfr_id(data: HFRVerificationRequest):
    with get_supabase_connection() as connection:
        connection.row_factory = tuple_row
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select mvp_hfr_id, hospital_name
                from public.abdm_mock_hfr
                where mvp_hfr_id = %s
                """,
                (data.mvp_hfr_id,),
            )
            record = cursor.fetchone()

    if record is None:
        return HFRVerificationResponse(
            verified=False,
            directory_match=False,
            mvp_hfr_id=data.mvp_hfr_id,
            hospital_name=data.hospital_name,
            message="No hospital found with this HFR ID.",
        )

    mvp_hfr_id, hospital_name = record
    names_match = hospital_name is not None and hospital_name.strip().casefold() == data.hospital_name.strip().casefold()
    if not names_match:
        return HFRVerificationResponse(
            verified=False,
            directory_match=True,
            mvp_hfr_id=mvp_hfr_id,
            hospital_name=hospital_name,
            message="Enter correct credentials for Verification...",
        )

    return HFRVerificationResponse(
        verified=True,
        directory_match=True,
        mvp_hfr_id=mvp_hfr_id,
        hospital_name=hospital_name,
        message="Facility verified. Continue registration.",
    )

@router.post("/hospitals")
def create_hospital(data: HospitalCreate):
    hospital_collection.insert_one(data.model_dump())
    return {"message": "Hospital created"}

@router.get("/hospitals")
def get_hospitals():
    hospitals = list(hospital_collection.find({}, {"_id": 0}))
    return hospitals

@router.get("/hospitals/{hospital_id}")
def get_hospital(hospital_id: str):
    hospital = hospital_collection.find_one({"id": hospital_id}, {"_id": 0})
    return hospital