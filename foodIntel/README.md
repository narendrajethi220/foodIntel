# FoodIntel dbt project

This directory contains the dbt transformation layer for FoodIntel. It reads
source tables from the `FOODINTEL.RAW` schema and creates the Silver and Gold
layers in Snowflake.

## Project structure

```text
models/
├── staging/       # Silver: source declarations and cleaned views
└── marts/         # Gold: dimensions, facts, and reporting models
macros/            # reusable dbt macros
dbt_project.yml    # project and materialization configuration
```

Staging models are the Silver layer and are configured as views in the
`STAGING` schema. Marts are the Gold layer and are configured as tables in the
`MARTS` schema, with incremental fact models where appropriate.

## Run locally

Install the Snowflake adapter if needed:

```bash
python -m pip install dbt-snowflake
```

Create `~/.dbt/profiles.yml` with the `foodIntel` profile. Keep passwords,
private keys, and passphrases outside this repository.

From this directory:

```bash
dbt debug
dbt run
dbt test
```

For local validation without querying Snowflake:

```bash
dbt parse
dbt compile
```

## Resources

- [dbt documentation](https://docs.getdbt.com/docs/introduction)
- [Snowflake adapter documentation](https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup)
