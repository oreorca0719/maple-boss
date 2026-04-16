"""
넥슨 메이플스토리 오픈 API 클라이언트.

maplestory-openapi 라이브러리 대신 httpx로 직접 호출.
(Python 3.13 호환성 문제 우회 + 의존성 단순화)

Rate Limit: Semaphore(5) — 동시 최대 5개 요청.
"""

import asyncio
import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.models.character import CharacterUpdate

logger = logging.getLogger(__name__)

BASE_URL = "https://open.api.nexon.com/maplestory/v1"
_SEMAPHORE = asyncio.Semaphore(5)


class NexonApiClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._headers = {"x-nxopen-api-key": settings.nexon_api_key}

    async def fetch_character(self, char_name: str) -> Optional[CharacterUpdate]:
        """단일 캐릭터 정보 비동기 조회"""
        async with _SEMAPHORE:
            try:
                async with httpx.AsyncClient(
                    headers=self._headers, timeout=10.0
                ) as client:
                    # 1) OCID 조회
                    r = await client.get(
                        f"{BASE_URL}/id",
                        params={"character_name": char_name},
                    )
                    if r.status_code == 404:
                        logger.warning(f"[NexonAPI] '{char_name}' 캐릭터를 찾을 수 없음 (404)")
                        return None
                    r.raise_for_status()
                    ocid: str = r.json()["ocid"]

                    # 2) 기본 정보 + 스탯 병렬 조회
                    basic_r, stat_r = await asyncio.gather(
                        client.get(f"{BASE_URL}/character/basic", params={"ocid": ocid}),
                        client.get(f"{BASE_URL}/character/stat",  params={"ocid": ocid}),
                    )
                    basic_r.raise_for_status()
                    stat_r.raise_for_status()

                    basic = basic_r.json()
                    stat  = stat_r.json()

                    # 3) 전투력: final_stat 리스트에서 "전투력" 항목 추출
                    combat_power = 0
                    for entry in stat.get("final_stat", []):
                        if entry.get("stat_name") == "전투력":
                            try:
                                combat_power = int(
                                    str(entry.get("stat_value", "0")).replace(",", "")
                                )
                            except ValueError:
                                pass
                            break

                    return CharacterUpdate(
                        job=basic.get("character_class", ""),
                        job_detail=basic.get("character_class_level", ""),
                        level=basic.get("character_level", 0),
                        combat_power=combat_power,
                        image_url=basic.get("character_image", ""),
                        server=basic.get("world_name", ""),
                    )

            except httpx.HTTPStatusError as e:
                logger.warning(f"[NexonAPI] '{char_name}' HTTP {e.response.status_code}: {e.response.text}")
                return None
            except Exception as e:
                logger.warning(f"[NexonAPI] '{char_name}' 조회 실패: {type(e).__name__}: {e}")
                return None

    async def fetch_characters_bulk(
        self, char_names: list[str]
    ) -> dict[str, Optional[CharacterUpdate]]:
        """다수 캐릭터 정보 동시 조회 (Semaphore(5) 제한)"""
        tasks = [self.fetch_character(name) for name in char_names]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return dict(zip(char_names, results))
