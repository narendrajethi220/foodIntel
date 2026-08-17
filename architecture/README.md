# FoodINTEL architecture guide

## End-to-end flow

```text
Source CSVs
    ↓
Amazon S3 (file lake)
    ↓ Snowflake storage integration + COPY INTO
Snowflake RAW / Bronze
    ↓ dbt staging models
Snowflake STAGING / Silver
    ↓ dbt marts models
Snowflake MARTS / Gold
    ↓
Streamlit dashboard, RAG chat, and text-to-SQL
```

## Airflow flow

```text
foodIntel_batch (DAG)
    ↓
reload_raw (task)
    ↓
dbt_build_core (task)
    ↓
enrich_reviews (task)
    ↓
dbt_build_ai (task)
```

## File-to-flow map

| File | Responsibility |
|---|---|
| `snowflake/01_setup.sql` | Creates database, schemas, warehouse, and roles |
| `snowflake/02_storage_integraion.sql` | Connects Snowflake to the S3 bucket |
| `snowflake/03_stage_and_formats.sql` | Defines CSV format and external stage |
| `snowflake/04_raw_tables.sql` | Creates RAW tables |
| `snowflake/05_load_data.sql` | Loads staged files with `COPY INTO` |
| `foodIntel/dbt_project.yml` | Tells dbt where files are and how to materialize models |
| `foodIntel/models/staging/*.sql` | Cleans and standardizes RAW data into Silver views |
| `foodIntel/models/marts/*.sql` | Builds Gold dimensions, facts, and reporting marts |
| `airflow/dags/foodIntel_batch.py` | Schedules and orders pipeline tasks |
| `ai/enrich_reviews.py` | Uses Groq to label reviews and writes to `FOODINTEL.AI` |
| `ai/rag.py` | Embeds reviews with Voyage and answers grounded questions |
| `ai/text_to_sql.py` | Generates safe SQL for MARTS questions and displays results |
| `airflow/docker-compose.yaml` | Runs Airflow services and PostgreSQL metadata storage |
| `airflow/dbt_profiles/profiles.yml` | Gives container dbt its Snowflake connection settings |

## What happens in each layer

- **Source:** original CSV files; do not transform them here.
- **S3/Lake:** durable file copy and landing area.
- **RAW/Bronze:** source-shaped Snowflake tables; useful for replay and audit.
- **STAGING/Silver:** clean names, types, null handling, and joins; usually views.
- **MARTS/Gold:** business-ready dimensions, facts, and reporting marts.
- **AI:** review labels and embeddings that extend the analytical model.
- **Serve:** Streamlit apps and BI tools query Gold and AI outputs.

## Why the pipeline is not repeating work

`COPY INTO` tracks files loaded into Snowflake and normally skips a file already
loaded from the same stage. dbt rebuilds transformations, not the original S3
files. Incremental fact models use merge keys. Review enrichment filters out
review IDs already written to `FOODINTEL.AI.REVIEW_ENRICHED`.

## Airflow terms

- **DAG:** the complete workflow: `foodIntel_batch`.
- **Task:** one unit of work inside the DAG, such as `reload_raw`.
- **Operator:** the Airflow class that runs a task, such as `SQLExecuteQueryOperator` or `BashOperator`.
- **Dependency:** the arrow defining order, such as `reload_raw >> dbt_build_core`.
- **Scheduler:** decides when a DAG should run.
- **PostgreSQL:** stores Airflow metadata, not FoodINTEL analytics data.
