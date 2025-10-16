Poniżej masz gotową, jednolitą dokumentację projektu w formacie **Markdown** (najlepsza praktyka 2025: jeden plik „handover pack” do repo). Skopiuj całość do pliku `PROJECT_DOCUMENTATION_2025.md` w katalogu głównym projektu.

---

# Laser/Press Orders – Phase 1.1

**Project Documentation (2025 handover pack)**

> Single-file documentation designed for efficient handover to a new engineering team.
> Stack: Python (Tkinter desktop) + Supabase (Postgres + Storage). Version: **Phase 1.1**.

---

## Table of Contents

1. Overview
2. Architecture
3. Local Development Environment
4. Configuration & Secrets
5. Database Schema (Supabase/Postgres)
6. Row-Level Security (RLS) & Storage
7. Application Structure (`mfg_app.py`)
8. Operational Workflows
9. Testing & Smoke Checks
10. Security & Compliance (Production Readiness)
11. Troubleshooting
12. Roadmap (Phase 2 & 3)
13. Handover Checklist
14. Change Log

---

## 1) Overview

**Purpose**: MVP to register and track **customers**, **orders**, and **parts** for laser/press operations.
**Key capabilities**:

* CRUD on customers, orders, parts (+ file uploads to Storage).
* Auto numbering: `process_no = YYYY-00001` (per year).
* Order statuses with **history** and an **SLA dashboard**.
* Export reports to **XLSX**, **DOCX**, **PDF**.

> Production tech (nesting, CAM, execution) is out-of-scope and handled by CypCloud.

**Non-goals** (Phase 1.1): quoting pipeline, ML-based nesting, Outlook agent (planned in later phases).

---

## 2) Architecture

**Client**: Python desktop app (Tkinter) – file: `mfg_app.py`
**Backend**: Supabase (Postgres + RLS + Storage bucket `attachments`)
**Auth (MVP)**: permissive RLS for role `anon` to simplify local desktop use.
**Recommended prod target**: Supabase Auth + `authenticated` role + per-user RLS.

High-level:

```
Tkinter (desktop) ── supabase-py ──► Supabase (Postgres + RLS)
                          │
                          └──────► Supabase Storage (attachments/)
```

---

## 3) Local Development Environment

### Prerequisites

* Python **3.11+** (Windows recommended via `py` launcher)
* Any IDE (Visual Studio 2022 / VS Code / PyCharm)
* Supabase project (Free)
* Git (optional)

### Virtual environment & dependencies

> Best practice: isolate the environment per project.

```powershell
# in project root
py -m venv .venv
.venv\Scripts\Activate.ps1  # CMD: .venv\Scripts\activate.bat ; bash: source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install supabase openpyxl python-docx reportlab pillow tkcalendar python-dotenv
```

### Run the app

```powershell
python mfg_app.py
```

**IDE integration (VS 2022)**: set interpreter to `<project>/.venv/Scripts/python.exe`.

---

## 4) Configuration & Secrets

Create a text file named **`.env`** in the project root:

```
SUPABASE_URL=https://xcehmhxaoqfpehrfofbu.supabase.co
SUPABASE_KEY=<eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZWhtaHhhb3FmcGVocmZvZmJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAwMDI5NzksImV4cCI6MjA3NTU3ODk3OX0.4FPqtwT27jSKmD_MVqMnpNXoT7uXw7nMlyLnzxG1fns>
```

* For MVP, `anon` key is acceptable but **avoid** distributing it publicly.
* For production, require **user sign-in** and use `authenticated` policies.

Do **not** commit real keys to VCS. Use environment-specific `.env` or a secret manager.

---

## 5) Database Schema (Supabase/Postgres)


### Entities

* **customers**
  `id uuid PK`, `name text unique not null`, `contact text`, `created_at timestamptz`
* **orders**
  `id uuid PK`, `process_no text unique not null`, `customer_id uuid -> customers`,
  `title text not null`, `status order_status not null`, `price_pln numeric(12,2)`,
  `received_at date`, `planned_at date`, `finished_at date`, `notes text`, `created_at timestamptz`
