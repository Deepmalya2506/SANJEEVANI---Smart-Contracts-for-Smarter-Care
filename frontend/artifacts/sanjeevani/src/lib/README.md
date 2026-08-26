# Sanjeevani API integration

`src/lib/api.ts` is the data layer for the emergency logistics service. Page
components can use it without knowing which service owns an endpoint.

Set these frontend environment variables when running the services separately:

```env
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000
VITE_GIS_API_BASE_URL=http://localhost:8001
VITE_MCP_API_BASE_URL=http://localhost:9001
VITE_ORIGIN_LAT=22.5726
VITE_ORIGIN_LON=88.3639
```

The client maps these endpoints:

- `POST /chat`
- `POST /dispatch` and `POST /dispatch/preview`
- `GET /hospitals` and `GET /hospitals/{id}`
- `GET /inventory/search` and `GET /inventory/{hospital_id}`
- `POST /gis/best-option`, `/gis/route`, `/gis/route-map`, `/gis/isochrone`, `/gis/isochrone-map`
- `POST /events/loan-created`, `/events/delivery-confirmed`, `/events/loan-settled`

Keep the returned shapes stable so loading, optimistic status, and empty states
remain unchanged.