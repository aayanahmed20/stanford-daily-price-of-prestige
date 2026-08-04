import numpy as np
import pandas as pd
from scripts.analysis import rankings, trend_stats
from scripts.config import FOCAL_SCHOOL


def _peer_frame() -> pd.DataFrame:
    # Stanford ranked: 1st lowest net price, 3rd highest earnings.
    rows = [
        ("Princeton University", 9000, 90000),
        (FOCAL_SCHOOL, 11000, 124000),
        ("Harvard University", 15000, 100000),
        ("Yale University", 17000, 95000),
        ("MIT", 20000, 110000),
    ]
    frame = pd.DataFrame(rows, columns=["INSTNM", "NPT4_PRIV", "MD_EARN_WNE_P10"])
    for col in ["COSTT4_A", "C150_4", "PCTPELL", "GRAD_DEBT_MDN", "PCT90_EARN_WNE_P10"]:
        frame[col] = np.arange(len(frame), dtype=float) + 1
    return frame


def test_rankings_lower_is_better_first():
    peers = _peer_frame()
    out = rankings(peers)
    r = out["NPT4_PRIV"]
    assert r["rank"] == 2
    assert r["n"] == 5
    assert r["best"] == "Princeton University"
    assert r["worst"] == "MIT"


def test_rankings_higher_is_better_first():
    peers = _peer_frame()
    out = rankings(peers)
    r = out["MD_EARN_WNE_P10"]
    assert r["rank"] == 1
    assert r["best"] == FOCAL_SCHOOL


def test_rankings_dropna():
    peers = _peer_frame()
    peers.loc[1, "MD_EARN_WNE_P10"] = np.nan
    out = rankings(peers)
    assert out["MD_EARN_WNE_P10"]["n"] == 4
    assert out["MD_EARN_WNE_P10"]["rank"] is None


def test_trend_stats_uses_per_series_windows():
    t = pd.DataFrame(
        {
            "year_int": [1996, 2000, 2005, 2010, 2024],
            "stanford_tuition": [np.nan, 24716, 35000, 45000, 65910],
            "real_stanford_tuition": [np.nan, 46213, 50000, 55000, 67646],
            "peer_median_tuition": [30000, 32000, 40000, 50000, 67250],
            "real_peer_median_tuition": [50000, 55000, 60000, 65000, 69021],
            "national_median_tuition": [1000, 3300, 5000, 7000, 10068],
            "real_national_median_tuition": [2000, 6169, 7000, 8000, 10333],
            "stanford_cost": [np.nan, np.nan, 51760, 70000, 87833],
            "real_stanford_cost": [np.nan, np.nan, 60000, 75000, 90000],
        }
    )
    out = trend_stats(t)
    series = {s["series"]: s for s in out["tuition_series"]}
    assert series["stanford"]["start_year"] == 2000
    assert series["stanford"]["end_year"] == 2024
    assert series["stanford"]["start_nominal"] == 24716
    assert out["stanford_total_cost"]["start_year"] == 2005
    assert out["stanford_total_cost"]["end_year"] == 2024
    assert abs(series["stanford"]["cagr_real"] - ((67646 / 46213) ** (1 / 24) - 1)) < 1e-9
