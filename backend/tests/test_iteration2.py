"""Iteration 2 backend tests: Dealroom import, LP export, IRR, cash flows, inline edit."""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://venture-crm-2.preview.emergentagent.com').rstrip('/')
ADMIN_EMAIL = "admin@fund.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def funds(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/funds")
    assert r.status_code == 200
    data = r.json()
    return {f["slug"]: f for f in data}


@pytest.fixture(scope="module")
def fund_i(funds):
    return funds["fund-i"]


@pytest.fixture(scope="module")
def beta_fund(funds):
    return funds["beta"]


# ---- Metrics + IRR
class TestMetrics:
    def test_metrics_has_irr_field(self, auth_session, beta_fund):
        r = auth_session.get(f"{BASE_URL}/api/metrics/portfolio", params={"fund_id": beta_fund["id"]})
        assert r.status_code == 200
        data = r.json()
        assert "irr" in data
        assert "deployed_capital" in data
        assert "dry_powder" in data
        assert "moic" in data
        assert "num_investments" in data


# ---- Investments + Cash flows + IRR compute
class TestInvestmentCashFlows:
    company_id = None
    inv_id = None

    def test_create_company_for_investment(self, auth_session, fund_i):
        r = auth_session.post(f"{BASE_URL}/api/companies", json={
            "fund_id": fund_i["id"], "name": "TEST_IRR_Co", "stage": "invested", "sector": "SaaS"
        })
        assert r.status_code == 200
        TestInvestmentCashFlows.company_id = r.json()["id"]

    def test_create_investment_seeds_call(self, auth_session, fund_i):
        assert TestInvestmentCashFlows.company_id
        r = auth_session.post(f"{BASE_URL}/api/investments", json={
            "fund_id": fund_i["id"],
            "company_id": TestInvestmentCashFlows.company_id,
            "amount": 100000,
            "close_date": "2023-01-15",
            "round_stage": "Seed",
            "current_value": 150000,
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["amount"] == 100000
        assert isinstance(data["cash_flows"], list)
        assert len(data["cash_flows"]) == 1
        cf = data["cash_flows"][0]
        assert cf["amount"] == -100000
        assert cf["kind"] == "call"
        TestInvestmentCashFlows.inv_id = data["id"]

    def test_add_distribution_cash_flow(self, auth_session):
        assert TestInvestmentCashFlows.inv_id
        r = auth_session.post(
            f"{BASE_URL}/api/investments/{TestInvestmentCashFlows.inv_id}/cash-flows",
            json={"date": "2024-06-01", "amount": 50000, "kind": "distribution"},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["cash_flows"]) == 2
        assert any(f["amount"] == 50000 for f in data["cash_flows"])

    def test_patch_investment_current_value(self, auth_session):
        r = auth_session.patch(
            f"{BASE_URL}/api/investments/{TestInvestmentCashFlows.inv_id}",
            json={"current_value": 200000},
        )
        assert r.status_code == 200
        assert r.json()["current_value"] == 200000

    def test_irr_computed_after_flows(self, auth_session, fund_i):
        r = auth_session.get(f"{BASE_URL}/api/metrics/portfolio", params={"fund_id": fund_i["id"]})
        assert r.status_code == 200
        data = r.json()
        assert data["irr"] is not None
        assert isinstance(data["irr"], (int, float))

    def test_remove_cash_flow(self, auth_session):
        r = auth_session.delete(
            f"{BASE_URL}/api/investments/{TestInvestmentCashFlows.inv_id}/cash-flows/1"
        )
        assert r.status_code == 200
        assert len(r.json()["cash_flows"]) == 1

    def test_cleanup_investment(self, auth_session):
        r = auth_session.delete(f"{BASE_URL}/api/investments/{TestInvestmentCashFlows.inv_id}")
        assert r.status_code == 200
        auth_session.delete(f"{BASE_URL}/api/companies/{TestInvestmentCashFlows.company_id}")


# ---- Company inline edit (PATCH)
class TestCompanyPatch:
    company_id = None

    def test_create_company(self, auth_session, fund_i):
        r = auth_session.post(f"{BASE_URL}/api/companies", json={
            "fund_id": fund_i["id"], "name": "TEST_PatchCo"
        })
        assert r.status_code == 200
        TestCompanyPatch.company_id = r.json()["id"]

    def test_patch_multiple_fields_and_persist(self, auth_session):
        cid = TestCompanyPatch.company_id
        r = auth_session.patch(f"{BASE_URL}/api/companies/{cid}", json={
            "sector": "FinTech", "round_stage": "Series A", "hq": "SF, USA",
            "website": "https://test.co", "lead_partner": "Alice", "source": "Referral",
            "ask_amount": 5000000,
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["sector"] == "FinTech"
        # verify persistence
        g = auth_session.get(f"{BASE_URL}/api/companies/{cid}")
        assert g.status_code == 200
        gd = g.json()
        assert gd["sector"] == "FinTech"
        assert gd["round_stage"] == "Series A"
        assert gd["hq"] == "SF, USA"
        assert gd["website"] == "https://test.co"
        assert gd["lead_partner"] == "Alice"
        assert gd["source"] == "Referral"
        assert gd["ask_amount"] == 5000000

    def test_cleanup(self, auth_session):
        auth_session.delete(f"{BASE_URL}/api/companies/{TestCompanyPatch.company_id}")


# ---- LP Report CSV Export
class TestLPExport:
    def test_lp_report_csv(self, auth_session, beta_fund):
        r = auth_session.get(f"{BASE_URL}/api/export/lp-report", params={"fund_id": beta_fund["id"]})
        assert r.status_code == 200
        ctype = r.headers.get("content-type", "")
        assert "text/csv" in ctype, f"Wrong content-type: {ctype}"
        body = r.text
        assert "Company,Sector,Round,Amount,Valuation" in body
        assert f"Fund: {beta_fund['name']}" in body


# ---- Dealroom import (small CSV)
DEALROOM_SAMPLE = """URL,Filters
https://x,y
ID,Name,Dealroom URL,Website,Tagline,Long description,HQ city,HQ country,Industries,Sub industries,Total funding (USD M),Last round,Last funding amount,Growth stage,Investors names,Founders,LinkedIn,Valuation (USD)
1,TEST_DR_Alpha,https://dr/alpha,https://alpha.co,Alpha tagline,Alpha long desc,Boston,USA,SaaS,B2B,2.5,Seed,500000,seed,Acme VC,Jane Doe,https://linkedin/alpha,10000000
2,TEST_DR_Beta,https://dr/beta,https://beta.co,Beta tagline,Beta long desc,NYC,USA,FinTech,,10.0,Series A,3000000,series a,Big VC,John Smith,https://linkedin/beta,50000000
"""


class TestDealroomImport:
    def test_import_small_csv(self, auth_session, fund_i):
        files = {"file": ("dealroom.csv", DEALROOM_SAMPLE.encode("utf-8"), "text/csv")}
        data = {"fund_id": fund_i["id"], "default_stage": "sourced"}
        r = auth_session.post(f"{BASE_URL}/api/import/dealroom", files=files, data=data)
        assert r.status_code == 200, r.text
        res = r.json()
        assert "imported" in res
        assert "updated" in res
        assert "skipped" in res
        assert (res["imported"] + res["updated"]) >= 2

    def test_reimport_updates(self, auth_session, fund_i):
        files = {"file": ("dealroom.csv", DEALROOM_SAMPLE.encode("utf-8"), "text/csv")}
        data = {"fund_id": fund_i["id"], "default_stage": "sourced"}
        r = auth_session.post(f"{BASE_URL}/api/import/dealroom", files=files, data=data)
        assert r.status_code == 200
        res = r.json()
        assert res["updated"] >= 2

    def test_imported_company_has_dealroom_fields(self, auth_session, fund_i):
        r = auth_session.get(f"{BASE_URL}/api/companies", params={"fund_id": fund_i["id"]})
        assert r.status_code == 200
        comps = r.json()
        alpha = next((c for c in comps if c.get("name") == "TEST_DR_Alpha"), None)
        assert alpha is not None
        assert alpha.get("source") == "Dealroom"
        assert alpha.get("sector") == "SaaS"

    def test_cleanup(self, auth_session, fund_i):
        r = auth_session.get(f"{BASE_URL}/api/companies", params={"fund_id": fund_i["id"]})
        for c in r.json():
            if c.get("name", "").startswith("TEST_DR_"):
                auth_session.delete(f"{BASE_URL}/api/companies/{c['id']}")
