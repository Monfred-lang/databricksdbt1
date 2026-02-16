# Job-Ready dbt + Databricks E-Commerce Project [2026]

End-to-end data pipeline for an e-commerce analytics layer: **orders**, **customers**, **products**, and **order line items**. Built with dbt on Databricks so you can run it locally or deploy via CI/CD.

## What you get

**Medallion architecture** (no prefix/postfix on schema names):

- **Bronze** (`bronze` schema): Raw data from seed CSVs (customers, orders, order_items, products) loaded into Databricks.
- **Silver** (`silver` schema): Staging views for orders, order_items, products (1:1 with raw) + intermediate views. Customers have no staging—only `scd_customers` (snapshot from raw) in gold.
- **Gold** (`gold` schema): Marts — `fct_orders`, `fct_order_items`, `dim_products`; **`scd_customers`** (Type 2 SCD — the only customer table, attributes only, no order-derived fields); and **exposures** (who uses the data).

**Concepts included (beginner-friendly):**
- **Incremental models**: `fct_orders` and `fct_order_items` use `merge` so only new/changed data is processed each run.
- **Slowly changing dimension (Type 2)**: `scd_customers` snapshot tracks customer history; use `dbt_valid_from` / `dbt_valid_to` for point-in-time queries.
- **Exposures**: Link gold models to dashboards and consumers (CEO dashboard, product analytics).
- **Hooks**: `on-run-start` / `on-run-end` in `dbt_project.yml` for run logging.
- **Tests**: Generic (unique, not_null, relationships, accepted_values) plus singular tests (revenue non-negative, no future dates, positive quantities, valid email, positive product price).

Catalog: **workspace**. Workspace: `dbc-aef35066-afa2.cloud.databricks.com`.

## Prerequisites

- **Python 3.12** (recommended; 3.10–3.11 also work; 3.14 is not yet supported by dbt’s dependencies)
- A Databricks workspace with a **SQL Warehouse** (or all-purpose cluster)
- Databricks **host**, **HTTP path**, and **token** (or OAuth) for connection

## Quick start

### 1. Clone and install

```bash
git clone <your-repo-url>
cd job-ready-dbt-databricks-data-engineering-project
python3.12 -m pip install -r requirements.txt
```

### 2. Connect to Databricks

**Option A — project profile (recommended):** Create `profiles.yml` in the project (or copy from `profiles.yml.example`) and set:

- `http_path`: from Databricks → SQL Warehouse → Connection details → HTTP path
- `token`: from User Settings → Developer → Access tokens

Then run with:

```bash
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/xxxxx"
export DATABRICKS_TOKEN="dapi..."
DBT_PROFILES_DIR=. dbt seed && dbt run && dbt test
```

**Option B — user profile:** Copy `profiles.yml.example` to `~/.dbt/profiles.yml` and fill in `http_path` and `token`. Catalog is `workspace`; schema names are `bronze`, `silver`, `gold` (no prefix/postfix).

### 3. Install packages, load seeds, run models and snapshots

```bash
dbt deps
dbt seed
dbt snapshot   # scd_customers from raw (must run before run, as models depend on it)
dbt run
dbt test
```

### 4. Build and test (full run)

```bash
# If using project profile (profiles.yml in repo with env vars):
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/YOUR_ID"
export DATABRICKS_TOKEN="dapi..."
DBT_PROFILES_DIR=. dbt seed
DBT_PROFILES_DIR=. dbt run
DBT_PROFILES_DIR=. dbt snapshot
DBT_PROFILES_DIR=. dbt test
```

Or use the helper script (uses Python 3.12, runs seed + run + test):

```bash
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/YOUR_ID"
export DATABRICKS_TOKEN="dapi..."
./run.sh
```

### 5. Docs (optional)

```bash
dbt docs generate
dbt docs serve
```

## Project layout (medallion)

```
seeds/              # raw_*.csv → bronze schema
models/
  staging/          # silver: stg_* (views)
  intermediate/     # silver: int_* (views)
  marts/core/       # gold: fct_orders, fct_order_items (incremental), dim_products, exposures
snapshots/          # gold: scd_customers (Type 2 SCD — only customer table, attributes only)
tests/              # singular tests (assert_*.sql) + schema tests in yml
macros/             # generate_schema_name (schema as-is, no prefix/postfix)
```

## CI/CD (GitHub Actions)

The workflow in `.github/workflows/dbt.yml` runs on push to `main`/`master` and on pull requests. It runs `dbt deps`, `dbt seed`, `dbt run`, and `dbt test` against Databricks.

### Required GitHub secrets

| Secret                | Description                                      |
|-----------------------|--------------------------------------------------|
| `DATABRICKS_HOST`     | Workspace host, e.g. `xxx.cloud.databricks.com`  |
| `DATABRICKS_HTTP_PATH`| SQL Warehouse HTTP path                          |
| `DATABRICKS_TOKEN`    | Personal or service principal token (e.g. `dapi...`) |

### Optional secrets

| Secret                 | Description              | Default    |
|------------------------|--------------------------|------------|
| `DBT_SCHEMA`           | Schema for CI runs       | `silver`   |
| `DATABRICKS_CATALOG`   | Unity Catalog name       | `workspace` |

Add these under **Settings → Secrets and variables → Actions** for the repo. Pushes to `main` and PRs will then run the pipeline against the Databricks workspace you configured.

## Interview talking points

When asked *"Walk me through a data project you've built"* or *"What's in your dbt project?"*, you can say:

- **Architecture:** "I built a medallion pipeline on Databricks: bronze for raw data, silver for staging and intermediate models, gold for fact and dimension tables. Schema names are clean—no prefix or postfix."
- **Facts & dimensions:** "Gold has two fact tables—`fct_orders` (order grain) and `fct_order_items` (line grain)—and one dimension, `dim_products`. Customers are in `scd_customers` only (Type 2 SCD, attributes only, no order aggregates)."
- **Scale & history:** "The fact tables are incremental with merge so we only process new data. Customer changes are tracked in `scd_customers` for point-in-time reporting."
- **Quality & impact:** "I added generic tests (unique, not_null, relationships, accepted_values) and singular tests for business rules. Exposures link gold models to dashboards so we can see downstream impact."
- **Deployment:** "The pipeline runs in CI on every push via GitHub Actions against Databricks, and can be scheduled with Databricks Jobs for production."

See **[docs/GOLD_LAYER_QUESTIONS.md](docs/GOLD_LAYER_QUESTIONS.md)** for the dimensional model and 30+ business questions answerable from the gold layer.

**Production tip:** When raw data comes from a lake or warehouse instead of seeds, define **sources** in YAML and set **source freshness** so dbt can alert when data stops landing.

## Databricks workflow (native dbt task + CI/CD)

The pipeline runs in Databricks using the **native dbt task** (Add task → **dbt**): Git source, SQL warehouse, and commands `dbt deps`, `dbt seed`, `dbt run`, `dbt snapshot`, `dbt test`.

**databricks/job_dbt_pipeline.json** defines the job with one **dbt_task**. Replace `YOUR_ORG`, repo name, and `YOUR_SQL_WAREHOUSE_ID` in the JSON, or set Git source and SQL warehouse in the UI after import. Run the job once to confirm. **Deploy Databricks job** (on push to main) updates the job from the JSON; **Trigger Databricks dbt job** runs it by name via the API.

## License

See [LICENSE](LICENSE).
