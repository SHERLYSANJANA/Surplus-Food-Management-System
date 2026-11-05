# 🍱 Food Redistribution System

A Streamlit + PostgreSQL web app that connects donors with surplus food to receivers who need it. Donors post food, receivers request what they need, and the app matches requests to unexpired donations.

## Features

- **Donor registration** with email and phone validation, and duplicate-email detection
- **Receiver registration** and **food requests**, with a list of open requests
- **Food donations** with an expiry date and time, and a list of active (unexpired) donations
- **Smart matching**
  - Matches food names exactly or by similarity (for example "Rice" and "Cooked Rice")
  - Ranks matches by name similarity, how much of the request is covered, and expiry urgency
  - A donor with more food than requested is a valid match, and the surplus stays available
  - Approve one match at a time, or auto-match everything, best first
  - Row locking inside a transaction prevents over-allocation
- **Reports** with counts, a request status chart and a donor-wise donation table
- **SQL operations** page demonstrating SELECT, UPDATE and DELETE

## Tech stack

| Part | Technology |
|------|------------|
| Front end | Streamlit (1.50 or later) |
| Database | PostgreSQL |
| DB driver | psycopg 3 |
| Data tables | pandas |

## Project structure

```
food_redistribution/
├── app.py                  # Home page: dashboard, how it works, quick actions
├── db.py                   # PostgreSQL connection (reads environment variables)
├── ui.py                   # Shared CSS and page header
├── schema.sql              # Database tables
├── test_db.py              # Checks the database connection
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Theme
└── pages/
    ├── 1_Donor.py
    ├── 2_Receivers.py
    ├── 3_Donations.py
    ├── 4_Matching.py
    ├── 5_Reports.py
    └── 6_SQL_Operations.py
```

The `pages/` folder and the numbered file names matter. Streamlit builds the sidebar from them.

## Setup

### 1. Prerequisites

- Python 3.10 or later
- PostgreSQL, with a user that can create databases (the default `postgres` user works)

### 2. Install the dependencies

Open a terminal in the project folder (in VS Code: **Terminal → New Terminal**) and run:

```
pip install -r requirements.txt
```

### 3. Create the database and tables

Create the database once:

```
psql -U postgres -h localhost -c "CREATE DATABASE food_redistribution;"
```

Load the schema:

```
psql -U postgres -h localhost -d food_redistribution -f schema.sql
```

If `psql` is not recognised on Windows, add the PostgreSQL `bin` folder to your PATH for the session (change `16` to your version):

```powershell
$env:Path += ";C:\Program Files\PostgreSQL\16\bin"
```

### 4. Set the database password

The password is read from an environment variable, so it is never stored in the code. Set it in the **same terminal** where you run the app.

PowerShell (Windows):
```powershell
$env:DB_PASSWORD = "your_password"
```

macOS / Linux / Git Bash:
```bash
export DB_PASSWORD="your_password"
```

Optional variables and their defaults:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `food_redistribution` |
| `DB_USER` | `postgres` |

### 5. Test the connection

```
python test_db.py
```

You should see the PostgreSQL version and the list of tables.

### 6. Run the app

```
streamlit run app.py
```

The app opens at http://localhost:8501.

## How to use it

1. **Donor** page: register a donor.
2. **Receivers** page: register a receiver, then submit a food request.
3. **Donations** page: pick a donor and post a food item with a quantity and expiry time.
4. **Matching** page: review the ranked matches and approve one, or use **Auto-match all**.
5. **Reports** page: see totals, request statuses and donor-wise donations.

## Database design

| Table | Purpose |
|-------|---------|
| `Donor` | Donor details (email is unique) |
| `Donation` | A donation post, with an expiry time, linked to a donor |
| `Donation_Items` | Items in a donation, keyed by `(post_id, item_no)` |
| `Receiver` | Receiver details (email is unique) |
| `Receiver_request` | A food request, with status `Pending`, `Partial`, `Fulfilled` or `Cancelled` |
| `Match_Allocation` | Quantity allocated from a donation item to a request |
| `Donor_photos` | Photos for a donor (not used by any page yet) |

## Resetting the data

Delete all rows and restart the ID counters, keeping the tables:

```
psql -U postgres -h localhost -d food_redistribution -c "TRUNCATE donor_photos, match_allocation, donation_items, receiver_request, donation, receiver, donor RESTART IDENTITY CASCADE;"
```

Drop everything and rebuild from `schema.sql`:

```
psql -U postgres -h localhost -d food_redistribution -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -U postgres -h localhost -d food_redistribution -f schema.sql
```

Both commands permanently delete data.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `password authentication failed` | `DB_PASSWORD` is wrong, or not set in this terminal. Check it with `echo $env:DB_PASSWORD` (PowerShell). |
| `DB_PASSWORD environment variable is not set` | Set it as shown in step 4, then restart Streamlit. |
| `psql` not recognised | Add the PostgreSQL `bin` folder to PATH, or use the full path to `psql.exe`. |
| `Could not find page: pages/1_Donor.py` | The page files must be inside a `pages/` folder with these exact names. |
| `relation "reciever_request" does not exist` | An old file is still in use. Search for old spellings with `Select-String -Path *.py, pages\*.py -Pattern "reciever"`. |
| `ModuleNotFoundError: ui` or `db` | `ui.py` and `db.py` must sit next to `app.py`. |
| Styling does not change | Stop Streamlit with `Ctrl+C` and start it again. |
