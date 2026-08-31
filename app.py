"""GTM Lead Qualification & Revenue Pipeline System."""

from datetime import date, datetime
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import (
    GTM_STAGES,
    OPEN_STAGES,
    dashboard_metrics,
    funnel_conversions,
    funnel_counts,
    overdue_followups,
    source_performance,
)
from database import add_lead, get_lead, get_leads, init_db, mark_contacted, update_lead_stages
from scoring import calculate_lead_score, lead_temperature


st.set_page_config(
    page_title="Nimble GTM | Revenue Operations",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)

GTM_OPTIONS = ["New Lead", "MQL", "SQL", "Opportunity", "Closed Won", "Closed Lost"]
SALES_OPTIONS = ["Prospecting", "Discovery", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
SOURCE_OPTIONS = ["Website", "LinkedIn", "Referral", "Cold Outreach", "Webinar", "Email Campaign", "Demo Request"]
INDUSTRY_OPTIONS = ["SaaS", "FinTech", "E-commerce", "Healthcare", "EdTech", "Logistics", "Manufacturing", "Other"]
PAGES = ["Dashboard", "Leads", "Lead Details", "Sales Pipeline", "Follow-ups", "Analytics", "Add Lead"]


def format_inr(value: float) -> str:
    """Format a value using Indian digit grouping."""
    number = int(round(value))
    sign = "-" if number < 0 else ""
    digits = str(abs(number))
    if len(digits) <= 3:
        return f"{sign}₹{digits}"
    tail = digits[-3:]
    head = digits[:-3]
    pairs = []
    while head:
        pairs.insert(0, head[-2:])
        head = head[:-2]
    return f"{sign}₹{','.join(pairs)},{tail}"


def style_chart(fig, height=340):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=44, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#344054"),
        title_font=dict(size=16, color="#101828"),
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="#EAECF0", zeroline=False)
    fig.update_yaxes(gridcolor="#EAECF0", zeroline=False)
    return fig


def section_intro(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f"<div class='eyebrow'>{eyebrow}</div><h1>{title}</h1><p class='page-copy'>{description}</p>",
        unsafe_allow_html=True,
    )


