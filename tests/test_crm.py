"""Core workflow tests using only Python's standard unittest runner."""

from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

import analytics
import database
from scoring import calculate_lead_score, lead_temperature


class CRMWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.original_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "test_crm.db"
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_database_seeds_realistic_demo_data(self):
        leads = database.get_leads()
        self.assertEqual(len(leads), 50)
        self.assertGreater(leads["company"].nunique(), 15)
        self.assertTrue(set(leads["temperature"]).issubset({"Hot", "Warm", "Cold"}))
        metrics = analytics.dashboard_metrics(leads)
        self.assertEqual(metrics["Total Leads"], 50)
        self.assertGreater(metrics["Pipeline Value"], 0)
        self.assertGreater(metrics["Won Revenue"], 0)

    def test_scoring_is_transparent_and_capped(self):
        score, breakdown = calculate_lead_score(900, "CEO", 750_000, "Demo Request")
        self.assertEqual(score, 100)
        self.assertEqual(sum(breakdown.values()), 100)
        self.assertEqual(lead_temperature(score), "Hot")
        cold_score, _ = calculate_lead_score(20, "Analyst", 20_000, "Cold Outreach")
        self.assertEqual(cold_score, 20)
        self.assertEqual(lead_temperature(cold_score), "Cold")

    def test_add_update_and_followup_workflow(self):
        score, _ = calculate_lead_score(600, "Founder", 800_000, "Referral")
        record = {
            "name": "Demo Buyer", "email": "demo.buyer@test.example", "phone": "",
            "company": "Demo Systems", "industry": "SaaS", "job_title": "Founder",
            "company_size": 600, "lead_source": "Referral", "budget": 800_000,
            "lead_score": score, "temperature": lead_temperature(score),
            "gtm_stage": "Opportunity", "sales_stage": "Proposal", "deal_value": 600_000,
            "last_contacted": (date.today() - timedelta(days=8)).isoformat(),
            "created_at": date.today().isoformat(),
        }
        lead_id = database.add_lead(record)
        self.assertEqual(len(database.get_leads()), 51)
        overdue_ids = set(analytics.overdue_followups(database.get_leads())["id"])
        self.assertIn(lead_id, overdue_ids)

        database.mark_contacted(lead_id, date.today().isoformat())
        overdue_ids = set(analytics.overdue_followups(database.get_leads())["id"])
        self.assertNotIn(lead_id, overdue_ids)

        database.update_lead_stages(lead_id, "Closed Won", "Closed Won")
        updated = database.get_lead(lead_id)
        self.assertEqual(updated["gtm_stage"], "Closed Won")
        self.assertEqual(updated["sales_stage"], "Closed Won")

    def test_analytics_and_filter_inputs_are_consistent(self):
        leads = database.get_leads()
        performance = analytics.source_performance(leads)
        self.assertEqual(int(performance["Number of Leads"].sum()), 50)
        conversions = analytics.funnel_conversions(leads)
        self.assertEqual(len(conversions), 4)
        self.assertTrue(conversions["Conversion %"].between(0, 100).all())
        # The same boolean masks used by the UI filters must return valid subsets.
        filtered = leads[(leads["industry"] == leads.iloc[0]["industry"]) & (leads["temperature"] == leads.iloc[0]["temperature"])]
        self.assertTrue(set(filtered["industry"]) <= {leads.iloc[0]["industry"]})


if __name__ == "__main__":
    unittest.main()

