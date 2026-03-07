import pandas as pd
import numpy as np
from pathlib import Path

ROOT           = Path(__file__).parent.parent
RAW_PATH       = ROOT / "data" / "raw"       / "f1_raw_data.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "cleaned_race_data.csv"


def load_raw_data(path: Path = RAW_PATH) -> pd.DataFrame:
    # na_values catches \N which is how Kaggle stores nulls
    df = pd.read_csv(path, na_values=["\\N", "NA", "N/A", "", " "])
    print(f"[load]  {len(df):,} rows x {df.shape[1]} columns")
    print(f"  Columns: {list(df.columns)}")
    return df


def inspect_data(df: pd.DataFrame) -> None:
    print("\n── Missing Values (%) ──")
    pct = df.isnull().mean().mul(100).round(2)
    missing = pct[pct > 0]
    print(missing.to_string() if not missing.empty else "  None!")
    print("\n── lap_time_seconds sample ──")
    if "lap_time_seconds" in df.columns:
        print(df["lap_time_seconds"].describe())


def fix_lap_times(df: pd.DataFrame) -> pd.DataFrame:
    """Force lap_time_seconds to numeric, drop rows where it's missing."""
    if "lap_time_seconds" not in df.columns:
        return df

    before = len(df)
    df["lap_time_seconds"] = pd.to_numeric(df["lap_time_seconds"], errors="coerce")
    df = df.dropna(subset=["lap_time_seconds"])
    print(f"[fix_lap_times]  kept {len(df):,} rows (dropped {before - len(df):,} with missing lap time)")
    return df.reset_index(drop=True)


def drop_junk(df: pd.DataFrame) -> pd.DataFrame:
    """Remove impossible lap times and missing driver/race info."""
    before = len(df)

    # Only filter if we have valid numeric values
    if "lap_time_seconds" in df.columns:
        valid_min = df["lap_time_seconds"].quantile(0.01)  # bottom 1%
        valid_max = df["lap_time_seconds"].quantile(0.99)  # top 1%
        print(f"  Keeping lap times between {valid_min:.1f}s and {valid_max:.1f}s")
        df = df[df["lap_time_seconds"].between(valid_min, valid_max)]

    mandatory = [c for c in ["driverRef", "raceId"] if c in df.columns]
    if mandatory:
        df = df.dropna(subset=mandatory)

    print(f"[drop_junk]  removed {before - len(df):,} invalid rows, kept {len(df):,}")
    return df.reset_index(drop=True)


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing numeric with median, missing text with UNKNOWN."""
    numeric_cols  = df.select_dtypes(include=[np.number]).columns.tolist()
    category_cols = df.select_dtypes(include=["object"]).columns.tolist()

    for col in numeric_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    for col in category_cols:
        df[col] = df[col].fillna("UNKNOWN")

    print("[handle_missing]  done")
    return df


def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Cast columns to correct types."""
    int_cols   = ["raceId", "lap", "position", "tyre_age_laps",
                  "stint_number", "safety_car", "constructorId", "grid"]
    float_cols = ["lap_time_seconds", "pit_duration_s"]
    cat_cols   = ["compound", "driverRef", "circuit"]

    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    print("[fix_dtypes]  done")
    return df


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Remove statistically extreme lap times per race."""
    if "lap_time_seconds" not in df.columns or "raceId" not in df.columns:
        return df

    before = len(df)
    z = df.groupby("raceId")["lap_time_seconds"].transform(
        lambda s: (s - s.mean()) / s.std()
    ).abs()
    df = df[z <= 3.0]
    print(f"[remove_outliers]  removed {before - len(df):,} outliers, kept {len(df):,}")
    return df.reset_index(drop=True)


def save_processed(df: pd.DataFrame, path: Path = PROCESSED_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[save]  {len(df):,} rows saved → {path}")


def run_pipeline() -> pd.DataFrame:
    print("=" * 50)
    print("  F1 Data Preprocessing Pipeline")
    print("=" * 50)
    df = load_raw_data()
    inspect_data(df)
    df = fix_lap_times(df)      # ← fixes \N null issue first
    df = drop_junk(df)
    df = handle_missing(df)
    df = fix_dtypes(df)
    df = remove_outliers(df)
    save_processed(df)
    print("\n✅  Preprocessing complete!")
    return df


if __name__ == "__main__":
    run_pipeline()