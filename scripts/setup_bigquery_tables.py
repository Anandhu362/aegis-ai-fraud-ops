"""Setup BigQuery tables for Aegis Fraud Ops telemetry and historical baselines."""

from google.cloud import bigquery

PROJECT_ID = "aegis-fraud-ops-2026"
DATASET_ID = "fraud_telemetry"


def setup_tables() -> None:
    client = bigquery.Client(project=PROJECT_ID)

    # 1. investigation_results
    ddl_investigations = f"""
    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.investigation_results` (
      tx_id STRING NOT NULL,
      user_id STRING NOT NULL,
      completed_at TIMESTAMP NOT NULL,
      amount NUMERIC,
      currency STRING,
      merchant STRING,
      merchant_category STRING,
      threat_score INT64 NOT NULL,
      risk_level STRING NOT NULL,
      decision STRING NOT NULL,
      typology STRING NOT NULL,
      degraded BOOL,
      llm_adjustment INT64,
      signals STRING,
      rules ARRAY<STRING>,
      latency_total_ms INT64,
      model_orchestrator STRING,
      model_specialist STRING
    )
    PARTITION BY DATE(completed_at);
    """
    client.query(ddl_investigations).result()
    print(f"[OK] Table `{PROJECT_ID}.{DATASET_ID}.investigation_results` verified.")

    # 2. historical_txs
    ddl_historical = f"""
    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.historical_txs` (
      tx_id STRING NOT NULL,
      user_id STRING NOT NULL,
      ts TIMESTAMP NOT NULL,
      amount NUMERIC NOT NULL,
      currency STRING NOT NULL,
      merchant STRING,
      merchant_category STRING NOT NULL,
      channel STRING NOT NULL,
      device_id STRING,
      ip_address STRING,
      latitude FLOAT64,
      longitude FLOAT64,
      city STRING,
      country STRING,
      is_fraud BOOL NOT NULL,
      fraud_type STRING
    )
    PARTITION BY DATE(ts)
    CLUSTER BY user_id, merchant_category;
    """
    client.query(ddl_historical).result()
    print(f"[OK] Table `{PROJECT_ID}.{DATASET_ID}.historical_txs` verified.")

    # 3. user_baselines
    ddl_baselines = f"""
    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.user_baselines` (
      user_id STRING NOT NULL,
      avg_amount NUMERIC,
      std_amount NUMERIC,
      median_amount NUMERIC,
      p95_amount NUMERIC,
      tx_count_90d INT64,
      known_categories ARRAY<STRING>,
      known_countries ARRAY<STRING>,
      known_devices ARRAY<STRING>,
      home_city STRING,
      home_country STRING,
      as_of DATE
    );
    """
    client.query(ddl_baselines).result()
    print(f"[OK] Table `{PROJECT_ID}.{DATASET_ID}.user_baselines` verified.")


if __name__ == "__main__":
    setup_tables()
