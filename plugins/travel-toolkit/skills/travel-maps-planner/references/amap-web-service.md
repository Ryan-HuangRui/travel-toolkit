# Amap Web Service Notes

Use a Web Service API key through `AMAP_API_KEY`; never commit it. Domestic place and route requests use `restapi.amap.com` and GCJ-02 coordinates. Overseas services require Amap entitlement and use `sg-restapi.opnavi.com` with WGS84 coordinates.

- Place text search: `GET /v3/place/text`
- Walking: `GET /v5/direction/walking`
- Transit: `GET /v5/direction/transit/integrated` and requires origin/destination city codes
- Driving: `GET /v5/direction/driving`

Request URLs, availability, coverage, and pricing can change. Confirm the current requirements in Amap's official Places and Routes documentation before extending this adapter.
