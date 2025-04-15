import pandas as pd
import os

# --- Log statistical summary of confidence scores to a CSV file ---
def log_confidence_summary(df, filename="confidence_summary.csv"):
    """
    Computes and logs descriptive statistics (mean, std, etc.) for the confidence
    scores of categorized posts. Appends the result to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame with a 'confidence' column
        filename (str): Name of the CSV file to log summary to (default: "confidence_summary.csv")
    """

    # Compute descriptive statistics for the 'confidence' column
    stats = df['confidence'].describe()

    # Structure the summary as a single-row dictionary
    summary = {
        "count": stats["count"],   # Total number of posts
        "mean": stats["mean"],     # Average confidence score
        "std": stats["std"],       # Standard deviation
        "min": stats["min"],       # Minimum confidence
        "25%": stats["25%"],       # 25th percentile
        "50%": stats["50%"],       # Median
        "75%": stats["75%"],       # 75th percentile
        "max": stats["max"]        # Maximum confidence
    }

    # Add timestamp to indicate when the log entry was created
    summary["label"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

    # Check if log file already exists
    file_exists = os.path.isfile(filename)
    df_out = pd.DataFrame([summary])

    # Append to file if exists, otherwise create a new one
    if file_exists:
        df_out.to_csv(filename, mode='a', header=False, index=False)
    else:
        df_out.to_csv(filename, index=False)
