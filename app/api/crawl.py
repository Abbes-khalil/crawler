import asyncio

from fastapi import APIRouter

from app.crawler.orchestrator import crawl_company
from app.models.request import CrawlCompanyRequest
from app.models.response import CrawlCompanyResponse
from app.storage import persist_crawl_result


router = APIRouter()


@router.post(
    "/crawl-company",
    response_model=CrawlCompanyResponse,
)
async def crawl_company_endpoint(
    request: CrawlCompanyRequest,
):
    response = await crawl_company(
        website=request.website,
        max_pages=request.max_pages,
    )

    await asyncio.to_thread(persist_crawl_result, response)

    return response
