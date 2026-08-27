from fastapi import APIRouter, HTTPException

from app.storage.db import get_session
from app.storage.results import get_result, list_results

router = APIRouter(prefix="/api")


@router.get("/results")
async def results():
    session = get_session()
    try:
        return list_results(session)
    finally:
        session.close()


@router.get("/results/{company_id}")
async def result_detail(company_id: int):
    session = get_session()
    try:
        data = get_result(session, company_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Result not found")
        return data
    finally:
        session.close()