def temperature_badge(value: str) -> str:
    return f"<span class='badge badge-{value.lower()}'>{value}</span>"


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #F6F8FB; }
    [data-testid="stSidebar"] { background: #101828; border-right: 1px solid #1D2939; }
    [data-testid="stSidebar"] * { color: #F2F4F7; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: .55rem .75rem; border-radius: .55rem; margin-bottom: .12rem;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #1D2939; }
    .brand { padding: .7rem .3rem 1.3rem; }
    .brand-mark { display:inline-flex; width:34px; height:34px; border-radius:10px; align-items:center;
        justify-content:center; background:#7F56D9; color:white; font-weight:700; margin-right:.55rem; }
    .brand-name { font-size:1.05rem; font-weight:700; color:white; vertical-align:middle; }
    .brand-sub { color:#98A2B3; font-size:.75rem; margin:.65rem 0 0 .1rem; }
    .eyebrow { color:#6941C6; text-transform:uppercase; letter-spacing:.09em; font-weight:700; font-size:.72rem; margin-top:.25rem; }
    h1 { color:#101828; letter-spacing:-.035em; font-size:2rem !important; margin:.2rem 0 .2rem !important; }
    h2, h3 { color:#101828; letter-spacing:-.02em; }
    .page-copy { color:#667085; max-width:760px; margin:0 0 1.35rem; }
    [data-testid="stMetric"] { background:white; border:1px solid #EAECF0; padding:1rem 1rem .85rem;
        border-radius:.75rem; box-shadow:0 1px 2px rgba(16,24,40,.04); min-height:112px; }
    [data-testid="stMetricLabel"] { color:#667085; }
    [data-testid="stMetricValue"] { color:#101828; font-weight:700; }
    [data-testid="stDataFrame"] { border:1px solid #EAECF0; border-radius:.75rem; overflow:hidden; }
    .panel { background:white; border:1px solid #EAECF0; border-radius:.8rem; padding:1.15rem; box-shadow:0 1px 2px rgba(16,24,40,.04); }
    .funnel { display:flex; align-items:center; gap:.45rem; background:white; border:1px solid #EAECF0;
        border-radius:.8rem; padding:1rem; overflow-x:auto; margin-bottom:1rem; }
    .funnel-step { flex:1; min-width:105px; padding:.8rem; background:#F9F5FF; border-radius:.6rem; text-align:center; }
    .funnel-name { color:#6941C6; font-size:.78rem; font-weight:600; }
    .funnel-count { color:#101828; font-size:1.45rem; font-weight:700; }
    .funnel-arrow { color:#98A2B3; font-weight:700; }
    .badge { display:inline-block; padding:.22rem .55rem; border-radius:99px; font-size:.76rem; font-weight:700; }
    .badge-hot { background:#FEE4E2; color:#B42318; }
    .badge-warm { background:#FEF0C7; color:#B54708; }
    .badge-cold { background:#E0F2FE; color:#026AA2; }
    .profile-head { background:linear-gradient(135deg,#42307D,#6941C6); padding:1.35rem; border-radius:.85rem; color:white; margin-bottom:1rem; }
    .profile-head h2 { color:white; margin:0; }
    .profile-head p { color:#E9D7FE; margin:.2rem 0 0; }
    .detail-label { color:#667085; font-size:.76rem; text-transform:uppercase; letter-spacing:.04em; }
    .detail-value { color:#101828; font-weight:600; margin-bottom:.85rem; }
    .follow-card { background:white; border:1px solid #EAECF0; border-left:4px solid #F04438;
        border-radius:.75rem; padding:1rem 1.1rem; margin-bottom:.7rem; }
    .follow-card h4 { margin:0 0 .15rem; color:#101828; }
    .follow-meta { color:#667085; font-size:.85rem; }
    .score-row { display:flex; justify-content:space-between; padding:.55rem 0; border-bottom:1px solid #F2F4F7; color:#475467; }
    .score-total { display:flex; justify-content:space-between; padding:.7rem 0 0; color:#101828; font-weight:700; }
    .stButton > button { border-radius:.55rem; font-weight:600; }
    div[data-testid="stForm"] { background:white; border:1px solid #EAECF0; border-radius:.8rem; padding:1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


init_db()

with st.sidebar:
    st.markdown(
        "<div class='brand'><span class='brand-mark'>N</span><span class='brand-name'>Nimble GTM</span>"
        "<div class='brand-sub'>LEAD & REVENUE OPERATIONS</div></div>",
        unsafe_allow_html=True,
    )
    page = st.radio("Workspace", PAGES, label_visibility="collapsed", key="page")
    st.markdown("---")
    st.caption("Local demo workspace")
    st.caption("SQLite · Updated live")


def dashboard_page(df: pd.DataFrame) -> None:
    section_intro("Revenue overview", "Good morning, Revenue Team", "A live view of lead quality, funnel health, and revenue performance.")
    metrics = dashboard_metrics(df)
    display = [
        ("Total Leads", f"{metrics['Total Leads']:,}"),
        ("Qualified Leads", f"{metrics['Qualified Leads']:,}"),
        ("Open Opportunities", f"{metrics['Open Opportunities']:,}"),
        ("Pipeline Value", format_inr(metrics["Pipeline Value"])),
        ("Won Revenue", format_inr(metrics["Won Revenue"])),
        ("Conversion Rate", f"{metrics['Conversion Rate']:.1f}%"),
    ]
    for row_start in (0, 3):
        cols = st.columns(3)
        for col, (label, value) in zip(cols, display[row_start:row_start + 3]):
            col.metric(label, value)

    st.subheader("GTM funnel")
    funnel = funnel_counts(df)
    html = "<div class='funnel'>"
    for index, row in funnel.iterrows():
        html += f"<div class='funnel-step'><div class='funnel-name'>{row['Stage']}</div><div class='funnel-count'>{row['Leads']}</div></div>"
        if index < len(funnel) - 1:
            html += "<div class='funnel-arrow'>→</div>"
    st.markdown(html + "</div>", unsafe_allow_html=True)

    left, right = st.columns(2)
    source = df.groupby("lead_source", as_index=False).size().rename(columns={"size": "Leads"})
    fig = px.bar(source.sort_values("Leads"), x="Leads", y="lead_source", orientation="h", title="Lead source distribution", color_discrete_sequence=["#7F56D9"])
    left.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})

    pipeline = df[df["gtm_stage"].isin(OPEN_STAGES)].groupby("sales_stage", as_index=False)["deal_value"].sum()
    fig = px.bar(pipeline, x="sales_stage", y="deal_value", title="Open pipeline by sales stage", color="sales_stage", color_discrete_sequence=["#7F56D9", "#9E77ED", "#B692F6", "#D6BBFB"])
    fig.update_yaxes(tickprefix="₹")
    right.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})

    followups = overdue_followups(df)
    st.markdown("### Follow-up alerts")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overdue leads", len(followups))
    c2.metric("High priority", int((followups["Priority"] == "High").sum()))
    c3.metric("Overdue pipeline", format_inr(followups["deal_value"].sum()))
    oldest = int(followups["Days Since Contact"].max()) if not followups.empty else 0
    c4.metric("Longest inactive", f"{oldest} days")


def leads_page(df: pd.DataFrame) -> None:
    section_intro("CRM database", "Leads", "Search, segment, and review every account in the revenue funnel.")
    with st.container(border=True):
        search = st.text_input("Search", placeholder="Search lead, company, or email…")
        cols = st.columns(5)
        industries = cols[0].multiselect("Industry", sorted(df["industry"].dropna().unique()))
        sources = cols[1].multiselect("Lead source", sorted(df["lead_source"].dropna().unique()))
        temperatures = cols[2].multiselect("Temperature", ["Hot", "Warm", "Cold"])
        gtm = cols[3].multiselect("GTM stage", GTM_OPTIONS)
        sales = cols[4].multiselect("Sales stage", SALES_OPTIONS)

    filtered = df.copy()
    if search:
        mask = filtered[["name", "company", "email"]].astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]
    for column, values in [("industry", industries), ("lead_source", sources), ("temperature", temperatures), ("gtm_stage", gtm), ("sales_stage", sales)]:
        if values:
            filtered = filtered[filtered[column].isin(values)]

    st.caption(f"Showing {len(filtered)} of {len(df)} leads")
    table = filtered.copy()
    table["Lead ID"] = table["id"].map(lambda value: f"LD-{value:04d}")
    table["Budget"] = table["budget"].map(format_inr)
    table["Deal Value"] = table["deal_value"].map(format_inr)
    last_contacted = pd.to_datetime(table["last_contacted"])
    inactive_days = (pd.Timestamp.today().normalize() - last_contacted.dt.normalize()).dt.days
    table["Follow-up Status"] = "Current"
    table.loc[(inactive_days > 2) & (table["gtm_stage"] != "Closed Won"), "Follow-up Status"] = "Overdue"
    table.loc[table["gtm_stage"] == "Closed Won", "Follow-up Status"] = "Complete"
    table = table.rename(columns={
        "name": "Name", "company": "Company", "email": "Email", "phone": "Phone",
        "industry": "Industry", "job_title": "Job Title", "company_size": "Company Size",
        "lead_source": "Lead Source", "lead_score": "Lead Score", "temperature": "Temperature",
        "gtm_stage": "GTM Stage", "sales_stage": "Sales Stage", "last_contacted": "Last Contacted",
    })
    columns = ["Lead ID", "Name", "Company", "Email", "Phone", "Industry", "Job Title", "Company Size", "Lead Source", "Budget", "Lead Score", "Temperature", "GTM Stage", "Sales Stage", "Deal Value", "Last Contacted", "Follow-up Status"]
    st.dataframe(table[columns], width="stretch", hide_index=True, height=550)


def lead_details_page(df: pd.DataFrame) -> None:
    section_intro("Account intelligence", "Lead Details", "Review qualification signals, account context, and the next sales action.")
    if df.empty:
        st.info("No leads are available yet.")
        return
    options = {f"LD-{row.id:04d} · {row.name} — {row.company}": int(row.id) for row in df.itertuples()}
    labels = list(options)
    default = 0
    selected_id = st.session_state.get("selected_lead_id")
    if selected_id in options.values():
        default = list(options.values()).index(selected_id)
    label = st.selectbox("Select a lead", labels, index=default)
    lead = get_lead(options[label])
    st.session_state.selected_lead_id = lead["id"]
    score, breakdown = calculate_lead_score(lead["company_size"], lead["job_title"], lead["budget"], lead["lead_source"])

    st.markdown(
        f"<div class='profile-head'><h2>{lead['name']}</h2><p>{lead['job_title']} at {lead['company']} · LD-{lead['id']:04d}</p></div>",
        unsafe_allow_html=True,
    )
    a, b, c, d, e = st.columns(5)
    a.metric("Lead Score", lead["lead_score"])
    b.markdown(f"<div class='detail-label'>Temperature</div><div style='margin-top:.55rem'>{temperature_badge(lead['temperature'])}</div>", unsafe_allow_html=True)
    c.metric("GTM Stage", lead["gtm_stage"])
    d.metric("Sales Stage", lead["sales_stage"])
    e.metric("Deal Value", format_inr(lead["deal_value"]))

    info, qualification = st.columns([1.55, 1])
    with info:
        st.markdown("### CRM profile")
        left, right = st.columns(2)
        items = [
            ("Email", lead["email"]), ("Phone", lead["phone"] or "—"),
            ("Company", lead["company"]), ("Industry", lead["industry"]),
            ("Company Size", f"{lead['company_size']:,} employees"), ("Job Title", lead["job_title"]),
            ("Lead Source", lead["lead_source"]), ("Budget", format_inr(lead["budget"])),
            ("Last Contacted", lead["last_contacted"]), ("Created", lead["created_at"]),
        ]
        for index, (key, value) in enumerate(items):
            target = left if index % 2 == 0 else right
            target.markdown(f"<div class='detail-label'>{key}</div><div class='detail-value'>{value}</div>", unsafe_allow_html=True)
    with qualification:
        st.markdown("### Why this lead received this score")
        rows = "".join(f"<div class='score-row'><span>{key}</span><strong>+{value}</strong></div>" for key, value in breakdown.items())
        st.markdown(f"<div class='panel'>{rows}<div class='score-total'><span>Total score</span><span>{score} / 100</span></div></div>", unsafe_allow_html=True)
        st.caption("The score is recalculated from company size, buyer role, budget, and acquisition source.")

    st.markdown("### Update pipeline position")
    with st.form(f"stage_form_{lead['id']}"):
        x, y, z = st.columns([1, 1, .6])
        new_gtm = x.selectbox("GTM stage", GTM_OPTIONS, index=GTM_OPTIONS.index(lead["gtm_stage"]))
        new_sales = y.selectbox("Sales stage", SALES_OPTIONS, index=SALES_OPTIONS.index(lead["sales_stage"]) if lead["sales_stage"] in SALES_OPTIONS else 0)
        submitted = z.form_submit_button("Save changes", width="stretch")
        if submitted:
            update_lead_stages(lead["id"], new_gtm, new_sales)
            st.success("Pipeline position updated.")
            st.rerun()


def pipeline_page(df: pd.DataFrame) -> None:
    section_intro("Deal desk", "Sales Pipeline", "Track active deal value and inspect accounts at each GTM stage.")
    open_df = df[df["gtm_stage"].isin(OPEN_STAGES)]
    metrics = dashboard_metrics(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Open pipeline", format_inr(metrics["Pipeline Value"]))
    c2.metric("Active opportunities", len(open_df))
    average = open_df["deal_value"].mean() if len(open_df) else 0
    c3.metric("Average deal size", format_inr(average))

    pipeline = df.groupby("gtm_stage", as_index=False)["deal_value"].sum()
    pipeline["gtm_stage"] = pd.Categorical(pipeline["gtm_stage"], categories=GTM_OPTIONS, ordered=True)
    pipeline = pipeline.sort_values("gtm_stage")
    fig = px.bar(pipeline, x="gtm_stage", y="deal_value", color="gtm_stage", title="Deal value across the GTM funnel", color_discrete_sequence=px.colors.sequential.Purples[2:])
    fig.update_yaxes(tickprefix="₹")
    st.plotly_chart(style_chart(fig, 370), width="stretch", config={"displayModeBar": False})

    tabs = st.tabs(GTM_OPTIONS)
    for tab, stage in zip(tabs, GTM_OPTIONS):
        with tab:
            subset = df[df["gtm_stage"] == stage].copy()
            st.caption(f"{len(subset)} leads · {format_inr(subset['deal_value'].sum())} total deal value")
            if subset.empty:
                st.info(f"No leads are currently in {stage}.")
            else:
                subset["Deal Value"] = subset["deal_value"].map(format_inr)
                subset = subset.rename(columns={"company": "Company", "name": "Lead", "sales_stage": "Sales Stage", "lead_score": "Lead Score", "last_contacted": "Last Contacted"})
                st.dataframe(subset[["Company", "Lead", "Deal Value", "Sales Stage", "Lead Score", "Last Contacted"]], hide_index=True, width="stretch")


def followups_page(df: pd.DataFrame) -> None:
    section_intro("Sales SLA", "Follow-ups", "Prioritised leads that have not been contacted in more than two days.")
    overdue = overdue_followups(df)
    high = int((overdue["Priority"] == "High").sum()) if len(overdue) else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Follow-up required", len(overdue))
    c2.metric("High priority", high)
    c3.metric("Value needing attention", format_inr(overdue["deal_value"].sum()))
    if overdue.empty:
        st.success("All follow-ups are current. Nice work.")
        return
    priority_filter = st.segmented_control("Priority", ["All", "High", "Medium", "Low"], default="All")
    if priority_filter and priority_filter != "All":
        overdue = overdue[overdue["Priority"] == priority_filter]
    for _, row in overdue.iterrows():
        left, right = st.columns([5, 1])
        with left:
            st.markdown(
                f"<div class='follow-card'><h4>{row['company']}</h4><div class='follow-meta'>{row['name']} · Score {row['lead_score']} · {format_inr(row['deal_value'])} · Last contacted {row['last_contacted'].strftime('%d %b %Y')}</div>"
                f"<div style='margin-top:.5rem'><strong>{row['Priority'].upper()} PRIORITY</strong> · {int(row['Days Since Contact'])} days inactive</div></div>",
                unsafe_allow_html=True,
            )
        with right:
            if st.button("Mark contacted", key=f"contact_{row['id']}", width="stretch"):
                mark_contacted(int(row["id"]), date.today().isoformat())
                st.toast(f"{row['name']} marked as contacted.")
                st.rerun()


def analytics_page(df: pd.DataFrame) -> None:
    section_intro("Performance insights", "Analytics", "Understand acquisition quality, funnel conversion, and revenue contribution.")
    performance = source_performance(df)
    st.markdown("### Lead source performance")
    if not performance.empty:
        display = performance.copy()
        display["Revenue"] = display["Revenue"].map(format_inr)
        st.dataframe(display, hide_index=True, width="stretch")

    left, right = st.columns(2)
    conversions = funnel_conversions(df)
    fig = px.bar(conversions, x="Conversion %", y="Funnel Step", orientation="h", text="Conversion %", title="Funnel conversion", color_discrete_sequence=["#7F56D9"])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_xaxes(range=[0, max(105, conversions["Conversion %"].max() + 10)], ticksuffix="%")
    left.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})

    revenue = df[df["gtm_stage"] == "Closed Won"].groupby("industry", as_index=False)["deal_value"].sum().sort_values("deal_value")
    fig = px.bar(revenue, x="deal_value", y="industry", orientation="h", title="Won revenue by industry", color_discrete_sequence=["#12B76A"])
    fig.update_xaxes(tickprefix="₹")
    right.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})

    left, right = st.columns(2)
    stage = df.groupby("sales_stage", as_index=False)["deal_value"].sum()
    fig = px.bar(stage, x="sales_stage", y="deal_value", title="Pipeline by sales stage", color="sales_stage", color_discrete_sequence=px.colors.sequential.Purples[2:])
    fig.update_yaxes(tickprefix="₹")
    left.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})

    temperature = df.groupby("temperature", as_index=False).size().rename(columns={"size": "Leads"})
    fig = px.pie(temperature, names="temperature", values="Leads", hole=.58, title="Lead temperature distribution", color="temperature", color_discrete_map={"Hot": "#F04438", "Warm": "#F79009", "Cold": "#2E90FA"})
    right.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})


def add_lead_page() -> None:
    section_intro("Lead capture", "Add Lead", "Create a CRM record and qualify it automatically using transparent business rules.")
    with st.form("add_lead_form", clear_on_submit=False):
        st.markdown("### Contact & company")
        a, b, c = st.columns(3)
        name = a.text_input("Name *", placeholder="e.g. Maya Raman")
        email = b.text_input("Work email *", placeholder="maya@company.example")
        phone = c.text_input("Phone", placeholder="+91 90000 00000")
        a, b, c = st.columns(3)
        company = a.text_input("Company name *", placeholder="e.g. Acme Systems")
        industry = b.selectbox("Industry *", INDUSTRY_OPTIONS)
        company_size = c.number_input("Company size (employees) *", min_value=1, value=100, step=10)

        st.markdown("### Qualification & sales")
        a, b, c = st.columns(3)
        job_title = a.text_input("Job title *", placeholder="e.g. VP Sales")
        lead_source = b.selectbox("Lead source *", SOURCE_OPTIONS)
        budget = c.number_input("Budget (₹) *", min_value=0, value=100_000, step=10_000)
        a, b, c = st.columns(3)
        deal_value = a.number_input("Expected deal value (₹) *", min_value=0, value=75_000, step=5_000)
        gtm_stage = b.selectbox("GTM stage", GTM_OPTIONS)
        sales_stage = c.selectbox("Sales stage", SALES_OPTIONS)
        last_contacted = st.date_input("Last contacted", value=date.today(), max_value=date.today())

        score, breakdown = calculate_lead_score(int(company_size), job_title or "Other", float(budget), lead_source)
        st.info(f"Estimated lead score: {score}/100 · {lead_temperature(score)}. The final score is calculated when you save the lead.")
        submitted = st.form_submit_button("Add lead", type="primary", width="stretch")
        if submitted:
            errors = []
            if not name.strip(): errors.append("Name is required.")
            if not email.strip() or "@" not in email: errors.append("A valid work email is required.")
            if not company.strip(): errors.append("Company name is required.")
            if not job_title.strip(): errors.append("Job title is required.")
            if errors:
                for error in errors:
                    st.error(error)
            else:
                score, _ = calculate_lead_score(int(company_size), job_title, float(budget), lead_source)
                record = {
                    "name": name.strip(), "email": email.strip().lower(), "phone": phone.strip(),
                    "company": company.strip(), "industry": industry, "job_title": job_title.strip(),
                    "company_size": int(company_size), "lead_source": lead_source, "budget": float(budget),
                    "lead_score": score, "temperature": lead_temperature(score), "gtm_stage": gtm_stage,
                    "sales_stage": sales_stage, "deal_value": float(deal_value),
                    "last_contacted": last_contacted.isoformat(), "created_at": datetime.now().isoformat(timespec="seconds"),
                }
                try:
                    lead_id = add_lead(record)
                    st.session_state.selected_lead_id = lead_id
                    st.success(f"{name} was added as LD-{lead_id:04d} with a score of {score}/100 ({lead_temperature(score)}).")
                except sqlite3.IntegrityError:
                    st.error("A lead with this email already exists.")


df = get_leads()
if page == "Dashboard":
    dashboard_page(df)
elif page == "Leads":
    leads_page(df)
elif page == "Lead Details":
    lead_details_page(df)
elif page == "Sales Pipeline":
    pipeline_page(df)
elif page == "Follow-ups":
    followups_page(df)
elif page == "Analytics":
    analytics_page(df)
else:
    add_lead_page()
