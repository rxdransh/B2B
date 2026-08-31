"""Transparent rule-based lead scoring for the CRM."""

from typing import Dict, Tuple


def calculate_lead_score(
    company_size: int,
    job_title: str,
    budget: float,
    lead_source: str,
) -> Tuple[int, Dict[str, int]]:
    """Return the capped score and the points awarded by each rule."""
    if company_size < 50:
        size_points = 5
    elif company_size < 200:
        size_points = 10
    elif company_size < 500:
        size_points = 20
    else:
        size_points = 30

    title = job_title.strip().lower()
    if "ceo" in title or "founder" in title:
        title_points = 25
    elif "cto" in title or "cio" in title:
        title_points = 25
    elif "vp" in title or "vice president" in title:
        title_points = 20
    elif "director" in title:
        title_points = 15
    elif "manager" in title:
        title_points = 10
    else:
        title_points = 5

    if budget < 50_000:
        budget_points = 5
    elif budget <= 100_000:
        budget_points = 10
    elif budget <= 500_000:
        budget_points = 20
    else:
        budget_points = 25

    source_points = {
        "Demo Request": 20,
        "Referral": 15,
        "LinkedIn": 10,
        "Webinar": 10,
        "Website": 8,
        "Cold Outreach": 5,
        "Email Campaign": 5,
    }.get(lead_source, 5)

    breakdown = {
        "Company Size": size_points,
        "Job Title": title_points,
        "Budget": budget_points,
        "Lead Source": source_points,
    }
    return min(sum(breakdown.values()), 100), breakdown


def lead_temperature(score: int) -> str:
    """Map a score to the CRM's prioritisation label."""
    if score >= 80:
        return "Hot"
    if score >= 50:
        return "Warm"
    return "Cold"

