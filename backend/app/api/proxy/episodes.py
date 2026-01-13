from typing import Any, Optional

from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, status

from .common import (
    SRC_AJAX_URL,
    SRC_BASE_URL,
    get_client,
    parse_sync_ids,
    safe_int,
)

router = APIRouter(prefix="/episode", tags=["Episodes"])


async def _parse_server_html(
    html: str, category: str, preferred: Optional[str]
) -> tuple[Optional[int], dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    episode_no_el = soup.select_one(".server-notice strong")
    episode_text = episode_no_el.get_text(strip=True) if episode_no_el else ""
    parts = episode_text.split(" ") if episode_text else []
    episode_no = next(reversed(parts), "")
    result = {
        "episodeId": "",
        "episodeNo": episode_no,
        "sub": [],
        "dub": [],
        "raw": [],
    }
    mapping = [
        ("servers-sub", "sub"),
        ("servers-dub", "dub"),
        ("servers-raw", "raw"),
    ]
    for cls, key in mapping:
        container = soup.select_one(f".ps_-block.{cls} .ps__-list") or soup.select_one(
            f".ps_-block.{cls}"
        )
        if not container:
            continue
        for item in container.select(".server-item"):
            server_id = safe_int(item.get("data-server-id"))
            server_name = (item.get_text() or "").strip().lower()
            result[key].append({"serverId": server_id, "serverName": server_name})

    target_list = result.get(category, []) or result.get("sub", [])
    chosen_id = None
    if preferred:
        preferred_lower = preferred.lower()
        for srv in target_list:
            if srv["serverName"] == preferred_lower:
                chosen_id = srv["serverId"]
                break
    if chosen_id is None and target_list:
        chosen_id = target_list[0]["serverId"]
    return chosen_id, result


@router.get("/servers")
async def episode_servers(animeEpisodeId: str = Query(...)) -> dict[str, Any]:
    episode_id = animeEpisodeId
    if "?ep=" not in episode_id:
        episode_id = f"{episode_id}?ep={episode_id.split('-')[-1]}"
    ep_key = episode_id.split("?ep=")[1]
    async with await get_client() as client:
        resp = await client.get(
            f"{SRC_AJAX_URL}/v2/episode/servers",
            params={"episodeId": ep_key},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{SRC_BASE_URL}/watch/{episode_id}",
            },
        )
        resp.raise_for_status()
        html = resp.json().get("html", "")

    _, parsed = await _parse_server_html(html, "sub", preferred=None)
    parsed["episodeId"] = episode_id
    return {"data": parsed}


@router.get("/sources")
async def episode_sources(
    animeEpisodeId: str = Query(...),
    server: Optional[str] = Query(None),
    category: str = Query("sub"),
) -> dict[str, Any]:
    episode_id = animeEpisodeId
    if "?ep=" not in episode_id:
        episode_id = f"{episode_id}?ep={episode_id.split('-')[-1]}"
    ep_key = episode_id.split("?ep=")[1]

    async with await get_client() as client:
        servers_resp = await client.get(
            f"{SRC_AJAX_URL}/v2/episode/servers",
            params={"episodeId": ep_key},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{SRC_BASE_URL}/watch/{episode_id}",
            },
        )
        servers_resp.raise_for_status()
        servers_html = servers_resp.json().get("html", "")

        server_id, parsed_servers = await _parse_server_html(
            servers_html, category or "sub", preferred=server
        )
        if not server_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No server found for requested episode",
            )
        source_resp = await client.get(
            f"{SRC_AJAX_URL}/v2/episode/sources",
            params={"id": server_id},
        )
        source_resp.raise_for_status()
        source_link = source_resp.json().get("link")

        watch_page = await client.get(
            f"{SRC_BASE_URL}/watch/{episode_id.split('?')[0]}",
            headers={"Referer": SRC_BASE_URL},
        )

    ids = parse_sync_ids(watch_page.text)
    payload = {
        "headers": {"Referer": SRC_BASE_URL},
        "tracks": [],
        "intro": {"start": 0, "end": 0},
        "outro": {"start": 0, "end": 0},
        "sources": (
            [{"url": source_link, "type": "iframe"}] if source_link else []
        ),
        "anilistID": ids["anilistID"],
        "malID": ids["malID"],
    }
    return {"data": payload}
