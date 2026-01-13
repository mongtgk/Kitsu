from typing import Any

from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, status

from .common import SRC_AJAX_URL, SRC_BASE_URL, get_client

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search() -> dict[str, Any]:
    # The existing UI uses backend search endpoints; keep a placeholder.
    return {"data": []}


async def fetch_search_suggestions(query: str) -> dict[str, Any]:
    async with await get_client() as client:
        resp = await client.get(
            f"{SRC_AJAX_URL}/search/suggest",
            params={"keyword": query},
            headers={
                "Accept": "*/*",
                "Referer": SRC_BASE_URL,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        resp.raise_for_status()
        html = resp.json().get("html", "")
    soup = BeautifulSoup(html, "html.parser")
    suggestions = []
    for item in soup.select(".nav-item"):
        link = item.get("href", "")
        if "javascript" in link:
            continue
        suggestions.append(
            {
                "id": link.split("?")[0].lstrip("/"),
                "name": (item.select_one(".film-name") or {}).get_text(strip=True),
                "jname": (item.select_one(".film-name") or {}).get("data-jname"),
                "poster": (item.select_one(".film-poster-img") or {}).get(
                    "data-src"
                ),
                "moreInfo": [
                    text.strip()
                    for text in item.select_one(".film-infor").stripped_strings
                ]
                if item.select_one(".film-infor")
                else [],
            }
        )
    return {"suggestions": suggestions}


@router.get("/suggestion")
async def search_suggestion(q: str = Query(...)) -> dict[str, Any]:
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query"
        )
    data = await fetch_search_suggestions(q.strip())
    return {"data": data}
