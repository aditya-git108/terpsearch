import os
import pandas as pd

def get_real_posts():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "results.csv")

    df = pd.read_csv(csv_path)

    # Only keep the columns we need
    df = df[["text", "timestamp"]]

    # Drop rows with missing or NaN values
    df = df.dropna(subset=["text", "timestamp"])

    # Remove extra quotes from the text field
    df["text"] = df["text"].astype(str).str.replace('"', "").str.strip()

    # Parse timestamps to make sure they’re valid ISO strings
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])  # drop invalid timestamps
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")  # remove Z and millis

    # Convert to JSON-safe records
    return df.to_dict(orient="records")
