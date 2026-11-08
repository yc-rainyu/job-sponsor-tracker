# Job Sponsor Tracker

Check whether a UK company holds a visa sponsor licence, pull the visa wording out of a job ad, and keep track of your applications.

**Live site:** [tracker.ycrainyu.com](https://tracker.ycrainyu.com). Press **Try the demo** to look around without signing in.

## Features

- **Sponsors** (`/`): Search the Home Office register of licensed sponsors by company name. Matches typos, trading names and known brand aliases, and shows each company's rating and visa routes.
- **Analyse** (`/analyse`): Paste a job ad to see what it says about visa sponsorship, quoted from the ad. Also extracts salary, work mode, years of experience and skills. Rule-based, no AI. Signed-in users can save the result to their tracker.
- **Applications** (`/applications`): Sign in with Google to track applications in a table or as cards. Filter by status, country and sponsor result, change the status in place, keep the cover letter and job description with each application, and export everything to CSV.
- **Demo**: *Try the demo* signs you in as a temporary user with 30 sample applications. The demo account and its data are deleted after 24 hours.
- **Your data**: [Privacy](https://tracker.ycrainyu.com/privacy) and [terms](https://tracker.ycrainyu.com/terms) pages. *Delete my account* removes the account and every application straight away.

## Architecture

```mermaid
flowchart LR
  Browser --> Vercel["Vercel: Next.js and proxy.ts"]
  Vercel --> Caddy
  subgraph EC2 ["AWS EC2, London"]
    Caddy["Caddy, HTTPS"] --> FastAPI --> PostgreSQL[(PostgreSQL)]
    Timer["deploy timer"]
  end
  Actions["GitHub Actions"] -->|arm64 image| GHCR
  Timer -->|pulls new images| GHCR
  PostgreSQL -.->|daily backup| S3[(S3)]
```

- **Frontend**: Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, TanStack Table, react-hook-form with zod, next-intl
- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, google-auth, PyJWT
- **Database**: PostgreSQL 17, `pg_trgm` for fuzzy company name search
- **Hosting**: Vercel (frontend), AWS EC2 with Docker Compose (backend), Caddy (HTTPS), Cloudflare (DNS), S3 (backups)
- **CI/CD**: GitHub Actions (ruff, pytest, ESLint, Prettier, builds, Playwright end-to-end tests), images on GitHub Container Registry

The browser only calls `/api/*` on the frontend's domain, and `web/proxy.ts` forwards those requests to the backend. So no CORS setup is needed and the session cookie stays first-party. The frontend's API types are generated from the backend's OpenAPI schema.

## Sign-in

- Google Identity Services gives the browser an ID token. The API checks its signature, audience and issuer with `google-auth` and only accepts verified email addresses.
- Accounts are keyed by the Google account id (`sub`), not by email address.
- The API then sets its own session: a signed JWT in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie that lasts 7 days, or 24 hours for demo users. No passwords or Google tokens are stored.
- Every query on applications is filtered by the signed-in user, and another user's application returns 404.
- Rate limits count each visitor separately even behind Vercel: `proxy.ts` forwards the visitor's IP together with a shared secret, and the API only trusts that IP when the secret matches.

## Deployment

1. A merge to `main` runs CI. Vercel builds the frontend at the same time.
2. Once every check passes, GitHub Actions builds the API image for arm64 (the server is a Graviton t4g) and pushes it to GHCR, tagged with the commit.
3. A systemd timer on the server looks every minute. When `main` has a new commit and its image exists, it pulls the image and restarts the API. Migrations run when the container starts.
4. `/health` reports the commit it was built from. The deploy script waits for it, and a last CI job waits until the live API reports the new commit.

GitHub has no access to the server: the server pulls, nothing pushes to it. The database is dumped to S3 every day and kept for 30 days, and the restore script has been tested.

## Repository layout

```
job-sponsor-tracker
├── api                              // FastAPI backend
│   ├── app
│   │   ├── main.py                  // api routers
│   │   ├── cli.py                   // import-register, import-aliases, import-applications
│   │   ├── core                     // settings, sessions, rate limit, request deps
│   │   ├── db                       // engine and session
│   │   ├── models                   // SQLAlchemy tables
│   │   ├── schemas                  // Pydantic request/response shapes
│   │   ├── routers                  // HTTP endpoints (keep these thin)
│   │   └── services                 // business logic
│   ├── alembic
│   ├── tests                        // pytest
│   ├── Dockerfile
│   └── pyproject.toml               // uv deps, ruff, pytest
├── web                              // Next.js frontend
│   ├── app                          // routes: / (sponsors), /analyse, /applications, /privacy, /terms
│   ├── components
│   │   ├── ui                       // shadcn primitives (kebab-case)
│   │   ├── layout
│   │   ├── sponsors
│   │   ├── analyse
│   │   ├── applications
│   │   └── legal
│   ├── hooks                        // TanStack Query hooks
│   ├── lib                          // API client and generated OpenAPI types
│   ├── messages                     // next-intl copy (en.json)
│   ├── e2e                          // Playwright tests
│   ├── proxy.ts                     // forwards /api/* to the backend
│   └── next.config.ts
├── data
│   ├── aliases.csv
│   ├── skills.yaml                  // skill dictionary for the job-ad parser
│   └── demo-seed.json               // sample applications for the demo
├── docker
│   └── postgres
│       └── init                     // creates jst_test on first database boot
├── deploy                           // production compose, Caddyfile, deploy and backup scripts, systemd timers
├── .github/workflows                // CI, image publish and live deploy check
├── compose.yaml                     // local PostgreSQL + API
├── .env.example
└── README.md
```

## Run locally

Requirements: Docker, Node.js 22, pnpm 9, [uv](https://docs.astral.sh/uv/)

```bash
cp .env.example .env
docker compose up -d                  # PostgreSQL and API on http://localhost:8000
cd web && cp .env.example .env.local
pnpm install && pnpm dev              # http://localhost:3000
```

Sign-in needs a Google OAuth web client ID in `GOOGLE_CLIENT_ID` (`.env`) and `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (`web/.env.local`), with `http://localhost` and `http://localhost:3000` as Authorized JavaScript origins. The demo works without it. Leave `PROXY_KEY` empty locally.

The database starts empty. To load sponsor data, download the latest CSV from the [register page](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers) and import it:

```bash
cd api
uv run python -m app.cli import-register path/to/register.csv --published YYYY-MM-DD
uv run python -m app.cli import-aliases ../data/aliases.csv
```

Tests (the test database needs one migration before the first run):

```bash
cd api
DATABASE_URL=postgresql+psycopg://jst:change-me@localhost:5432/jst_test uv run alembic upgrade head
uv run pytest
cd ../web && pnpm lint && pnpm build
pnpm e2e                              # needs the API running (docker compose up -d)
```

## Data model

```mermaid
erDiagram
  register_snapshots ||--o{ sponsors : "first_seen / last_seen"
  sponsors ||--o{ sponsor_routes : has
  sponsors ||--o{ sponsor_aliases : aka
  users ||--o{ auth_identities : "signs in with"
  users ||--o{ applications : owns

  register_snapshots {
    serial id PK
    date published_date
    text source_file
    int row_count
    int org_count
    int added_count
    int removed_count
    timestamptz import_time
  }

  sponsors {
    serial id PK
    text name_raw
    text legal_name_norm
    text trading_name_raw
    text trading_name_norm
    text town
    text county
    int first_seen_snapshot_id FK
    int last_seen_snapshot_id FK
    timestamptz removed_time
  }

  sponsor_routes {
    int sponsor_id FK
    text route
    text type_rating
  }

  sponsor_aliases {
    serial id PK
    text alias_norm
    int sponsor_id FK
    text source
  }

  users {
    uuid id PK
    text email
    text display_name
    bool is_demo
    timestamptz created_at
    timestamptz last_login_at
  }

  auth_identities {
    uuid id PK
    uuid user_id FK
    text provider
    text provider_subject
  }

  applications {
    uuid id PK
    uuid user_id FK
    text company
    text role
    text country
    text status
    date applied_on
    text cover_letter
    text jd_text
    jsonb sponsor_check
    jsonb skills
    jsonb analysis
    timestamptz updated_at
  }
```

- `sponsors`: unique on `(name_raw, town)`. Trigram indexes sit on the normalised name columns.
- `removed_time`: set when a company drops off a later register import. The row is kept.
- `auth_identities`: unique on `(provider, provider_subject)`.
- `applications.sponsor_check`: the register match saved as JSON when the application was checked, not a foreign key.
- Deleting a user deletes their identities and applications through `ON DELETE CASCADE`.

## Data and licence

- Sponsor data: [Register of licensed sponsors: workers](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers), Home Office. Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- Code: [MIT License](LICENSE)

Unofficial project. Not affiliated with the Home Office and not immigration advice.
