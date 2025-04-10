import pandas as pd
import os

def log_confidence_summary(df, filename="confidence_summary.csv"):
    stats = df['confidence'].describe()
    summary = {
        "count": stats["count"],
        "mean": stats["mean"],
        "std": stats["std"],
        "min": stats["min"],
        "25%": stats["25%"],
        "50%": stats["50%"],
        "75%": stats["75%"],
        "max": stats["max"]
    }

    summary["label"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

    file_exists = os.path.isfile(filename)
    df_out = pd.DataFrame([summary])

    if file_exists:
        df_out.to_csv(filename, mode='a', header=False, index=False)
    else:
        df_out.to_csv(filename, index=False)
