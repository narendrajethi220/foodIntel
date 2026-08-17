from datetime import datetime
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.bash import BashOperator      # Airflow 3 import

DBT = "/opt/airflow/dbt_venv/bin/dbt"
DBT_PROJECT = "/opt/airflow/dbt/foodIntel"
DBT_PROFILES = "/opt/airflow/dbt/profiles"

COPY_RAW = [
    "USE WAREHOUSE FOODINTEL_WH",
    "COPY INTO FOODINTEL.RAW.restaurants FROM @FOODINTEL.RAW.FOODINTEL_RAW_STAGE/restaurants/  ON_ERROR='CONTINUE'",
    "COPY INTO FOODINTEL.RAW.users       FROM @FOODINTEL.RAW.FOODINTEL_RAW_STAGE/users/        ON_ERROR='CONTINUE'",
    "COPY INTO FOODINTEL.RAW.food        FROM @FOODINTEL.RAW.FOODINTEL_RAW_STAGE/food/         ON_ERROR='CONTINUE'",
    "COPY INTO FOODINTEL.RAW.menu        FROM @FOODINTEL.RAW.FOODINTEL_RAW_STAGE/menu/         ON_ERROR='CONTINUE'",
    "COPY INTO FOODINTEL.RAW.orders      FROM @FOODINTEL.RAW.FOODINTEL_RAW_STAGE/orders/",
    "COPY INTO FOODINTEL.RAW.order_items FROM @FOODINTEL.RAW.FOODINTEL_RAW_STAGE/order_items/",
    "COPY INTO FOODINTEL.RAW.reviews     FROM @FOODINTEL.RAW.FOODINTEL_RAW_STAGE/reviews/",
]

with DAG(
    dag_id="foodIntel_batch",
    # Use a past date so Airflow can schedule the DAG now.
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["foodIntel", "dbt", "snowflake"],
    doc_md=__doc__,
) as dag:

    reload_raw = SQLExecuteQueryOperator(
        task_id="reload_raw", 
        conn_id="snowflake_default",
        sql=COPY_RAW,
        split_statements=True,
        autocommit=True,
    )

    dbt_build_core = BashOperator(
        task_id="dbt_build_core",
        bash_command=f"{DBT} build --exclude tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROFILES}",
    )

    enrich_reviews = BashOperator(
        task_id="enrich_reviews",
        bash_command=f"python /opt/airflow/ai/enrich_reviews.py",
    )

    dbt_build_ai = BashOperator(
        task_id = "dbt_build_ai",
        bash_command=f"{DBT} build --select tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROFILES}"
    )

    reload_raw >> dbt_build_core >> enrich_reviews >> dbt_build_ai
