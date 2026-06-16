# Michelin Riding API

Base URL: `http://localhost:8000`  
All endpoints except `/auth/register`, `/auth/login` and `/strava/callback` require:
```
Authorization: Bearer <token>
```

---

## Start the app

```bash
docker compose up --build
docker compose exec api alembic upgrade head
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Current user |

### Profile
| Method | Path | Description |
|--------|------|-------------|
| GET | `/profiles/{userId}` | Get profile + stats |
| PATCH | `/profiles/{userId}` | Update bio, rider type |
| POST | `/profiles/{userId}/bike` | Add a bike |
| POST | `/profiles/{userId}/mounted-tyres` | Mount a tyre on a bike |

### Activities
| Method | Path | Description |
|--------|------|-------------|
| POST | `/activities` | Create a draft activity |
| GET | `/activities` | List activities |
| GET | `/activities/{activityId}` | Get one activity |
| PATCH | `/activities/{activityId}` | Update notes / weather |
| POST | `/activities/{activityId}/complete` | Mark as completed with stats |
| GET | `/activities/{activityId}/route` | Get GPS coordinates for map |
| POST | `/activities/import/gpx` | Import a GPX file |

### Strava
| Method | Path | Description |
|--------|------|-------------|
| GET | `/strava/connect` | Get the Strava OAuth URL |
| GET | `/strava/callback` | OAuth callback (Strava redirects here) |
| GET | `/strava/activities` | List user's Strava activities |
| POST | `/strava/import` | Import a Strava activity |

### Community
| Method | Path | Description |
|--------|------|-------------|
| GET | `/feed` | Community feed |
| POST | `/activities/{activityId}/like` | Like / unlike |
| POST | `/activities/{activityId}/comments` | Post a comment |

### Progress
| Method | Path | Description |
|--------|------|-------------|
| GET | `/progress/summary` | Total km, rides, badges |
| GET | `/progress/weekly` | Distance per day this week |
| GET | `/progress/tyre-wear` | Tyre wear per mounted tyre |

### Recommendations
| Method | Path | Description |
|--------|------|-------------|
| POST | `/recommendations/tyres` | Get tyre recommendation |
| GET | `/recommendations/tyres/{recommendationId}` | Get saved recommendation |

### Challenges
| Method | Path | Description |
|--------|------|-------------|
| GET | `/challenges` | List challenges |
| POST | `/challenges/{challengeId}/join` | Join a challenge |

---

## Connect Strava to an account

### 1. Get the OAuth URL

```
GET /strava/connect
Authorization: Bearer <token>
```

```json
{
  "data": {
    "auth_url": "https://www.strava.com/oauth/authorize?client_id=...",
    "message": "Open this URL in a browser to connect your Strava account."
  }
}
```

Open `auth_url` in the user's browser or a WebView.

### 2. User authorises on Strava

Strava redirects automatically to `GET /strava/callback`. The backend exchanges
the code and stores the tokens — no action needed on the frontend.

Response from the callback:

```json
{
  "data": {
    "connected": true,
    "athlete_id": "163090788",
    "athlete_name": "Souhail Cherif"
  }
}
```

The account is now linked. Store `connected: true` to show/hide the Strava UI.

### 3. Browse Strava activities

```
GET /strava/activities?per_page=20
Authorization: Bearer <token>
```

```json
{
  "data": [
    {
      "strava_id": 18422693586,
      "name": "Morning ride",
      "sport_type": "Ride",
      "distance_km": 42.3,
      "duration_seconds": 5640,
      "elevation_m": 312.0,
      "started_at": "2026-05-08T08:31:09Z",
      "already_imported": false
    }
  ]
}
```

### 4. Import a Strava activity

```
POST /strava/import
Authorization: Bearer <token>

{
  "strava_activity_id": 18422693586,
  "type": "route",
  "weather": "dry",
  "bike_id": "bik_001"
}
```

`bike_id` is optional (defaults to first bike).  
`type`: `route` `gravel` `mtb` `urban`  
`weather`: `dry` `wet` `mixed`

Returns a standard `Activity` object with an `id` to use for map rendering.

---

## Add a route

A route can be added in three ways. All three store the same GPS coordinates
and expose them through `GET /activities/{id}/route`.

### Option A — Manual (no GPS)

```
POST /activities
{
  "user_id": "usr_001",
  "bike_id": "bik_001",
  "type": "route",
  "started_at": "2026-06-16T07:00:00Z"
}
```

Then complete it with stats:

```
POST /activities/{activityId}/complete
{
  "distance_km": 42.3,
  "duration_seconds": 5640,
  "elevation_m": 312,
  "average_speed_kmh": 26.8
}
```

### Option B — GPX file

```
POST /activities/import/gpx
Authorization: Bearer <token>
Content-Type: multipart/form-data

file=<my_ride.gpx>
type=route
weather=dry
```

Stats and GPS coordinates are computed automatically from the file.

### Option C — From Strava

See **Connect Strava** above (steps 3 and 4).

---

## Render the route on a map

```
GET /activities/{activityId}/route
Authorization: Bearer <token>
```

```json
{
  "data": {
    "activity_id": "act_001",
    "coordinates": [[45.765, 4.841], [45.764, 4.840]],
    "distance_km": 42.3,
    "elevation_m": 312.0,
    "duration_seconds": 5640,
    "average_speed_kmh": 26.8,
    "started_at": "2026-06-16T07:00:00",
    "completed_at": "2026-06-16T08:34:00"
  }
}
```

`coordinates` is an array of `[lat, lon]` pairs.

**Leaflet:**
```js
L.polyline(data.coordinates).addTo(map);
```

**React Native Maps:**
```js
const coords = data.coordinates.map(([lat, lng]) => ({ latitude: lat, longitude: lng }));
<Polyline coordinates={coords} />
```

**Mapbox GL** (note: Mapbox uses `[lng, lat]`):
```js
const coords = data.coordinates.map(([lat, lng]) => [lng, lat]);
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+aiomysql://appuser:apppassword@db:3306/appdb` | DB connection |
| `SECRET_KEY` | `change-me` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime (24 h) |
| `STRAVA_CLIENT_ID` | — | From strava.com/settings/api |
| `STRAVA_CLIENT_SECRET` | — | From strava.com/settings/api |
| `STRAVA_REDIRECT_URI` | `http://localhost:8000/strava/callback` | Must match Strava app settings |

---

## Run tests

```bash
docker compose exec api python -m pytest tests/ -v
```
