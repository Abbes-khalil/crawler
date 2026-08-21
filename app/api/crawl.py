from fastapi import APIRouter

from app.crawler.orchestrator import crawl_company
from app.models.request import CrawlCompanyRequest
from app.models.response import CrawlCompanyResponse


router = APIRouter()


@router.post(
    "/crawl-company",
    response_model=CrawlCompanyResponse,
)
async def crawl_company_endpoint(
    request: CrawlCompanyRequest,
):
    return await crawl_company(
        website=str(request.website),
        max_pages=request.max_pages,
    )