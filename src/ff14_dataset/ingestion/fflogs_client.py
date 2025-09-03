from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


AUTH_URL = "https://www.fflogs.com/oauth/token"
GQL_URL = "https://www.fflogs.com/api/v2/client"


@dataclass
class FFLogsAuth:
    client_id: str
    client_secret: str
    access_token: Optional[str] = None
    token_expiry: float = 0.0


class FFLogsClient:
    def __init__(self, client_id: str, client_secret: str, concurrency: int = 3, sleep_ms: int = 300):
        self.auth = FFLogsAuth(client_id, client_secret)
        self.semaphore = asyncio.Semaphore(concurrency)
        self.sleep_ms = sleep_ms
        self._client = httpx.AsyncClient(http2=True, timeout=60)

    async def close(self):
        await self._client.aclose()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
    async def _refresh_token(self) -> None:
        resp = await self._client.post(
            AUTH_URL,
            data={"grant_type": "client_credentials", "client_id": self.auth.client_id, "client_secret": self.auth.client_secret},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        self.auth.access_token = data["access_token"]
        self.auth.token_expiry = time.time() + float(data.get("expires_in", 3600)) * 0.9

    async def _ensure_token(self) -> None:
        if not self.auth.access_token or time.time() > self.auth.token_expiry:
            await self._refresh_token()

    async def _gql(self, query: str, variables: Dict[str, Any] | None = None) -> Dict[str, Any]:
        await self._ensure_token()
        async with self.semaphore:
            # gentle pacing
            await asyncio.sleep(self.sleep_ms / 1000.0)
            headers = {"Authorization": f"Bearer {self.auth.access_token}"}
            resp = await self._client.post(GQL_URL, json={"query": query, "variables": variables or {}}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                raise httpx.HTTPError(str(data["errors"]))
            return data["data"]

    # Placeholder queries (to be completed)
    async def list_reports(self, guild_id: Optional[str] = None, encounter_id: Optional[int] = None) -> Dict[str, Any]:
        query = """
        query($encounter: Int) {
          worldData {
            encounter(id: $encounter) { id name }
          }
        }
        """
        return await self._gql(query, {"encounter": encounter_id})

    async def list_zones(self) -> Dict[str, Any]:
        query = """
        query {
          worldData {
            zones {
              id
              name
              difficulties { id name }
              encounters { id name }
            }
          }
        }
        """
        return await self._gql(query)
