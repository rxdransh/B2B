"""Business metric calculations kept separate from presentation code."""

import pandas as pd


GTM_STAGES = ["New Lead", "MQL", "SQL", "Opportunity", "Closed Won", "Closed Lost"]
OPEN_STAGES = ["MQL", "SQL", "Opportunity"]


def prepare_dates(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["last_contacted"] = pd.to_datetime(result["last_contacted"], errors="coerce")
    result["created_at"] = pd.to_datetime(result["created_at"], errors="coerce")
    return result


def dashboard_metrics(df: pd.DataFrame) -> dict:
    total = len(df)
    won = int((df["gtm_stage"] == "Closed Won").sum()) if total else 0
    open_mask = df["gtm_stage"].isin(OPEN_STAGES) if total else pd.Series(dtype=bool)
    return {
        "Total Leads": total,
        "Qualified Leads": int((df["lead_score"] >= 50).sum()) if total else 0,
        "Open Opportunities": int(open_mask.sum()) if total else 0,
        "Pipeline Value": float(df.loc[open_mask, "deal_value"].sum()) if total else 0,
        "Won Revenue": float(df.loc[df["gtm_stage"] == "Closed Won", "deal_value"].sum()) if total else 0,
        "Conversion Rate": (won / total * 100) if total else 0,
    }


def funnel_counts(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["gtm_stage"].value_counts()
    return pd.DataFrame({"Stage": GTM_STAGES, "Leads": [int(counts.get(stage, 0)) for stage in GTM_STAGES]})


def overdue_followups(df: pd.DataFrame, today=None) -> pd.DataFrame:
    dated = prepare_dates(df)
    today = pd.Timestamp.today().normalize() if today is None else pd.Timestamp(today).normalize()
    dated["Days Since Contact"] = (today - dated["last_contacted"].dt.normalize()).dt.days
    result = dated[(dated["gtm_stage"] != "Closed Won") & (dated["Days Since Contact"] > 2)].copy()
    result["Priority"] = result["temperature"].map({"Hot": "High", "Warm": "Medium", "Cold": "Low"})
    result["_priority"] = result["Priority"].map({"High": 0, "Medium": 1, "Low": 2})
    return result.sort_values(["_priority", "lead_score"], ascending=[True, False]).drop(columns="_priority")


def source_performance(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source, group in df.groupby("lead_source"):
        rows.append({
            "Lead Source": source,
            "Number of Leads": len(group),
            "Qualified Leads": int((group["lead_score"] >= 50).sum()),
            "Opportunities": int(group["gtm_stage"].isin(["Opportunity", "Closed Won", "Closed Lost"]).sum()),
            "Won Deals": int((group["gtm_stage"] == "Closed Won").sum()),
            "Revenue": float(group.loc[group["gtm_stage"] == "Closed Won", "deal_value"].sum()),
        })
    return pd.DataFrame(rows).sort_values("Number of Leads", ascending=False) if rows else pd.DataFrame()


def funnel_conversions(df: pd.DataFrame) -> pd.DataFrame:
    # Counts are cumulative: each later stage has passed through earlier stages.
    stage_rank = {
        "New Lead": 0,
        "MQL": 1,
        "SQL": 2,
        "Opportunity": 3,
        "Closed Won": 4,
        # A lost deal still entered the opportunity stage.
        "Closed Lost": 3,
    }
    ranks = df["gtm_stage"].map(stage_rank).fillna(-1)
    steps = [("Lead → MQL", 0, 1), ("MQL → SQL", 1, 2), ("SQL → Opportunity", 2, 3), ("Opportunity → Closed Won", 3, 4)]
    rows = []
    for label, from_rank, to_rank in steps:
        entered = int((ranks >= from_rank).sum())
        progressed = int((ranks >= to_rank).sum())
        rows.append({"Funnel Step": label, "Entered": entered, "Progressed": progressed, "Conversion %": round(progressed / entered * 100, 1) if entered else 0.0})
    return pd.DataFrame(rows)
