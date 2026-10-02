# Instream — Backend

The API server for **Instream**, a video-sharing platform.

## Getting Started

### Prerequisites
- Docker Desktop (for the Compose setup), **or** Python 3.13 + Postgres + Redis for local dev.

### Run with Docker Compose (recommended)

```bash
# 1. Create your env file from the template
cp .env.sample .env
# 2. Edit .env — set DB creds, JWT secret, Cloudinary + SMTP values
# 3. Build and start the full stack (API + Postgres + Redis)
docker compose up --build
```

The API is then at **http://localhost:8000**, docs at **http://localhost:8000/docs**. A quick readiness check: `GET http://localhost:8000/health`.

Inside Compose, the API reaches Postgres and Redis by service name (`db`, `redis`) — so `DATABASE_URL` uses `@db:5432` and `REDIS_URL` uses `@redis:6379`, not `localhost`.

### Run locally (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Point DATABASE_URL / REDIS_URL at your local Postgres & Redis (localhost)
uvicorn app.main:app --reload --port 8000
```

### Useful commands

```bash
docker compose up -d --build      # run in background
docker compose logs -f api        # tail the API logs
docker compose down               # stop (keep data)
docker compose down -v            # stop and wipe the Postgres volume
docker compose config             # show resolved config (debug .env)
```

## API Routes

All responses use the `ApiResponse` envelope. All routes require a `Bearer` access token **except** the public ones (listed in `middleware/auth_paths.py`) and the two public `GET /account` reads below.

### Auth — `/auth`
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register/email` | Start registration, email an OTP |
| POST | `/auth/verify/email` | Verify OTP, create the account *(rate-limited)* |
| POST | `/auth/login/email` | Log in, receive access + refresh tokens *(rate-limited)* |
| POST | `/auth/refresh` | Exchange a refresh token for a new pair |
| POST | `/auth/logout` | Revoke refresh + denylist access token |
| POST | `/auth/forgot-password/email` | Email a password-reset code |
| POST | `/auth/reset-password/email` | Verify code, set a new password |

### User — `/account`
| Method | Path | Description |
|---|---|---|
| GET | `/account/{user_id}` | Fetch a user's public profile *(public)* |
| GET | `/account/{user_id}/display-picture` | Stream a user's avatar *(public)* |
| POST | `/account/upload-dp` | Upload/replace own avatar |
| POST | `/account/change-password` | Change password |
| DELETE | `/account/delete` | Delete own account |

### Channel — `/channel`
| Method | Path | Description |
|---|---|---|
| POST | `/channel/create` | Create a channel |
| GET | `/channel/me` | Owner's own channel |
| GET | `/channel/following` | Channels the current user follows |
| GET | `/channel/view/{channel_id}` | Viewer-safe channel info + follow state |
| PATCH | `/channel/update/name` | Update own channel name |
| PATCH | `/channel/update/description` | Update own channel description |
| DELETE | `/channel/delete` | Delete own channel |
| POST | `/channel/follow/{channel_id}` | Follow a channel |
| POST | `/channel/unfollow/{channel_id}` | Unfollow a channel |

### Video — `/video`
| Method | Path | Description |
|---|---|---|
| GET | `/video` | Feed |
| GET | `/video/search?query=` | Search by title/description |
| GET | `/video/{video_id}` | Single video (+ likes, is_liked, channel) |
| GET | `/video/channel-videos/{channel_id}` | Videos for a channel |
| POST | `/video/upload/generate-signatures` | Signed Cloudinary params (streamers only) |
| POST | `/video/upload/data` | Save video metadata after upload |
| DELETE | `/video/delete` | Delete own video (+ Cloudinary assets) |
| POST | `/video/like/{video_id}` | Like a video |
| POST | `/video/unlike/{video_id}` | Unlike a video |
| POST | `/video/inc-views?video_id=` | Increment views (works logged in or out) |

### Comment — `/comment`
| Method | Path | Description |
|---|---|---|
| POST | `/comment/write/{video_id}` | Post a comment |
| GET | `/comment/{video_id}` | List comments for a video |
| DELETE | `/comment/delete/{comment_id}` | Delete (author or channel owner) |

### History — `/history`
| Method | Path | Description |
|---|---|---|
| GET | `/history` | Current user's watch history |
| POST | `/history/append/{video_id}` | Record a watch |
| DELETE | `/history/delete/{video_id}` | Remove from history |

Interactive docs are available at `/docs` (Swagger) and `/redoc`.

## Folder Structure

```
app/
├── main.py                 # FastAPI app, router registration, middleware
├── configs/
│   ├── db.py               # engine + get_db_session dependency
│   ├── rediss.py           # get_redis_client dependency
│   └── cloudinary.py       # cloudinary.config(secure=True)
├── middleware/
│   ├── auth_middleware.py  # gates all non-public paths
│   └── auth_paths.py       # PUBLIC_PATHS, PUBLIC_PREFIXES
├── dependencies/
│   ├── security.py         # HTTPBearer / security dependency
│   └── rate_limiter.py     # request rate limiting
├── router/                 # endpoint declarations (one file per domain)
│   ├── auth_route.py
│   ├── user_route.py
│   ├── channel_route.py
│   ├── video_route.py
│   ├── comment_route.py
│   └── history_route.py
├── controller/             # handler logic (one file per domain)
│   ├── auth_handler.py
│   ├── user_handler.py
│   ├── channel_handler.py
│   ├── video_handler.py
│   ├── comments_handler.py
│   └── history_handler.py
├── models/                 # SQLModel tables
│   ├── user_model.py
│   ├── channel_model.py
│   ├── video_model.py
│   ├── likes_model.py
│   ├── follower_model.py
│   ├── comment_model.py
│   └── history_model.py
├── schemas.py              # Pydantic request/response schemas + ApiResponse
├── types.py                # enums (ResponseStatusType, …)
└── utils/
    ├── password.py         # hash / verify / validate
    ├── otp.py              # OTP generation
    ├── token.py            # JWT create / decode (+ TTL constants)
    ├── email_service.py    # OTP email delivery
    ├── cloudinary_service.py  # signed upload params, asset destroy
    └── revocation.py       # token revocation helpers
```

## Tech Stack

| Concern | Choice |
|---|---|
| Framework | FastAPI |
| ORM / models | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL |
| Cache / tokens | Redis (async) |


## Environment Variables

Copy `.env.sample` to `.env` and fill in real values. `.env` is gitignored — never commit real secrets.

| Variable | Description |
|---|---|
| `POSTGRES_USER` | Postgres username (used to create the DB in Compose) |
| `POSTGRES_PASSWORD` | Postgres password |
| `POSTGRES_DB` | Database name (`instream-db`) |
| `DATABASE_URL` | Full connection string; host is `db` under Compose |
| `REDIS_URL` | Redis connection string; host is `redis` under Compose |
| `JWT_SECRET` | Secret used to sign access/refresh tokens |
| `SMTP_USER` | SMTP account for sending OTP emails |
| `SMTP_PASSWORD` | SMTP app password |
| `CLOUDINARY_URL` | `cloudinary://<api-key>:<api-secret>@<cloud-name>` |

> The DB credentials must match in three places: the `POSTGRES_*` values, and the user/password/db inside `DATABASE_URL`.
> `CLOUDINARY_URL` is read automatically by `configs/cloudinary.py` via `cloudinary.config(secure=True)`.
> Token lifetimes are configured as constants in `app/utils/token.py`.