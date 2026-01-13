from datetime import datetime, timezone
from typing import Any, Optional

from bs4 import BeautifulSoup
from fastapi import APIRouter, Query

from .common import SRC_AJAX_URL, SRC_BASE_URL, get_client, safe_int

router = APIRouter(tags=["Schedule"])


@router.get("/home")
async def home() -> dict[str, Any]:
    # Home endpoint is not critical for current UI flows.
    return {"data": {}}


@router.get("/schedule")
async def schedule(date: Optional[str] = Query(None)) -> dict[str, Any]:
    target_date = date or datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    async with await get_client() as client:
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
        episode_button_text = (
            episode_button.get_text(strip=True) if episode_button else ""
        )
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
                "episode": safe_int(
                    episode_button_text.split(" ")[1]
                    if episode_button_text and " " in episode_button_text
                    else None
                )
                or 0,
            }
        )

    return {"data": {"scheduledAnimes": items}}
