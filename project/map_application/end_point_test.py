import pytest
import httpx

base_url = "http://127.0.0.1:8000"

endpoints = [
    "/mapbox/refresh_weekend_route_sample/0.1",
    "/bike-stations",
    "/country_moi",
    "/refresh/constant_html/admin",
]

@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", endpoints)
async def test_api_endpoints(endpoint):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}{endpoint}", timeout=60.0)
            assert response.status_code == 200, f"Endpoint {endpoint} failed with status code {response.status_code}"
        except httpx.ReadTimeout:
            pytest.fail(f"Request to {endpoint} timed out.")