* **parts**
  `id uuid PK`, `order_id uuid -> orders`, `idx_code text`, `name text not null`,
  `material text`, `thickness_mm numeric(6,2)`, `qty int`, **unique** (`order_id`, `name`)
* **files**
  `id uuid PK`, `order_id uuid -> orders`, `part_id uuid -> parts`, `kind text`,
  `storage_path text not null`, `original_name text`, `uploaded_at timestamptz`
* **order_status_history**
  `id uuid PK`, `order_id uuid -> orders`, `old_status/new_status order_status`,
  `changed_at timestamptz`, `changed_by text`
* **process_counters**
  `year int PK`, `last_no int`

### Enums

```sql
create type order_status as enum (
  'RECEIVED','CONFIRMED','PLANNED','IN_PROGRESS','DONE','INVOICED'
);
```

### Views (dashboard/SLA)

```sql
create or replace view v_orders_full as
select o.*, c.name as customer_name
from orders o left join customers c on c.id = o.customer_id;

create or replace view v_orders_status_counts as
select status, count(*) as cnt from orders group by status;

create or replace view v_orders_sla as
select
  o.id, o.process_no, o.title, o.status, o.planned_at, o.finished_at,
  (o.planned_at - now()::date) as days_to_deadline,
  case when o.planned_at is not null and o.finished_at is null and o.planned_at < now()::date
       then true else false end as overdue
from orders o;
```

### Auto-numbering (`process_no`) – function & triggers

```sql
create table if not exists process_counters (
  year int primary key,
  last_no int not null default 0
);

create or replace function next_process_no_fn(p_date date default now()::date)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare y int := extract(year from p_date); n int;
begin
  insert into process_counters(year, last_no) values (y, 0)
  on conflict (year) do nothing;

  update process_counters set last_no = last_no + 1
   where year = y returning last_no into n;

  return y::text || '-' || lpad(n::text, 5, '0');
end$$;

alter function next_process_no_fn(date) owner to postgres;

create or replace function set_process_no_before_insert()
returns trigger language plpgsql as $$
begin
  if new.process_no is null or length(new.process_no)=0 then
    new.process_no := next_process_no_fn(coalesce(new.received_at, now()::date));
  end if;
  return new;
end$$;

drop trigger if exists trg_set_procno on orders;
create trigger trg_set_procno
before insert on orders for each row execute procedure set_process_no_before_insert();

create or replace function log_order_status_change()
returns trigger language plpgsql as $$
begin
  if (tg_op = 'UPDATE' and new.status is distinct from old.status) then
    insert into order_status_history(order_id, old_status, new_status, changed_by)
    values (old.id, old.status, new.status, current_setting('request.jwt.claims', true));
  end if;
  return new;
end$$;

drop trigger if exists trg_log_order_status on orders;
create trigger trg_log_order_status
after update on orders for each row execute procedure log_order_status_change();
```

---

## 6) Row-Level Security (RLS) & Storage

### RLS (MVP permissive, using `anon`)

> For desktop MVP without Auth. For production, switch to **authenticated** and per-user policies.

```sql
alter table customers enable row level security;
alter table orders    enable row level security;
alter table parts     enable row level security;
alter table files     enable row level security;
alter table order_status_history enable row level security;
alter table process_counters enable row level security;

drop policy if exists customers_anon_all on customers;
create policy customers_anon_all on customers
for all to anon using (true) with check (true);

drop policy if exists orders_anon_all on orders;
create policy orders_anon_all on orders
for all to anon using (true) with check (true);

drop policy if exists parts_anon_all on parts;
create policy parts_anon_all on parts
for all to anon using (true) with check (true);

drop policy if exists files_anon_all on files;
create policy files_anon_all on files
for all to anon using (true) with check (true);
```

### Storage (bucket `attachments`)

Create bucket in **Storage → Buckets**: `attachments`.

**Auth model (recommended later):**

```sql
create policy "attachments_read"   on storage.objects for select to authenticated using (bucket_id = 'attachments');
create policy "attachments_write"  on storage.objects for insert  to authenticated with check (bucket_id = 'attachments');
create policy "attachments_delete" on storage.objects for delete  to authenticated using (bucket_id = 'attachments');
```

