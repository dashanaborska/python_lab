import asyncio
import json
import sys
from typing import Any

import httpx

from sport_results.config import get_settings


def show(method: str, url: str, response: httpx.Response, body: Any = None) -> None:
    print(f"\n>>> {method} {url}")
    if body is not None:
        print(json.dumps(body, ensure_ascii=False))
    print(f"<<< {response.status_code} {response.reason_phrase}")
    if response.content:
        text = json.dumps(response.json(), ensure_ascii=False, indent=2)
        lines = text.splitlines()
        print("\n".join(lines[:14] + (["  ..."] if len(lines) > 14 else [])))


async def demo(base_url: str) -> None:
    async with httpx.AsyncClient(base_url=base_url, timeout=5) as client:
        calls: list[tuple[str, str, Any]] = [
            ("GET", "/api/v1/athletes?sport=Плавання&limit=2", None),
            (
                "POST",
                "/api/v1/athletes",
                {"name": "Наталія Мороз", "sport": "Плавання", "category": "МС"},
            ),
            (
                "POST",
                "/api/v1/results",
                {"athlete_id": 8, "score": 93.4, "competition_name": "Кубок Києва"},
            ),
            ("PATCH", "/api/v1/results/9", {"score": 94.0}),
            ("GET", "/api/v1/sports/1/ranking", None),
            ("DELETE", "/api/v1/results/9", None),
            ("POST", "/api/v1/results", {"athlete_id": 1, "score": 120}),
            ("GET", "/api/v1/sports/99/results", None),
        ]
        for method, url, body in calls:
            response = await client.request(method, url, json=body)
            show(method, url, response, body)
        url = "/api/v1/rankings?sport_id=1&sport_id=2&sport_id=3&sport_id=99"
        response = await client.get(url)
        print(f"\n>>> GET {url}")
        print(f"<<< {response.status_code} {response.reason_phrase}")
        data = response.json()
        for ranking in data["rankings"]:
            leader = ranking["ranking"][0]
            print(
                f"  {ranking['sport']:16}лідер: {leader['athlete']} "
                f"({leader['best']}), учасників: {len(ranking['ranking'])}"
            )
        print(f"  failed: {data['failed']}  elapsed: {data['elapsed']} s")


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else get_settings().api_base_url
    asyncio.run(demo(base_url))


if __name__ == "__main__":
    main()
