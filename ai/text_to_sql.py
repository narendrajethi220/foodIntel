import os
import pandas as pd
import streamlit as st
import snowflake.connector
from groq import Groq
import json
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

# This is one of the active models available to the current Groq project.
MODEL = "openai/gpt-oss-20b"

FORBIDDEN_WORDS = [
    "drop", "delete", "truncate", "alter", "update", "insert", "create",
    "replace", "grant", "revoke", "merge", "call", "execute",
]

EXAMPLE_QUESTIONS = [
    "Top 10 cities by GMV",
    "Which cuisin has the most orders?",
    "Average delivery time by city, worst first",
    "Cancel rate by payment method"
]

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SCHEMA = """
Tables available (Snowflake). Use bare table names, no database or schema prefix.
 
FCT_ORDERS(order_id, order_date, customer_id, restaurant_id, city, cuisine,
           payment_method, order_status, is_delivered, sales_amount, discount,
           delivery_fee, gst, customer_rating, delivery_time_min)
DIM_RESTAURANTS(restaurant_id, restaurant_name, city, cuisine, rating, cost_for_two)
DIM_CUSTOMER(customer_id, customer_name, age, age_segment, gender, occupation,
            income_band, education, family_size)
MART_DAILY_CITY_REVENUE(order_date, city, orders, delivered_orders, cancel_rate, gmv, aov)
MART_RESTAURANT_PERFORMANCE(restaurant_id, restaurant_name, city, cuisine,
                            orders, revenue, avg_customer_rating, avg_delivery_min)
MART_DELIVERY_SLA(city, order_hour, delivered_orders, p50, p90)

 
Note: gmv means delivered revenue. Prefer the MART_ tables when they fit the question.
"""
 
SYSTEM_PROMPT = f"""
You are a Snowflake SQL expert. Write ONE SELECT query that answers the question.
 
Rules:
- SELECT queries only, never modify data.
- Use bare table names (FCT_ORDERS, not FOODINTEL.MARTS.FCT_ORDERS).
- Add a LIMIT of 100 or less, unless the question asks for a single total.
- Reply as JSON in this exact format: {{"sql": "your query here"}}
 
{SCHEMA}
"""
 


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="MARTS",
        role="DBT_ROLE",
        private_key_file=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE"),
        private_key_file_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
    )


def generate_sql(question):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )
    answer = response.choices[0].message.content
    sql = json.loads(answer)["sql"]

    sql = sql.replace("FOODINTEL.MARTS.", "").replace("FOODINTEL.", "")
    return sql.strip().rstrip(";")


def is_safe(sql):
    normalized = sql.strip().rstrip(";").strip()
    lowered = normalized.lower()

    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False

    if ";" in normalized or "--" in normalized or "/*" in normalized:
        return False

    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            return False

    return True

def run_query(sql):
    conn = get_connection()
    cursor = conn.cursor()
    return cursor.execute(sql).fetch_pandas_all()


st.title("Chat with your FOODINTEL Data")
st.caption(f"Ask in English, {MODEL} writes the SQL, Snowflake runs it")

with st.sidebar:
    st.header("Example Questions")
    for q in EXAMPLE_QUESTIONS:
        st.markdown(f" - {q}")

question = st.text_input("Enter your question here", 
                         placeholder="e.g. Top 10 restaurants by revenune in Banglore")


if question:
    sql = generate_sql(question)
    st.code(sql, language="sql")

    if not is_safe(sql):
        st.error("The generated SQL is not safe to run. Please modify your question.")

    else:
        try:
            df = run_query(sql)
            st.success(f"{len(df)} rows returned")
            st.dataframe(df, hide_index=True)

            if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                st.bar_chart(df, x=df.columns[0], y=df.columns[1])

        except Exception as e:
            st.error(f"Error running query: {e}")
