# job-sponsor-tracker

Track job applications and check UK visa sponsors.

Work in progress.

## Sponsor register

```mermaid
erDiagram
  register_snapshots ||--o{ sponsors : "first_seen / last_seen"
  sponsors ||--o{ sponsor_routes : has
  sponsors ||--o{ sponsor_aliases : aka

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
```

- `sponsors`: unique on `(name_raw, town)`. Trigram indexes sit on the normalised name columns.

- `removed_time`: set when a company drops off a later register import (row kept)

Source: [Register of licensed sponsors: workers](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers) (OGL v3.0).
