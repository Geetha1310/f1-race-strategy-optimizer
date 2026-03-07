import pandas as pd
import numpy as np
from pathlib import Path

ROOT           = Path(__file__).parent.parent
PROCESSED_PATH = ROOT / "data" / "processed" / "cleaned_race_data.csv"
FEATURES_PATH  = ROOT / "data" / "processed" / "features.csv"


# ── Load ───────────────────────────────────────────────────────────────────
def load_clean(path: Path = PROCESSED_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[load]  {len(df):,} rows loaded from cleaned data")
    return df


# ── 1. Tyre features ───────────────────────────────────────────────────────
def add_tyre_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    tyre_age_squared  → captures how degradation accelerates over time
    deg_rate          → how much slower each lap gets on same stint
    """
    if "tyre_age_laps" in df.columns:
        df["tyre_age_squared"] = df["tyre_age_laps"] ** 2
        print("  + tyre_age_squared")

    if {"lap_time_seconds", "raceId", "driverRef"}.issubset(df.columns):
        df = df.sort_values(["raceId", "driverRef", "lap"])
        df["deg_rate"] = df.groupby(["raceId", "driverRef"])[
            "lap_time_seconds"
        ].diff().fillna(0)
        print("  + deg_rate")

    print("[tyre_features]  done")
    return df


# ── 2. Lap time features ───────────────────────────────────────────────────
def add_lap_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    rolling_avg_3  → average of last 3 laps (smooths out one-off slow laps)
    rolling_std_3  → consistency over last 3 laps
    lap_delta      → how much faster/slower vs previous lap
    is_pit_lap     → 1 if this lap was unusually slow (pit stop happened)
    """
    if "lap_time_seconds" not in df.columns:
        return df

    grp = df.groupby(["raceId", "driverRef"])["lap_time_seconds"]

    df["rolling_avg_3"] = grp.transform(
        lambda s: s.rolling(3, min_periods=1).mean()
    )
    df["rolling_std_3"] = grp.transform(
        lambda s: s.rolling(3, min_periods=1).std().fillna(0)
    )
    df["lap_delta"] = grp.transform(lambda s: s.diff().fillna(0))

    # A lap is a pit lap if it's more than 20s slower than median
    median_lt = df["lap_time_seconds"].median()
    df["is_pit_lap"] = (df["lap_time_seconds"] > median_lt + 20).astype(int)

    print("[lap_time_features]  done")
    print("  + rolling_avg_3, rolling_std_3, lap_delta, is_pit_lap")
    return df


# ── 3. Fuel load estimate ──────────────────────────────────────────────────
def add_fuel_features(df: pd.DataFrame,
                      fuel_per_lap: float = 1.8) -> pd.DataFrame:
    """
    Estimate fuel load: cars start with ~100kg, burn ~1.8kg per lap.
    Heavier fuel = slower lap time (~0.03s per kg).
    """
    if "lap" in df.columns:
        df["fuel_load_kg"] = (100 - df["lap"] * fuel_per_lap).clip(lower=0)
        df["fuel_effect"]  = df["fuel_load_kg"] * 0.03
        print("[fuel_features]  done  + fuel_load_kg, fuel_effect")
    return df


# ── 4. Race progress ───────────────────────────────────────────────────────
def add_race_progress(df: pd.DataFrame) -> pd.DataFrame:
    """
    race_progress  → how far through the race (0.0 = start, 1.0 = finish)
    gap_to_leader  → position - 1 (0 = leader)
    """
    if "lap" in df.columns:
        max_lap = df.groupby("raceId")["lap"].transform("max")
        df["race_progress"] = (df["lap"] / max_lap.replace(0, np.nan)).fillna(0)
        print("  + race_progress")

    if "position" in df.columns:
        df["gap_to_leader"] = df["position"] - 1
        print("  + gap_to_leader")

    print("[race_progress]  done")
    return df


# ── 5. Safety car window ───────────────────────────────────────────────────
def add_safety_car_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    laps_since_sc  → laps since last safety car (pit opportunity indicator)
    sc_window_5    → 1 if within 5 laps of a safety car period
    """
    if "safety_car" not in df.columns:
        return df

    df = df.sort_values(["raceId", "lap"])

    def laps_since(s: pd.Series) -> pd.Series:
        out, counter = [], 0
        for val in s:
            counter = 0 if val == 1 else counter + 1
            out.append(counter)
        return pd.Series(out, index=s.index)

    df["laps_since_sc"] = df.groupby("raceId")["safety_car"].transform(laps_since)
    df["sc_window_5"]   = (df["laps_since_sc"] <= 5).astype(int)

    print("[safety_car_features]  done  + laps_since_sc, sc_window_5")
    return df


# ── 6. Encode text columns for ML ─────────────────────────────────────────
def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    ML models need numbers, not text.
    Creates a numeric version of each text column.
    e.g. driverRef_enc: verstappen=0, hamilton=1, ...
    """
    for col in ["driverRef", "circuit", "compound"]:
        if col in df.columns:
            df[f"{col}_enc"] = df[col].astype("category").cat.codes
            print(f"  + {col}_enc")

    print("[encode_categoricals]  done")
    return df


# ── Save ───────────────────────────────────────────────────────────────────
def save_features(df: pd.DataFrame, path: Path = FEATURES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[save]  {len(df):,} rows, {df.shape[1]} features saved → {path}")


# ── Full Pipeline ──────────────────────────────────────────────────────────
def build_features() -> pd.DataFrame:
    print("=" * 50)
    print("  F1 Feature Engineering Pipeline")
    print("=" * 50)
    df = load_clean()
    df = add_tyre_features(df)
    df = add_lap_time_features(df)
    df = add_fuel_features(df)
    df = add_race_progress(df)
    df = add_safety_car_features(df)
    df = encode_categoricals(df)
    save_features(df)
    print("\n✅  Feature engineering complete!")
    print(f"    Final feature columns: {list(df.columns)}")
    return df


if __name__ == "__main__":
    build_features()