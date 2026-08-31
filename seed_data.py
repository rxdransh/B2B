"""Deterministic demo data so the CRM is useful on its first run."""

from datetime import date, timedelta
import random

from scoring import calculate_lead_score, lead_temperature


COMPANIES = [
    "NovaTech Solutions", "CloudSphere", "DataBridge Systems", "FinEdge",
    "ScaleWorks", "BrightLayer", "CoreStack", "Nexora",
    "BluePeak Technologies", "Vertex Systems", "OrbitDesk", "MetricMint",
    "QuantaGrid", "Northstar Labs", "Asterix Digital", "FlowForge",
    "Clearpath Systems", "PrismByte", "ZenithOps", "ElevateIQ",
]

FIRST_NAMES = [
    "Aarav", "Diya", "Kabir", "Meera", "Vihaan", "Anaya", "Rohan", "Ishita",
    "Arjun", "Naina", "Dev", "Tara", "Kunal", "Riya", "Neel", "Aditi",
]
LAST_NAMES = [
    "Mehta", "Kapoor", "Iyer", "Bose", "Nair", "Shah", "Rao", "Khanna",
    "Malhotra", "Desai", "Bhat", "Sethi", "Menon", "Joshi", "Arora", "Sen",
]
INDUSTRIES = ["SaaS", "FinTech", "E-commerce", "Healthcare", "EdTech", "Logistics", "Manufacturing"]
JOB_TITLES = ["CEO", "Founder", "CTO", "CIO", "VP Sales", "VP Operations", "Director of Growth", "IT Director", "Sales Manager", "Product Manager", "Business Analyst"]
SOURCES = ["Website", "LinkedIn", "Referral", "Cold Outreach", "Webinar", "Email Campaign", "Demo Request"]
GTM_STAGES = ["New Lead", "MQL", "SQL", "Opportunity", "Closed Won", "Closed Lost"]
SALES_STAGE_BY_GTM = {
    "New Lead": ["Prospecting"],
    "MQL": ["Prospecting", "Discovery"],
    "SQL": ["Discovery", "Proposal"],
    "Opportunity": ["Proposal", "Negotiation"],
    "Closed Won": ["Closed Won"],
    "Closed Lost": ["Closed Lost"],
}


def generate_sample_leads(count: int = 50) -> list[dict]:
    """Generate consistent fictional B2B leads with varied funnel positions."""
    rng = random.Random(42)
    today = date.today()
    leads = []

    # A weighted funnel produces a realistic top-heavy pipeline.
    stage_weights = [26, 20, 17, 15, 13, 9]
    sizes = [18, 36, 75, 120, 250, 420, 650, 900, 1400, 2200]
    budgets = [30_000, 45_000, 75_000, 100_000, 180_000, 350_000, 500_000, 750_000, 1_200_000]

    for index in range(count):
        company = COMPANIES[index % len(COMPANIES)]
        company_unit = index // len(COMPANIES) + 1
        display_company = company if company_unit == 1 else f"{company} {['Labs', 'Cloud', 'Works'][company_unit - 2]}"
        first = FIRST_NAMES[index % len(FIRST_NAMES)]
        last = LAST_NAMES[(index * 3) % len(LAST_NAMES)]
        name = f"{first} {last}"
        job_title = rng.choice(JOB_TITLES)
        company_size = rng.choice(sizes)
        budget = rng.choice(budgets)
        source = rng.choice(SOURCES)
        stage = rng.choices(GTM_STAGES, weights=stage_weights, k=1)[0]
        sales_stage = rng.choice(SALES_STAGE_BY_GTM[stage])
        score, _ = calculate_lead_score(company_size, job_title, budget, source)
        deal_multiplier = rng.uniform(0.65, 1.15)
        deal_value = round((budget * deal_multiplier) / 5_000) * 5_000
        days_ago = rng.randint(0, 16)
        created_days_ago = days_ago + rng.randint(3, 90)
        email_company = display_company.lower().replace(" ", "").replace("-", "")

        leads.append({
            "name": name,
            "email": f"{first.lower()}.{last.lower()}{index + 1}@{email_company}.example",
            "phone": f"+91 90000 {10000 + index:05d}",
            "company": display_company,
            "industry": rng.choice(INDUSTRIES),
            "job_title": job_title,
            "company_size": company_size,
            "lead_source": source,
            "budget": budget,
            "lead_score": score,
            "temperature": lead_temperature(score),
            "gtm_stage": stage,
            "sales_stage": sales_stage,
            "deal_value": deal_value,
            "last_contacted": (today - timedelta(days=days_ago)).isoformat(),
            "created_at": (today - timedelta(days=created_days_ago)).isoformat(),
        })
    return leads

