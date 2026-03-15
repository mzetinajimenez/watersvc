"""Water intake CRUD API routes."""

from datetime import datetime
from zoneinfo import ZoneInfo

from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from watersvc.database.connection import get_database
from watersvc.database.service import WaterIntakeService
from watersvc.utils.conversions import convert_from_oz, convert_to_oz
from watersvc.utils.schemas import (
    CreateIntakeRequest,
    IntakeResponse,
    UpdateIntakeRequest,
    WaterIntakeDocument,
)
from watersvc.utils.timezone import get_local_date_time

router = APIRouter()


async def get_user_prefs(db: AsyncIOMotorDatabase, user_id: str) -> tuple[str, str]:
    """Get user timezone and preferred_unit from profile. Returns (timezone, preferred_unit)."""
    service = WaterIntakeService(db)
    profile = await service.get_profile(user_id)
    prefs = profile.get("preferences", {}) if profile else {}
    return prefs.get("timezone", "UTC"), prefs.get("preferred_unit", "oz")


def build_intake_response(intake: dict, preferred_unit: str) -> IntakeResponse:
    """Build IntakeResponse with display_amount in the preferred unit."""
    if intake["original_unit"] == preferred_unit:
        display_amount = intake["original_amount"]
    else:
        display_amount = convert_from_oz(intake["amount_oz"], preferred_unit)
    return IntakeResponse(
        id=str(intake["_id"]),
        display_amount=round(display_amount, 4),
        display_unit=preferred_unit,
        **{k: v for k, v in intake.items() if k != "_id"},
    )


@router.post("/intakes", response_model=IntakeResponse, status_code=201)
async def create_intake(
    request: CreateIntakeRequest,
    user_id: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a new water intake entry.

    Converts the amount to ounces for storage and calculates
    local date/time based on user's timezone preference.
    """
    service = WaterIntakeService(db)
    tz, preferred_unit = await get_user_prefs(db, user_id)

    timestamp = datetime.now(tz=ZoneInfo("UTC"))

    # Convert amount to ounces
    amount_oz = convert_to_oz(request.amount, request.unit)

    # Calculate local date and time
    local_date, local_time = get_local_date_time(timestamp, tz)

    # Create intake document
    intake_data = WaterIntakeDocument(
        user_id=user_id,
        amount_oz=amount_oz,
        original_amount=request.amount,
        original_unit=request.unit,
        timestamp=timestamp,
        local_date=local_date,
        local_time=local_time,
        timezone=tz,
        notes=request.notes,
    )

    # Insert into database
    created_intake = await service.create_intake(intake_data.model_dump())

    return build_intake_response(created_intake, preferred_unit)


@router.get("/intakes", response_model=list[IntakeResponse])
async def list_intakes(
    user_id: str = Query(...),
    date: str | None = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
    start_date: str | None = Query(None, description="Filter by date range start"),
    end_date: str | None = Query(None, description="Filter by date range end"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List water intake entries with optional filtering.

    Supports filtering by specific date or date range, with pagination.
    """
    service = WaterIntakeService(db)
    _, preferred_unit = await get_user_prefs(db, user_id)

    intakes = await service.list_intakes(
        user_id=user_id,
        local_date=date,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return [build_intake_response(intake, preferred_unit) for intake in intakes]


@router.get("/intakes/{intake_id}", response_model=IntakeResponse)
async def get_intake(
    intake_id: str,
    user_id: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get a specific water intake entry by ID."""
    service = WaterIntakeService(db)
    _, preferred_unit = await get_user_prefs(db, user_id)

    try:
        intake = await service.get_intake(intake_id, user_id)
    except InvalidId as err:
        raise HTTPException(status_code=400, detail="Invalid intake ID format") from err

    if not intake:
        raise HTTPException(status_code=404, detail="Intake entry not found")

    return build_intake_response(intake, preferred_unit)


@router.patch("/intakes/{intake_id}", response_model=IntakeResponse)
async def update_intake_partial(
    intake_id: str,
    request: UpdateIntakeRequest,
    user_id: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update a water intake entry (partial update).

    Updates only the provided fields, leaving others unchanged.
    """
    service = WaterIntakeService(db)
    _, preferred_unit = await get_user_prefs(db, user_id)

    # Check if intake exists
    try:
        existing_intake = await service.get_intake(intake_id, user_id)
    except InvalidId as err:
        raise HTTPException(status_code=400, detail="Invalid intake ID format") from err

    if not existing_intake:
        raise HTTPException(status_code=404, detail="Intake entry not found")

    # Build update data with only provided fields
    update_data: dict[str, object] = {}

    # If amount or unit is provided, recalculate amount_oz
    if request.amount is not None or request.unit is not None:
        amount = (
            request.amount if request.amount is not None else existing_intake["original_amount"]
        )
        unit = request.unit if request.unit is not None else existing_intake["original_unit"]
        update_data["amount_oz"] = convert_to_oz(amount, unit)
        update_data["original_amount"] = amount
        update_data["original_unit"] = unit

    if request.notes is not None:
        update_data["notes"] = request.notes

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    updated_intake = await service.update_intake(intake_id, update_data, user_id)
    if not updated_intake:
        raise HTTPException(status_code=500, detail="Failed to update intake")

    return build_intake_response(updated_intake, preferred_unit)


@router.delete("/intakes/{intake_id}", status_code=204)
async def delete_intake(
    intake_id: str,
    user_id: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Delete a water intake entry."""
    service = WaterIntakeService(db)

    try:
        deleted = await service.delete_intake(intake_id, user_id)
    except InvalidId as err:
        raise HTTPException(status_code=400, detail="Invalid intake ID format") from err

    if not deleted:
        raise HTTPException(status_code=404, detail="Intake entry not found")

    return None
