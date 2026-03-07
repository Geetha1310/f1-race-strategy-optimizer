import pandas as pd
from pathlib import Path

RAW = Path(__file__).parent / "raw"
OUT = RAW / "f1_raw_data.csv"


def load_csv(filename: str) -> pd.DataFrame:
    path = RAW / filename
    print(f"  Reading {filename} ...", end=" ")
    df = pd.read_csv(path)
    print(f"{len(df):,} rows")
    return df


if __name__ == "__main__":
    # ── Load files ─────────────────────────────────────────────────────
    lap_times = load_csv("lap_times.csv")
    pit_stops = load_csv("pit_stops.csv")
    races     = load_csv("races.csv")
    drivers   = load_csv("drivers.csv")
    results   = load_csv("results.csv")

    # ── Convert milliseconds → seconds ─────────────────────────────────
    lap_times["lap_time_seconds"] = lap_times["milliseconds"] / 1000

    # ── Add circuit name and year ───────────────────────────────────────
    races_small = races[["raceId", "year", "name"]].rename(columns={"name": "circuit"})
    df = lap_times.merge(races_small, on="raceId", how="left")

    # ── Add driver name ─────────────────────────────────────────────────
    drivers_small = drivers[["driverId", "driverRef"]]
    df = df.merge(drivers_small, on="driverId", how="left")

    # ── Add constructor info ────────────────────────────────────────────
    results_small = results[["raceId", "driverId", "constructorId", "grid"]].drop_duplicates()
    df = df.merge(results_small, on=["raceId", "driverId"], how="left")

    # ── Add pit stop info ───────────────────────────────────────────────
    pit_small = pit_stops[["raceId", "driverId", "lap", "stop", "duration"]].rename(
        columns={"stop": "pit_stop_no", "duration": "pit_duration_s"}
    )
    df = df.merge(pit_small, on=["raceId", "driverId", "lap"], how="left")

    # ── Placeholder columns for ML models ──────────────────────────────
    df["compound"]       = "UNKNOWN"
    df["tyre_age_laps"]  = 0
    df["stint_number"]   = 1
    df["safety_car"]     = 0
    df["speed_trap_kph"] = None
    df["fuel_load_kg"]   = None

    # ── Keep 2018–2023 only ─────────────────────────────────────────────
    df = df[df["year"] >= 2018].reset_index(drop=True)

    # ── Drop columns we don't need ──────────────────────────────────────
    df = df.drop(columns=["milliseconds", "time", "driverId"], errors="ignore")

    # ── Save ────────────────────────────────────────────────────────────
    df.to_csv(OUT, index=False)
    print(f"\n✅  Done!  {len(df):,} rows saved → {OUT}")
    print(f"    Columns: {list(df.columns)}")
    print("\nSample rows:")
    print(df.head(3).to_string())