**MVP without Auth (less secure):**

```sql
create policy "attachments_read_anon"   on storage.objects for select to anon using (bucket_id = 'attachments');
create policy "attachments_write_anon"  on storage.objects for insert  to anon with check (bucket_id = 'attachments');
create policy "attachments_delete_anon" on storage.objects for delete  to anon using (bucket_id = 'attachments');
```

---

## 7) Application Structure (`mfg_app.py`)

### Modules

* `supabase` – DB & Storage access
* `tkinter`, `ttk`, `tkcalendar` – GUI
* `python-docx`, `openpyxl`, `reportlab` – exports
* `python-dotenv` – `.env`

### Key features

* **Main window**: filters (customer/title/status/dates), SLA-aware color coding, status counts, overdue/soon counters, export buttons.
* **Customers…** dialog: grid, Add/Edit/Delete, right-click context menu.
* **New order** dialog: customer combobox (+ Add customer…), fields, **local parts list** with Add/Edit/Remove (validated for duplicates), batch save with order.
* **File upload**: stores in `attachments/orders/<process_no>/...` and records DB row.

### API layer (selected functions)

* `list_customers`, `create_customer`, `update_customer`, `delete_customer`
* `insert_order`, `add_part`, `upload_file`
* `update_order_status`, `fetch_status_history`
* `fetch_orders`, `fetch_status_dashboard`

---

## 8) Operational Workflows

* **Create customer** → **Create order** (select customer, add parts locally) → **Save** (order + parts) → (optional) **Upload files** → **Change status** (history logged) → **Export reports**.

* **SLA**: list colors reflect planned vs today (+ overdue/soon counters in dashboard).

* **Data integrity**: unique part `name` per `order_id` is enforced at DB and UI layer.

---

## 9) Testing & Smoke Checks

### DB smoke (SQL Editor)

```sql
insert into customers(name) values ('Test Sp. z o.o.') on conflict (name) do nothing;

insert into orders (customer_id, title, received_at, planned_at, price_pln)
select id, 'TEST ORDER', current_date, current_date + 1, 100
from customers where name='Test Sp. z o.o.' limit 1;

select process_no, title from orders order by created_at desc limit 1;
```

### App smoke

* Run `mfg_app.py` → create customer → new order with 1–2 parts → export XLSX → upload file → verify in Storage.

---

## 10) Security & Compliance (Production Readiness)

* Replace `anon` with **Supabase Auth** (`authenticated`) and per-user **RLS** (e.g., `owner_id = auth.uid()`).
* Avoid storing secrets in code; use secrets manager and environment separation (`.env.development`, `.env.production`, CI/CD variables).
* Storage policies: restrict to user/company-owned paths; consider signed URLs.
* Logging & auditing (DB triggers or external log sink).
* Backups & retention plan for attachments and DB.

---

## 11) Troubleshooting

