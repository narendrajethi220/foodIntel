# FoodIntel

FoodIntel is an end-to-end food analytics and AI project inspired by a modern
lakehouse workflow. The current repository contains the Snowflake foundation
for loading Zomato-style restaurant, menu, order, item, user, and review data.

The planned architecture is:

```text
Source CSVs → Amazon S3 → Snowflake RAW/BRONZE → dbt STAGING → dbt MARTS → serving layer
                                      ├── LLM review enrichment
                                      ├── review embeddings / RAG
                                      └── governed text-to-SQL
```

## Current repository

- `snowflake/01_setup.sql` — database, schemas, warehouse, and `DBT_ROLE`
- `snowflake/02_storage_integraion.sql` — S3 storage integration
- `snowflake/03_stage_and_formats.sql` — CSV format and external stage
- `snowflake/04_raw_tables.sql` — RAW table definitions
- `snowflake/05_load_data.sql` — `COPY INTO` statements and row-count checks
- `aws/iam/s3-read-policy.json` — read-only S3 policy for the integration role
- `data/` — local datasets; intentionally excluded from Git

The dbt models, Airflow DAGs, AI enrichment jobs, RAG application, and serving
dashboard shown in the architecture are planned extensions unless they are
added to this repository separately.

## Data model

The source data covers:

- restaurants and menus
- food items
- users
- orders and order items
- customer reviews

The Snowflake setup follows a medallion-style layout with `RAW`, `BRONZE`,
`STAGING`, `MARTS`, `SNAPSHOTS`, and `AI` schemas. Use dbt to build cleaned
staging models and analytical marts after the raw load is validated.

## Prerequisites

- An AWS account with an S3 bucket
- A Snowflake account with permission to create the database, warehouse,
  storage integration, stages, tables, and roles
- SnowSQL, Snowsight, or another Snowflake SQL client
- Local source files placed under `data/` (not committed)

## Setup

1. Create an S3 bucket and upload the source files using this layout:

   ```text
   s3://<your-bucket>/raw/restaurants/
   s3://<your-bucket>/raw/users/
   s3://<your-bucket>/raw/food/
   s3://<your-bucket>/raw/menu/
   s3://<your-bucket>/raw/orders/
   s3://<your-bucket>/raw/order_items/
   s3://<your-bucket>/raw/reviews/
   ```

2. Configure the AWS IAM role and trust relationship required by the
   Snowflake storage integration. Review `aws/iam/s3-read-policy.json` and
   replace its environment-specific bucket with your own value.

3. Replace the example/environment-specific AWS values in
   `snowflake/02_storage_integraion.sql` and
   `snowflake/03_stage_and_formats.sql`. Do not put credentials or external
   IDs in SQL files committed to Git.

4. Run the Snowflake scripts in order:

   ```text
   snowflake/01_setup.sql
   snowflake/02_storage_integraion.sql
   snowflake/03_stage_and_formats.sql
   snowflake/04_raw_tables.sql
   snowflake/05_load_data.sql
   ```

5. Verify the row counts returned by the final script, then add dbt models and
   tests for the staging and marts layers.

## Security and privacy

This repository intentionally does **not** include raw CSV data or credentials.
The source files contain personal and sensitive-looking fields such as names,
emails, passwords, addresses, user identifiers, order details, and review
text. Keep them in protected storage and use anonymized or synthetic fixtures
for examples and tests.

Before publishing, rotate any AWS/Snowflake credential or external ID that has
ever been committed, shared, or exposed. Also review account IDs, bucket names,
role ARNs, URLs, and IAM policies for unwanted environment disclosure.

To verify what Git would include before the first push:

```bash
git init
git status --short --ignored
git add README.md .gitignore snowflake aws
git diff --cached --stat
git diff --cached --name-only
```

If a sensitive file was staged before it was added to `.gitignore`, remove it
from the index without deleting the local copy:

```bash
git rm --cached credentials
git rm --cached data/*.csv
```

## Roadmap

- Parameterize environment-specific Snowflake and S3 configuration
- Add dbt staging, marts, tests, documentation, and incremental models
- Add Airflow orchestration for upload, raw load, dbt builds, and enrichment
- Add review summarization and sentiment/topic enrichment with an LLM
- Add embeddings and source-grounded RAG chat
- Add a guarded text-to-SQL interface with read-only warehouse access
- Add a Streamlit or BI serving layer

## License

Add a license before publishing if you plan to accept contributions or allow
reuse. Also confirm that the source dataset and any third-party assets permit
redistribution.
