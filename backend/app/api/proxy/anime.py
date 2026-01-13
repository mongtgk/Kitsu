from typing import Any

from bs4 import BeautifulSoup
import httpx
from fastapi import APIRouter, HTTPException, status

from .common import SRC_AJAX_URL, SRC_BASE_URL, get_client, parse_sync_ids, safe_int

router = APIRouter(prefix="/anime", tags=["Anime"])


async def _fetch_episodes(anime_id: str) -> dict[str, Any]:
    episode_key = anime_id.split("-")[-1]
    try:
        async with await get_client() as client:
            resp = await client.get(
                f"{SRC_AJAX_URL}/v2/episode/list/{episode_key}",
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{SRC_BASE_URL}/watch/{anime_id}",
                },
            )
            resp.raise_for_status()
            html = resp.json().get("html", "")
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if 500 <= status_code < 600:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Upstream service unavailable",
            ) from exc
        raise HTTPException(
            status_code=status_code, detail="Upstream request was rejected"
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream service unavailable",
        ) from exc

    soup = BeautifulSoup(html, "html.parser")
    episodes = []
    for link in soup.select(".detail-infor-content .ss-list a"):
        episodes.append(
            {
                "title": link.get("title"),
                "episodeId": (link.get("href") or "").split("/")[-1],
                "number": safe_int(link.get("data-number")) or 0,
                "isFiller": "ssl-item-filler" in link.get("class", []),
            }
        )
    return {"totalEpisodes": len(episodes), "episodes": episodes}


@router.get("/{anime_id}")
async def anime_info(anime_id: str) -> dict[str, Any]:
    try:
        async with await get_client() as client:
            resp = await client.get(f"{SRC_BASE_URL}/{anime_id.lstrip('/')}")
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if 500 <= status_code < 600:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Upstream service unavailable",
            ) from exc
        raise HTTPException(
            status_code=status_code, detail="Upstream request was rejected"
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream service unavailable",
        ) from exc

    ids = parse_sync_ids(resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")
    title_el = soup.select_one(".film-name.dynamic-name") or soup.select_one("title")
    poster_el = soup.select_one(".film-poster-img")
    description_el = soup.select_one(".film-description .text")
    return {
        "data": {
            "id": anime_id,
            "title": title_el.text.strip() if title_el else anime_id,
            "poster": poster_el.get("src") if poster_el else None,
            "description": description_el.text.strip() if description_el else "",
            "anilistID": ids["anilistID"],
            "malID": ids["malID"],
        }
    }


@router.get("/{anime_id}/episodes")
async def anime_episodes(anime_id: str) -> dict[str, Any]:
    data = await _fetch_episodes(anime_id)
    return {"data": data}