* **RLS error on insert**: ensure MVP policies exist and RLS is enabled; check `.env` credentials; re-run SQL.
* **`process_no` missing**: verify `trg_set_- [Laser/Press Orders – Phase 1.1](#laserpress-orders--phase-11)
  - [Table of Contents](#table-of-contents)
  - [1) Overview](#1-overview)
  - [2) Architecture](#2-architecture)
  - [3) Local Development Environment](#3-local-development-environment)
    - [Prerequisites](#prerequisites)
    - [Virtual environment \& dependencies](#virtual-environment--dependencies)
    - [Run the app](#run-the-app)
  - [4) Configuration \& Secrets](#4-configuration--secrets)
  - [5) Database Schema (Supabase/Postgres)](#5-database-schema-supabasepostgres)
    - [Entities](#entities)
    - [Enums](#enums)
    - [Views (dashboard/SLA)](#views-dashboardsla)
    - [Auto-numbering (`process_no`) – function \& triggers](#auto-numbering-process_no--function--triggers)
  - [6) Row-Level Security (RLS) \& Storage](#6-row-level-security-rls--storage)
    - [RLS (MVP permissive, using `anon`)](#rls-mvp-permissive-using-anon)
    - [Storage (bucket `attachments`)](#storage-bucket-attachments)
  - [7) Application Structure (`mfg_app.py`)](#7-application-structure-mfg_apppy)
    - [Modules](#modules)
    - [Key features](#key-features)
    - [API layer (selected functions)](#api-layer-selected-functions)
  - [8) Operational Workflows](#8-operational-workflows)
  - [9) Testing \& Smoke Checks](#9-testing--smoke-checks)
    - [DB smoke (SQL Editor)](#db-smoke-sql-editor)
    - [App smoke](#app-smoke)
  - [10) Security \& Compliance (Production Readiness)](#10-security--compliance-production-readiness)
  - [11) Troubleshooting](#11-troubleshooting)
  - [12) Roadmap (Phase 2 \& 3)](#12-roadmap-phase-2--3)
  - [13) Handover Checklist](#13-handover-checklist)
  - [14) Change Log](#14-change-log)
- [Laser/Press Orders – Phase 1.1](#laserpress-orders--phase-11)
  - [Table of Contents](#table-of-contents)
  - [1) Overview](#1-overview)
  - [2) Architecture](#2-architecture)
  - [3) Local Development Environment](#3-local-development-environment)
    - [Prerequisites](#prerequisites)
    - [Virtual environment \& dependencies](#virtual-environment--dependencies)
    - [Run the app](#run-the-app)
  - [4) Configuration \& Secrets](#4-configuration--secrets)
  - [5) Database Schema (Supabase/Postgres)](#5-database-schema-supabasepostgres)
    - [Entities](#entities)
    - [Enums](#enums)
    - [Views (dashboard/SLA)](#views-dashboardsla)
    - [Auto-numbering (`process_no`) – function \& triggers](#auto-numbering-process_no--function--triggers)
  - [6) Row-Level Security (RLS) \& Storage](#6-row-level-security-rls--storage)
    - [RLS (MVP permissive, using `anon`)](#rls-mvp-permissive-using-anon)
    - [Storage (bucket `attachments`)](#storage-bucket-attachments)
  - [7) Application Structure (`mfg_app.py`)](#7-application-structure-mfg_apppy)
    - [Modules](#modules)
    - [Key features](#key-features)
    - [API layer (selected functions)](#api-layer-selected-functions)
  - [8) Operational Workflows](#8-operational-workflows)
  - [9) Testing \& Smoke Checks](#9-testing--smoke-checks)
    - [DB smoke (SQL Editor)](#db-smoke-sql-editor)
    - [App smoke](#app-smoke)
  - [10) Security \& Compliance (Production Readiness)](#10-security--compliance-production-readiness)
  - [11) Troubleshooting](#11-troubleshooting)
  - [12) Roadmap (Phase 2 \& 3)](#12-roadmap-phase-2--3)
  - [13) Handover Checklist](#13-handover-checklist)
  - [14) Change Log](#14-change-log)
* **Upload fails**: verify bucket `attachments`, correct policies for `anon`/`authenticated` model, and correct path format.
* **Virtualenv issues**: don’t recreate `.venv` while active; `deactivate` → delete `.venv` → recreate.

---

## 12) Roadmap (Phase 2 & 3)

* **Phase 2 (Offers)**: numbering, statuses, conversion from offer → order, reports.
* **Phase 3 (Outlook Agent)**: automated intake of inquiries/orders, attachment parsing, templates, SLA alerts, task creation.

---

## 13) Handover Checklist

* [ ] Supabase URL + key shared securely.
* [ ] SQL setup executed (schema, RLS, views, triggers).**
* [ ] Bucket `attachments` created + Storage policies applied.
* [ ] `.env` present; app can connect.
* [ ] `.venv` created; dependencies installed.
* [ ] App runs; test order and exports verified.

---

## 14) Change Log

**2025-10-09** – Phase 1.1 handover pack finalized.

* Added Customers manager (CRUD + context menu).
* New Order dialog extended with local parts list.
* Dashboard + SLA counters.
* Updated DB policies for MVP and clarified prod migration path.

---

**Maintainers**

* App owner: *Operations / Manufacturing IT*
* DB owner: *Supabase project admin (postgres)*

**File**: `PROJECT_DOCUMENTATION_2025.md`
