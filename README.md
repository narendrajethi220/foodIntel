# FoodINTEL

FoodINTEL is a food analytics application that combines Snowflake, dbt,
Apache Airflow, Groq, Voyage AI, and Streamlit.

The project loads food delivery data, transforms it into analytics-ready
tables, enriches customer reviews with AI, and provides natural-language data
search and review analysis.

## Features

- Load food delivery data from Amazon S3 into Snowflake
- Transform data with dbt
- Build staging, fact, dimension, and reporting models
- Orchestrate the pipeline with Apache Airflow
- Classify reviews with Groq
- Search reviews using Voyage AI embeddings and RAG
- Ask data questions using natural-language text-to-SQL
- Display results through Streamlit

## Technologies

- **Storage:** Amazon S3
- **Data warehouse:** Snowflake
- **Transformations:** dbt and SQL
- **Orchestration:** Apache Airflow
- **Review AI:** Groq
- **Embeddings:** Voyage AI `voyage-4`
- **Applications:** Streamlit
- **Airflow metadata:** PostgreSQL

## Data flow

```text
CSV files → Amazon S3 → Snowflake RAW
                              ↓
                    dbt staging models
                              ↓
                    dbt marts models
                              ↓
                Streamlit and AI applications
```

The Airflow pipeline runs these tasks in order:

```text
reload_raw → dbt_build_core → enrich_reviews → dbt_build_ai
```

## Project structure

```text
FoodINTEL/
├── ai/
│   ├── enrich_reviews.py       # AI review classification
│   ├── rag.py                  # Review search and RAG application
│   ├── text_to_sql.py          # Natural-language SQL application
│   └── .env.example            # Environment variable template
├── airflow/
│   ├── dags/foodIntel_batch.py # Airflow workflow
│   ├── Dockerfile              # Airflow image dependencies
│   └── docker-compose.yaml     # Airflow and PostgreSQL services
├── aws/iam/                    # S3 access policy
├── foodIntel/                  # dbt project
│   ├── models/staging/         # Cleaned Silver models
│   ├── models/marts/           # Gold analytics models
│   └── dbt_project.yml         # dbt configuration
└── snowflake/                  # Snowflake setup and loading SQL
```

## Requirements

- Python 3.12 or newer
- A Snowflake account
- An Amazon S3 bucket
- Docker Desktop
- dbt with the Snowflake adapter
- Groq API key
- Voyage AI API key

## Configuration

Copy the environment template:

```bash
cp ai/.env.example ai/.env
```

Add your own credentials to `ai/.env`:

```env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=FOODINTEL
SNOWFLAKE_SCHEMA=AI
SNOWFLAKE_PRIVATE_KEY_FILE=/path/to/private_key.p8
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase
GROQ_API_KEY=your_groq_key
VOYAGE_API_KEY=your_voyage_key
```

Never commit `.env`, passwords, API keys, private keys, or raw datasets.

## Snowflake setup

Run the SQL files in order from the project root:

```text
snowflake/01_setup.sql
snowflake/02_storage_integraion.sql
snowflake/03_stage_and_formats.sql
snowflake/04_raw_tables.sql
snowflake/05_load_data.sql
```

These scripts create the Snowflake database objects, storage integration,
external stage, RAW tables, and data loading commands.

## Run dbt locally

```bash
cd foodIntel
python -m pip install dbt-snowflake
dbt debug
dbt build
dbt test
```

## Run Airflow

From the `airflow` directory:

```bash
cd airflow
docker compose --env-file ../ai/.env build
docker compose --env-file ../ai/.env up -d
```

Open Airflow at:

```text
http://localhost:8081
```

Enable the `foodIntel_batch` DAG and trigger it manually, or allow its daily
schedule to run.

## Run the Streamlit applications

Run the RAG application:

```bash
cd ai
streamlit run rag.py
```

Run the text-to-SQL application:

```bash
cd ai
streamlit run text_to_sql.py
```

## Authentication and security

Snowflake automation uses RSA key-pair authentication so scheduled jobs do not
need a user to enter an MFA code. Applications should use a least-privilege
Snowflake role and read-only access for text-to-SQL queries.

If a credential or API key has been exposed, rotate it immediately.
