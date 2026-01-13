import json
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, status

SRC_BASE_URL = "https://hianimez.to"
SRC_AJAX_URL = f"{SRC_BASE_URL}/ajax"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

router = APIRouter(prefix="/api", tags=["Anime"])


async def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=10.0, headers=DEFAULT_HEADERS)


def _parse_sync_ids(html: str) -> dict[str, Optional[int]]:
    soup = BeautifulSoup(html, "html.parser")
    sync_el = soup.select_one("#syncData")
    if not sync_el or not sync_el.text:
        return {"anilistID": None, "malID": None}
    try:
        data = json.loads(sync_el.text)
        return {
            "anilistID": data.get("anilist_id"),
            "malID": data.get("mal_id"),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"anilistID": None, "malID": None}


def _safe_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "up and running"}


@router.get("/home")
async def home() -> dict[str, Any]:
    # Home endpoint is not critical for current UI flows.
    return {"data": {}}


@router.get("/schedule")
async def schedule(date: Optional[str] = Query(None)) -> dict[str, Any]:
    target_date = (
        date
        if date
        else datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    )
    async with await _get_client() as client:
        resp = await client.get(
            f"{SRC_AJAX_URL}/schedule/list",
            params={"tzOffset": -330, "date": target_date},
            headers={
                "Accept": "*/*",
                "Referer": SRC_BASE_URL,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        resp.raise_for_status()
        html = resp.json().get("html", "")

    soup = BeautifulSoup(html, "html.parser")
    items = []
    for el in soup.select("li"):
        time_el = el.select_one("a .time")
        anime_link = el.select_one("a")
        name_el = el.select_one(".film-name.dynamic-name")
        time_text = time_el.text.strip() if time_el else ""
        episode_button = el.select_one(".fd-play button")
        airing_ts = None
        seconds_until = None
        if time_text:
            try:
                airing_dt = datetime.fromisoformat(f"{target_date}T{time_text}:00")
                airing_ts = int(airing_dt.timestamp() * 1000)
                seconds_until = int(airing_dt.timestamp() - datetime.now().timestamp())
            except ValueError:
                airing_ts = None
                seconds_until = None
        items.append(
            {
                "id": anime_link.get("href", "").lstrip("/") if anime_link else None,
                "time": time_text or None,
                "name": name_el.text.strip() if name_el else None,
                "jname": name_el.get("data-jname") if name_el else None,
                "airingTimestamp": airing_ts or 0,
                "secondsUntilAiring": seconds_until or 0,
                "episode": _safe_int(
                    episode_button.get_text(strip=True).split(" ")[1]
                    if episode_button and " " in episode_button.get_text(strip=True)
                    else None
                )
                or 0,
            }
        )

    return {"data": {"scheduledAnimes": items}}


@router.get("/search")
async def search() -> dict[str, Any]:
    # The existing UI uses backend search endpoints; keep a placeholder.
    return {"data": []}


async def _search_suggestions(query: str) -> dict[str, Any]:
    async with await _get_client() as client:
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


@router.get("/search/suggestion")
async def search_suggestion(q: str = Query(...)) -> dict[str, Any]:
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query"
        )
    data = await _search_suggestions(q.strip())
    return {"data": data}


async def _fetch_episodes(anime_id: str) -> dict[str, Any]:
    episode_key = anime_id.split("-")[-1]
    async with await _get_client() as client:
        resp = await client.get(
            f"{SRC_AJAX_URL}/v2/episode/list/{episode_key}",
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{SRC_BASE_URL}/watch/{anime_id}",
            },
        )
        resp.raise_for_status()
        html = resp.json().get("html", "")

    soup = BeautifulSoup(html, "html.parser")
    episodes = []
    for link in soup.select(".detail-infor-content .ss-list a"):
        episodes.append(
            {
                "title": link.get("title"),
                "episodeId": (link.get("href") or "").split("/")[-1],
                "number": _safe_int(link.get("data-number")) or 0,
                "isFiller": "ssl-item-filler" in link.get("class", []),
            }
        )
    return {"totalEpisodes": len(episodes), "episodes": episodes}


@router.get("/anime/{anime_id}")
async def anime_info(anime_id: str) -> dict[str, Any]:
    async with await _get_client() as client:
        resp = await client.get(f"{SRC_BASE_URL}/{anime_id.lstrip('/')}")
        if resp.status_code >= 500:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream unavailable")
    ids = _parse_sync_ids(resp.text)
    title = None
    poster = None
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


@router.get("/anime/{anime_id}/episodes")
async def anime_episodes(anime_id: str) -> dict[str, Any]:
    data = await _fetch_episodes(anime_id)
    return {"data": data}


async def _parse_server_html(html: str, category: str, preferred: Optional[str]) -> tuple[Optional[int], dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    episode_no_el = soup.select_one(".server-notice strong")
    episode_no = episode_no_el.get_text(strip=True).split(" ").pop() if episode_no_el else ""
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
            server_id = _safe_int(item.get("data-server-id"))
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


@router.get("/episode/servers")
async def episode_servers(animeEpisodeId: str = Query(...)) -> dict[str, Any]:
    episode_id = animeEpisodeId
    if "?ep=" not in episode_id:
        episode_id = f"{episode_id}?ep={episode_id.split('-')[-1]}"
    ep_key = episode_id.split("?ep=")[1]
    async with await _get_client() as client:
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


@router.get("/episode/sources")
async def episode_sources(
    animeEpisodeId: str = Query(...),
    server: Optional[str] = Query(None),
    category: str = Query("sub"),
) -> dict[str, Any]:
    episode_id = animeEpisodeId
    if "?ep=" not in episode_id:
        episode_id = f"{episode_id}?ep={episode_id.split('-')[-1]}"
    ep_key = episode_id.split("?ep=")[1]

    async with await _get_client() as client:
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

    ids = _parse_sync_ids(watch_page.text)
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


@router.post("/import/{provider}")
async def import_provider(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    if provider != "anilist":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider"
        )

    anime_list = payload.get("animes") or []
    if not anime_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No anime list provided"
        )

    status_map = {
        "CURRENT": "watching",
        "COMPLETED": "completed",
        "PLANNING": "plan to watch",
        "DROPPED": "dropped",
        "PAUSED": "on hold",
        "REPEATING": "watching",
    }

    mapped = []
    for item in anime_list:
        entries = item.get("entries") or []
        for entry in entries:
            media = entry.get("media") or {}
            title_obj = media.get("title") or {}
            english_title = title_obj.get("english")
            if not english_title:
                continue
            try:
                suggestions = await _search_suggestions(english_title)
            except Exception:
                continue
            suggestions_list = suggestions.get("suggestions") or []
            if not suggestions_list:
                continue
            first = suggestions_list[0]
            mapped.append(
                {
                    "id": first.get("id"),
                    "thumbnail": first.get("poster"),
                    "title": first.get("name"),
                    "status": status_map.get(item.get("status"), "watching"),
                }
            )

    return {"animes": mapped}
