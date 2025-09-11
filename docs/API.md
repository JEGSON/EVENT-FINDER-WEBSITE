# Event Finder API

Base URL: `http://127.0.0.1:8001/api`

## Resources

- `POST /events` — Create event
- `GET /events` — Search events (with pagination)
- `GET /events/{id}` — Get by ID
- `PATCH /events/{id}` — Partial update
- `DELETE /events/{id}` — Delete
- `GET /meta/categories` — List categories

## Models

Event (response):

```json
{
  "id": 1,
  "title": "Lagos Tech Meetup",
  "description": "Talks on AI, Web and Cloud.",
  "location": "Lagos, Nigeria",
  "category": "tech",
  "date": "2025-10-01",
  "created_at": "2025-09-11T11:00:00Z"
}
```

Create (request):

```json
{
  "title": "...",
  "description": "...",
  "location": "...",
  "category": "tech|music|sports|arts|business|community",
  "date": "YYYY-MM-DD"
}
```

Update (partial): any subset of fields above.

## Search: `GET /events`

Query params:

- `q`: keyword in title or description
- `location`: substring match (case-insensitive)
- `category`: one of the category enums
- `date`: exact date (YYYY-MM-DD)
- `start_date`, `end_date`: inclusive range
- `limit` (1–100), `offset` (>=0)
- `sort`: `date_asc` (default), `date_desc`, `created_desc`

Response headers:

- `X-Total-Count`: total number of matching events (ignores limit/offset)

Example:

```\
GET /api/events?category=tech&limit=6&offset=0&sort=created_desc
X-Total-Count: 42
```

## Create: `POST /events`

```\
POST /api/events
Content-Type: application/json

{"title":"Abuja Tech Expo","location":"Abuja, Nigeria","category":"tech","date":"2025-10-12"}
```

Returns 201 with the created event.

## Get by ID: `GET /events/{id}`

Returns 404 if not found.

## Update: `PATCH /events/{id}`

Partial update; returns 404 if not found.

## Delete: `DELETE /events/{id}`

Returns 204 on success; 404 if not found.
