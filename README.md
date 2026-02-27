# Cafe & Greengrocer Stock Tracker – Backend

A **FastAPI** backend for managing stock and orders in cafes and greengrocers.  
Authentication uses **JWT + OAuth2 Password Flow** with role-based access control.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Authentication & Authorisation](#authentication--authorisation)
- [User Roles & Permissions](#user-roles--permissions)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Default Admin Account](#default-admin-account)
- [Environment Variables](#environment-variables)
- [Database](#database)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.115 |
| ASGI server | Uvicorn |
| Database | SQLite 3 (via `sqlite3` stdlib) |
| Auth tokens | python-jose (JWT) |
| Password hashing | passlib / bcrypt |
| Data validation | Pydantic v2 |
| Settings | pydantic-settings |

---

## Project Structure

```
backend/
├── main.py                     # Application factory & entry point
├── requirements.txt            # Python dependencies
│
├── api/
│   └── v1/
│       ├── router.py           # Aggregates all v1 routers
│       └── endpoints/
│           ├── auth.py         # Login, refresh, logout, /me
│           ├── users.py        # User CRUD (Admin-only)
│           ├── categories.py   # Category CRUD (any authenticated user)
│           ├── items.py        # Item CRUD (any authenticated user)
│           ├── stock.py        # Stock CRUD (any authenticated user)
│           ├── carts.py        # Cart CRUD (any authenticated user)
│           └── daily_accounts.py # Daily account closing (any authenticated user)
│
├── core/
│   ├── config.py               # App settings (pydantic-settings)
│   ├── security.py             # JWT creation/verification, bcrypt helpers
│   └── dependencies.py         # FastAPI dependency injection (auth, RBAC)
│
├── db/
│   ├── database.py             # SQLite connection, get_db context manager
│   ├── schema.py               # DDL – CREATE TABLE statements
│   ├── seeder.py               # Default admin user seeder
│   └── mock_seeder.py          # Mock data for testing (dev only)
│
├── models/
│   ├── user.py                 # User dataclass + UserRole enum
│   ├── token.py                # RefreshToken dataclass
│   ├── category.py             # Category dataclass
│   ├── item.py                 # Item dataclass
│   ├── stock.py                # StockEntry dataclass
│   ├── cart.py                 # Cart dataclass
│   ├── cart_item.py            # CartItem dataclass
│   ├── daily_account.py        # DailyAccount dataclass
│   └── daily_account_item.py   # DailyAccountItem dataclass
│
├── schemas/
│   ├── user.py                 # Pydantic request/response schemas for User
│   ├── token.py                # Pydantic schemas for Token payloads
│   ├── category.py             # Pydantic schemas for Category
│   ├── item.py                 # Pydantic schemas for Item
│   ├── stock.py                # Pydantic schemas for StockEntry
│   ├── cart.py                 # Pydantic schemas for Cart
│   └── daily_account.py        # Pydantic schemas for DailyAccount
│
├── repositories/
│   ├── user_repository.py      # All SQL for the `users` table
│   ├── token_repository.py     # All SQL for the `refresh_tokens` table
│   ├── category_repository.py  # All SQL for the `categories` table
│   ├── item_repository.py      # All SQL for the `items` table
│   ├── stock_repository.py     # All SQL for the `stock_entries` table
│   ├── cart_repository.py      # All SQL for the `carts` table
│   ├── cart_item_repository.py # All SQL for the `cart_items` table
│   ├── daily_account_repository.py      # All SQL for the `daily_accounts` table
│   └── daily_account_item_repository.py # All SQL for the `daily_account_items` table
│
└── services/
    ├── auth_service.py         # Login, token refresh, logout business logic
    ├── user_service.py         # User registration, update, delete logic
    ├── category_service.py     # Category CRUD business logic
    ├── item_service.py         # Item CRUD business logic
    ├── stock_service.py        # Stock CRUD business logic
    ├── cart_service.py         # Cart CRUD business logic
    └── daily_account_service.py # Daily account closing business logic
```

---

## Architecture Overview

The project follows a strict **4-layer architecture**:

```
API Layer (endpoints)
      ↓  calls
Service Layer (business logic)
      ↓  calls
Repository Layer (data access / SQL)
      ↓  reads/writes
Database (SQLite)
```

| Layer | Responsibility |
|---|---|
| **API** | HTTP request/response, input validation via Pydantic schemas, dependency injection |
| **Service** | Business rules, orchestration, raises HTTP exceptions |
| **Repository** | Raw SQL queries, maps rows → domain models |
| **Models** | Pure Python dataclasses representing database rows |
| **Schemas** | Pydantic models for request validation and response serialisation |
| **Core** | Cross-cutting concerns: config, security utilities, DI helpers |

---

## Authentication & Authorisation

### Flow

1. Client sends `POST /api/v1/auth/login` with `username` + `password` (form data).
2. Server validates credentials, returns an **access token** and a **refresh token**.
3. Client includes the access token in every subsequent request:  
   `Authorization: Bearer <access_token>`
4. When the access token expires (15 min), client calls `POST /api/v1/auth/refresh` with the refresh token to get a new access token.
5. On logout, client calls `POST /api/v1/auth/logout` to revoke the refresh token.

### Token lifetimes

| Token | Lifetime | Storage |
|---|---|---|
| Access token | **15 minutes** | JWT (signed, not stored in DB) |
| Refresh token | **7 days** | JWT + stored in `refresh_tokens` table |

Refresh tokens are stored in the database so they can be **revoked** individually or all at once (logout-everywhere).

---

## User Roles & Permissions

### Roles

| Role | Value | Description |
|---|---|---|
| Admin | `admin` | Full access – manages all users and resources |
| Market Owner | `market_owner` | Manages their own market's employees, stock, and orders |
| Employee | `employee` | Limited access – can view/update assigned tasks |

### User Management Permissions

| Action | Admin | Market Owner | Employee |
|---|---|---|---|
| Create `admin` / `market_owner` | ✅ | ✗ | ✗ |
| Create `employee` | ✅ | ✅ | ✗ |
| List all users | ✅ | ✗ | ✗ |
| View any user profile | ✅ | ✗ | ✗ |
| View employee profiles | ✅ | ✅ | ✗ |
| View own profile | ✅ | ✅ | ✅ |
| Update any user | ✅ | ✗ | ✗ |
| Update employees (no role change) | ✅ | ✅ | ✗ |
| Soft-delete any user | ✅ | ✗ | ✗ |
| Soft-delete employees | ✅ | ✅ | ✗ |
| Soft-delete own account | ✅ | ✅ | ✅ |

Market Owners identify employees by their `role='employee'`. No foreign key relationship is needed.

---

## Item & Category Management

### Categories – `/api/v1/categories`

Categories organize items into logical groups (e.g., "Fresh Produce", "Dairy & Eggs").

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/` | Any authenticated user | Create a new category |
| `GET` | `/` | Any authenticated user | List all categories |
| `GET` | `/{category_id}` | Any authenticated user | Get a specific category |
| `PATCH` | `/{category_id}` | Any authenticated user | Update a category |
| `DELETE` | `/{category_id}` | Any authenticated user | Delete a category (only if no items assigned) |

### Items – `/api/v1/items`

Items represent products that can be stocked and sold.

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/` | Any authenticated user | Create a new item |
| `GET` | `/` | Any authenticated user | List all items (optionally filter by `?category_id=`) |
| `GET` | `/search?q={query}` | Any authenticated user | Search items by name |
| `GET` | `/{item_id}` | Any authenticated user | Get a specific item |
| `PATCH` | `/{item_id}` | Any authenticated user | Update an item |
| `DELETE` | `/{item_id}` | Any authenticated user | Delete an item |

### Item Fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Primary key |
| `category_id` | integer | Reference to the item's category |
| `name` | string | Item name (e.g., "Red Apples") |
| `description` | string | Optional detailed description |
| `sku` | string | Stock Keeping Unit – unique identifier |
| `barcode` | string | Optional barcode (EAN/UPC) |
| `image_url` | string | Optional URL to product image |
| `unit_price` | decimal | Price per unit |
| `unit_type` | string | Unit of measure (e.g., "kg", "piece", "litre") |
| `tax_rate` | decimal | Tax percentage (0-100) |
| `discount_rate` | decimal | Discount percentage (0-100) |
| `created_by` | integer | User who created the item |
| `updated_by` | integer | User who last updated the item |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

---

## API Endpoints

### Authentication – `/api/v1/auth`

| Method | Path | Auth required | Description |
|---|---|---|---|
| `POST` | `/login` | ✗ | OAuth2 Password Flow – returns access + refresh token |
| `POST` | `/refresh` | ✗ | Exchange refresh token for a new access token |
| `POST` | `/logout` | ✓ | Revoke the provided refresh token |
| `POST` | `/logout-all` | ✓ | Revoke all refresh tokens for the current user |
| `GET` | `/me` | ✓ | Get the current user's profile |

### Users – `/api/v1/users`

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/register` | Admin, Market Owner | Create a new user |
| `GET` | `` | Admin | List all users (`?include_deleted=true` for soft-deleted) |
| `GET` | `/{user_id}` | Admin, Market Owner (employees), self | Get a user by ID |
| `PATCH` | `/{user_id}` | Admin, Market Owner (employees) | Update a user |
| `DELETE` | `/{user_id}` | Admin, Market Owner (employees), self | Soft-delete a user |

### Categories – `/api/v1/categories`

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/` | Any authenticated user | Create a new category |
| `GET` | `/` | Any authenticated user | List all categories |
| `GET` | `/{category_id}` | Any authenticated user | Get a specific category |
| `PATCH` | `/{category_id}` | Any authenticated user | Update a category |
| `DELETE` | `/{category_id}` | Any authenticated user | Delete a category (only if no items) |

### Items – `/api/v1/items`

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/` | Any authenticated user | Create a new item |
| `GET` | `/` | Any authenticated user | List all items (filter by `?category_id=`) |
| `GET` | `/search?q={query}` | Any authenticated user | Search items by name |
| `GET` | `/{item_id}` | Any authenticated user | Get a specific item |
| `PATCH` | `/{item_id}` | Any authenticated user | Update an item |
| `DELETE` | `/{item_id}` | Any authenticated user | Delete an item |

> **Note:** The `sku` field is optional when creating an item.

### Stock – `/api/v1/stock`

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/` | Any authenticated user | Add an item to stock (first time only) |
| `GET` | `/` | Any authenticated user | List all stock entries |
| `GET` | `/by-category` | Any authenticated user | Stock grouped by category, sorted by name |
| `GET` | `/{item_id}` | Any authenticated user | Get stock entry for a specific item |
| `PATCH` | `/{item_id}` | Any authenticated user | Update quantity for a stocked item |
| `DELETE` | `/{item_id}` | Any authenticated user | Remove an item from stock |

**Stock rules:**
- An item must exist before it can be added to stock.
- Each item can only have **one** stock entry — adding the same `item_id` twice returns **409 Conflict**.
- To change the quantity, use `PATCH /stock/{item_id}`.

### Carts – `/api/v1/carts`

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/` | Any authenticated user | Create a new cart |
| `GET` | `/{cart_id}` | Any authenticated user | Get cart summary (items + totals) |
| `POST` | `/{cart_id}/items` | Any authenticated user | Add item to cart (error if exists) |
| `PATCH` | `/{cart_id}/items/{cart_item_id}` | Any authenticated user | Update cart item quantity (0 removes) |
| `DELETE` | `/{cart_id}/items` | Any authenticated user | Clear all cart items |

**Cart rules:**
- Items must exist and be in stock before adding to a cart.
- Requested quantities cannot exceed available stock.
- Cart totals include discounts and taxes calculated from item rates.
- Adding an item that already exists returns 409 Conflict; use PATCH to update quantity.
- Setting quantity to 0 via PATCH removes the item from the cart.

### Daily Accounts – `/api/v1/daily-accounts`

| Method | Path | Who can call | Description |
|---|---|---|---|
| `POST` | `/close` | Any authenticated user | Close today's account |
| `GET` | `/` | Any authenticated user | List recent daily accounts |
| `GET` | `/{account_id}` | Any authenticated user | Get daily account summary |
| `GET` | `/by-date/{date}` | Any authenticated user | Get daily account by date |

**Daily Account rules:**
- Closing an account aggregates all carts created today.
- Each day can only have one account, and it can only be closed once.
- Account totals include all items with their discounts and taxes.
- Cannot close an account if no carts exist for today.

Interactive API docs are available at **`/docs`** (Swagger UI) and **`/redoc`**.

---

## Getting Started

### Prerequisites

- Python 3.11+

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd <repo-name>

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set a strong SECRET_KEY

# 5. Run the server (from the project root)
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Swagger UI: `http://localhost:8000/docs`

---

## Default Admin Account

> ⚠️ **FOR DEVELOPMENT ONLY** – remove `seed_admin()` from `main.py` before deploying.

On first startup, a default admin account is automatically created:

| Field | Value |
|---|---|
| Username | `admin` |
| Email | `admin@stocktracker.local` |
| Password | `Admin1234!` |
| Role | `admin` |

The seeder is **idempotent** – it will not create duplicates if run again.

---

## Environment Variables

Copy `.env.example` to `.env` and adjust values:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(random)* | JWT signing secret – **change in production** |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime in days |
| `DATABASE_URL` | `sqlite:///./backend/stock_tracker.db` | SQLite database file path |
| `DEBUG` | `false` | Enable debug mode |
| `ALLOWED_ORIGINS` | `["http://localhost:3000","http://localhost:8000"]` | CORS allowed origins |

---

## Database

The application uses **SQLite 3** via Python's built-in `sqlite3` module.

- The database file (`stock_tracker.db`) is created automatically on first startup inside the `backend/` folder.
- It is listed in `.gitignore` and will **not** be committed to version control.
- Tables are created via `backend/db/schema.py`, called by `init_db()` at startup.
- **Migrations** are applied idempotently on every startup, so existing databases are upgraded automatically.

### Current Tables

| Table | Description |
|---|---|
| `users` | All registered users (including soft-deleted records) |
| `refresh_tokens` | Issued refresh tokens (for revocation) |
| `categories` | Item categories (e.g., "Fresh Produce", "Dairy") |
| `items` | Products/SKUs with pricing and inventory info |
| `stock_entries` | Current quantity on hand per item (one row per item) |
| `carts` | Shopping carts created by employees |
| `cart_items` | Items and quantities per cart |
| `daily_accounts` | Closed daily account summaries |
| `daily_account_items` | Items aggregated in each daily account |

### `items` Table – Key Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `category_id` | INTEGER | Foreign key to `categories` |
| `name` | TEXT | Item name |
| `description` | TEXT | Optional description |
| `sku` | TEXT | Unique stock keeping unit |
| `barcode` | TEXT | Optional barcode (EAN/UPC) |
| `image_url` | TEXT | Optional product image URL |
| `unit_price` | REAL | Price per unit |
| `unit_type` | TEXT | Unit of measure (kg, piece, etc.) |
| `tax_rate` | REAL | Tax percentage (0-100) |
| `discount_rate` | REAL | Discount percentage (0-100) |
| `created_by` | INTEGER | Foreign key to `users` |
| `updated_by` | INTEGER | Foreign key to `users` |
| `created_at` | TEXT | ISO timestamp |
| `updated_at` | TEXT | ISO timestamp |

### `categories` Table – Key Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `name` | TEXT | Unique category name |
| `description` | TEXT | Optional description |
| `created_by` | INTEGER | Foreign key to `users` |
| `updated_by` | INTEGER | Foreign key to `users` |
| `created_at` | TEXT | ISO timestamp |
| `updated_at` | TEXT | ISO timestamp |

### `carts` Table – Key Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `created_by` | INTEGER | Foreign key to `users` |
| `updated_by` | INTEGER | Foreign key to `users` |
| `created_at` | TEXT | ISO timestamp |
| `updated_at` | TEXT | ISO timestamp |

### `cart_items` Table – Key Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `cart_id` | INTEGER | Foreign key to `carts` |
| `item_id` | INTEGER | Foreign key to `items` |
| `quantity` | REAL | Quantity of the item in the cart |
| `created_by` | INTEGER | Foreign key to `users` |
| `updated_by` | INTEGER | Foreign key to `users` |
| `created_at` | TEXT | ISO timestamp |
| `updated_at` | TEXT | ISO timestamp |

### `daily_accounts` Table – Key Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `account_date` | TEXT | Date of the account (unique) |
| `subtotal` | REAL | Total before discounts and taxes |
| `discount_total` | REAL | Total discounts applied |
| `tax_total` | REAL | Total taxes applied |
| `total` | REAL | Final total after discounts and taxes |
| `carts_count` | INTEGER | Number of carts included |
| `items_count` | INTEGER | Number of unique items sold |
| `is_closed` | INTEGER | `1` if closed, `0` if open |
| `closed_at` | TEXT | ISO timestamp when closed |
| `closed_by` | INTEGER | Foreign key to `users` |
| `created_by` | INTEGER | Foreign key to `users` |
| `updated_by` | INTEGER | Foreign key to `users` |
| `created_at` | TEXT | ISO timestamp |
| `updated_at` | TEXT | ISO timestamp |

### `daily_account_items` Table – Key Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `account_id` | INTEGER | Foreign key to `daily_accounts` |
| `item_id` | INTEGER | Foreign key to `items` |
| `item_name` | TEXT | Name of the item at time of closing |
| `sku` | TEXT | SKU at time of closing |
| `quantity` | REAL | Total quantity sold |
| `unit_price` | REAL | Price per unit at time of closing |
| `discount_rate` | REAL | Discount percentage |
| `tax_rate` | REAL | Tax percentage |
| `line_subtotal` | REAL | Subtotal for this item |
| `line_discount` | REAL | Discount amount |
| `line_tax` | REAL | Tax amount |
| `line_total` | REAL | Total for this item |
| `created_at` | TEXT | ISO timestamp |

### `users` Table – Key Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `email` | TEXT | Unique email address |
| `username` | TEXT | Unique username |
| `role` | TEXT | `admin` / `market_owner` / `employee` |
| `is_active` | INTEGER | `1` = active, `0` = deactivated |
| `is_deleted` | INTEGER | `0` = visible, `1` = soft-deleted |
| `deleted_at` | TEXT | ISO timestamp of deletion (null if not deleted) |

### Soft Delete

Deleting a user via the API **never removes the row**. Instead:
- `is_deleted` is set to `1`
- `is_active` is set to `0`
- `deleted_at` is stamped with the current UTC timestamp

Soft-deleted users cannot log in and are excluded from all normal queries.  
Admins can include them in the user list with `GET /api/v1/users?include_deleted=true`.

> More tables (orders, inventory tracking, etc.) will be added in future iterations.

---

## Mock Data (Development)

> ⚠️ **FOR DEVELOPMENT ONLY** – remove `seed_mock_data()` from `main.py` before deploying.

On startup, the application automatically generates mock data for testing:

- **7 Categories**: Fresh Produce, Dairy & Eggs, Bakery, Beverages, Meat & Seafood, Pantry, Snacks
- **32 Items**: Realistic products with SKUs, barcodes, prices, and tax rates
- **3 Carts**: Sample carts populated with a few stocked items

This data is created using the first user (typically the admin) as the creator.
The seeder is **idempotent** – it will not create duplicates if run again.