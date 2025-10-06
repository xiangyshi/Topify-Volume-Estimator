import aiohttp
import asyncio
import json
import base64
from typing import Any, Dict, List, Optional, Union
from constants.endpoints import Endpoints

class DataForSEOClient:
    BASE_URL = "https://api.dataforseo.com/v3"

    def __init__(self, token: str, max_concurrency: int = 5):
        # DataForSEO uses Basic Auth with token
        self.auth_header = {
            "Authorization": "Basic " + token
        }
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def _post(self, session: aiohttp.ClientSession, endpoint: str, payload: Any) -> Dict:
        url = f"{self.BASE_URL}/{endpoint}"
        async with self.semaphore:
            for attempt in range(3):
                try:
                    async with session.post(url, headers=self.auth_header, json=payload, timeout=60) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status in {429, 500, 502, 503, 504}:
                            await asyncio.sleep(2 ** attempt)
                        else:
                            text = await resp.text()
                            raise Exception(f"API Error ({resp.status}): {text}")
                except Exception as e:
                    if attempt == 2:
                        raise e
                    await asyncio.sleep(2 ** attempt)

    async def _get(self, session: aiohttp.ClientSession, endpoint: str) -> Dict:
        url = f"{self.BASE_URL}/{endpoint}"
        async with self.semaphore:
            async with session.get(url, headers=self.auth_header, timeout=60) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    raise Exception(f"API Error ({resp.status}): {text}")

    # -----------------------------
    # High-Level API Methods
    # -----------------------------
    async def post_task(self, endpoint: str, payload: Any) -> Dict:
        """Submit a DataForSEO task (for endpoints like keywords, SERP, etc.)"""
        async with aiohttp.ClientSession() as session:
            return await self._post(session, endpoint, payload)

    async def get_task_result(self, endpoint: str) -> Dict:
        """Fetch a completed task result"""
        async with aiohttp.ClientSession() as session:
            return await self._get(session, endpoint)

    # -----------------------------
    # Generic API Methods
    # -----------------------------
    async def make_request(self, endpoint: Endpoints, payload: Any) -> Dict:
        """Generic method to make requests to any DataForSEO endpoint"""
        return await self.post_task(endpoint.value, payload)

    async def fetch_keyword_analysis(self, keyword: str, domain: str) -> Dict[str, Any]:
        """
        Fetch comprehensive keyword analysis data from DataForSEO API
        
        Args:
            keyword: The keyword to analyze (e.g., "faceless video ai")
            domain: The target domain (e.g., "videoinu.com")
        
        Returns:
            Dictionary containing all collected data with endpoint keys
        """
        print(f"Fetching comprehensive analysis for keyword: '{keyword}' and domain: '{domain}'")
        
        # Collect all data
        all_data = {}
        
        # 1. AI Keyword Search Volume
        print("1. Fetching AI keyword search volume...")
        ai_payload = [{
            "language_name": "English",
            "location_code": 2840,  # United States
            "keywords": [keyword]
        }]
        try:
            ai_data = await self.make_request(Endpoints.AI_KEYWORD_SEARCH_VOLUME, ai_payload)
            all_data["ai_keyword_search_volume"] = ai_data
            print("✅ AI keyword data collected")
        except Exception as e:
            print(f"❌ Failed to fetch AI keyword data: {e}")
            all_data["ai_keyword_search_volume"] = None


        # 2. SERP data
        print("2. Fetching SERP data...")
        serp_payload = [{
            "keyword": keyword,
            "location_code": 2840,    # United States
            "language_code": "en",     # English
            "device": "desktop",
            "os": "macos",
            "depth": 30,              # scan first 30 results
        }]
        try:
            serp_data = await self.make_request(Endpoints.SERP_GOOGLE_ORGANIC_LIVE_ADVANCED, serp_payload)
            all_data["serp_google_organic_live_advanced"] = serp_data
            print("✅ SERP all data collected")
        except Exception as e:
            print(f"❌ Failed to fetch SERP data: {e}")
            all_data["serp_google_organic_live_advanced"] = None

        # # 3. Google Keyword Search Volume
        # print("3. Fetching Google Ads keyword search volume...")
        # volume_payload = [{
        #     "keywords": [keyword],
        #     "location_code": 2840,
        #     "language_code": "en"
        # }]
        # try:
        #     volume_data = await self.make_request(Endpoints.KEYWORD_SEARCH_VOLUME, volume_payload)
        #     all_data["keyword_search_volume"] = volume_data
        #     print("✅ Keyword volume data collected")
        # except Exception as e:
        #     print(f"❌ Failed to fetch keyword volume data: {e}")
        #     all_data["keyword_search_volume"] = None
        
        print("🎉 Comprehensive keyword analysis complete!")
        return all_data

    async def bulk_fetch(self, jobs: List[Dict[str, Any]]):
        """Run multiple API calls concurrently"""
        async with aiohttp.ClientSession() as session:
            coroutines = []
            for job in jobs:
                coroutines.append(self._post(session, job["endpoint"], job["payload"]))
            return await asyncio.gather(*coroutines, return_exceptions=True)
