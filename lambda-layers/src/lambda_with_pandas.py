"""
Lambda Layers — Project 3
Lambda function that uses pandas (provided by PandasLayer) to process
a CSV payload passed in the event.

Demonstrates:
  - Using a layer with native extensions (pandas/numpy)
  - Inspecting sys.path to understand where the layer is mounted
  - Returning a structured analysis result
"""

import io
import json
import logging
import sys

import numpy as np
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("pandas version : %s", pd.__version__)
logger.info("numpy version  : %s", np.__version__)
logger.info("Layer paths    : %s", [p for p in sys.path if "/opt/" in p])


def handler(event, context):
    csv_data = event.get("csv_data", "")
    if not csv_data:
        return {"statusCode": 400, "body": "Missing 'csv_data' in event"}

    df = pd.read_csv(io.StringIO(csv_data))
    logger.info("Loaded DataFrame: %d rows × %d columns", *df.shape)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "numeric_columns": numeric_cols,
    }

    if numeric_cols:
        stats = df[numeric_cols].describe().to_dict()
        summary["statistics"] = {
            col: {k: round(v, 4) for k, v in vals.items()}
            for col, vals in stats.items()
        }

    return {"statusCode": 200, "body": json.dumps(summary, default=str)}
