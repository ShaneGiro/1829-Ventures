from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import io
import csv
import uuid
import logging
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict

# -------- Setup --------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Venture Fund CRM")
api_router = APIRouter(prefix="/api")

JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

# -------- Utilities --------
def new_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email,
               "exp": datetime.now(timezone.utc) + timedelta(minutes=60 * 8),
               "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id,
               "exp": datetime.now(timezone.utc) + timedelta(days=7),
               "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def set_auth_cookies(response: Response, access: str, refresh: str):
    response.set_cookie("access_token", access, httponly=True, secure=True,
                        samesite="none", max_age=60 * 60 * 8, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True,
                        samesite="none", max_age=60 * 60 * 24 * 7, path="/")

def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# -------- Models --------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class Fund(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    slug: str
    vintage: Optional[int] = None
    committed_capital: float = 0.0
    created_at: str = Field(default_factory=now_iso)

class FundIn(BaseModel):
    name: str
    slug: str
    vintage: Optional[int] = None
    committed_capital: float = 0.0

class Company(BaseModel):
    id: str = Field(default_factory=new_id)
    fund_id: str
    name: str
    sector: Optional[str] = None
    stage: str = "sourced"  # sourced, screening, diligence, ic, invested, passed
    website: Optional[str] = None
    hq: Optional[str] = None
    description: Optional[str] = None
    one_liner: Optional[str] = None
    round_stage: Optional[str] = None  # Seed, Series A, etc
    ask_amount: Optional[float] = None
    lead_partner: Optional[str] = None
    source: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

class CompanyIn(BaseModel):
    fund_id: str
    name: str
    sector: Optional[str] = None
    stage: str = "sourced"
    website: Optional[str] = None
    hq: Optional[str] = None
    description: Optional[str] = None
    one_liner: Optional[str] = None
    round_stage: Optional[str] = None
    ask_amount: Optional[float] = None
    lead_partner: Optional[str] = None
    source: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    stage: Optional[str] = None
    website: Optional[str] = None
    hq: Optional[str] = None
    description: Optional[str] = None
    one_liner: Optional[str] = None
    round_stage: Optional[str] = None
    ask_amount: Optional[float] = None
    lead_partner: Optional[str] = None
    source: Optional[str] = None

class Contact(BaseModel):
    id: str = Field(default_factory=new_id)
    fund_id: str
    name: str
    role: Optional[str] = None  # founder, co-investor, lp, advisor
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)

class ContactIn(BaseModel):
    fund_id: str
    name: str
    role: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None

class Conversation(BaseModel):
    id: str = Field(default_factory=new_id)
    fund_id: str
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    date: str  # ISO date
    channel: Optional[str] = None  # call, email, meeting, etc
    attendees: Optional[str] = None
    summary: str
    next_steps: Optional[str] = None
    sentiment: Optional[str] = None  # positive, neutral, negative
    created_at: str = Field(default_factory=now_iso)

class ConversationIn(BaseModel):
    fund_id: str
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    date: str
    channel: Optional[str] = None
    attendees: Optional[str] = None
    summary: str
    next_steps: Optional[str] = None
    sentiment: Optional[str] = None

class Diligence(BaseModel):
    id: str = Field(default_factory=new_id)
    fund_id: str
    company_id: str
    category: str  # legal, financial, tech, market, team
    item: str
    owner: Optional[str] = None
    status: str = "not_started"  # not_started, in_progress, complete, blocked
    due_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)

class DiligenceIn(BaseModel):
    fund_id: str
    company_id: str
    category: str
    item: str
    owner: Optional[str] = None
    status: str = "not_started"
    due_date: Optional[str] = None
    notes: Optional[str] = None

class DiligenceUpdate(BaseModel):
    category: Optional[str] = None
    item: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None

class Investment(BaseModel):
    id: str = Field(default_factory=new_id)
    fund_id: str
    company_id: str
    amount: float
    round_stage: Optional[str] = None
    valuation: Optional[float] = None
    ownership_pct: Optional[float] = None
    close_date: Optional[str] = None
    board_seat: bool = False
    pro_rata: bool = False
    current_value: Optional[float] = None
    notes: Optional[str] = None
    cash_flows: List[dict] = Field(default_factory=list)  # [{date, amount, kind}]
    created_at: str = Field(default_factory=now_iso)

class InvestmentIn(BaseModel):
    fund_id: str
    company_id: str
    amount: float
    round_stage: Optional[str] = None
    valuation: Optional[float] = None
    ownership_pct: Optional[float] = None
    close_date: Optional[str] = None
    board_seat: bool = False
    pro_rata: bool = False
    current_value: Optional[float] = None
    notes: Optional[str] = None

class InvestmentUpdate(BaseModel):
    amount: Optional[float] = None
    round_stage: Optional[str] = None
    valuation: Optional[float] = None
    ownership_pct: Optional[float] = None
    close_date: Optional[str] = None
    board_seat: Optional[bool] = None
    pro_rata: Optional[bool] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None

class CashFlowIn(BaseModel):
    date: str
    amount: float  # negative = capital call, positive = distribution
    kind: Optional[str] = None  # "call" | "distribution" | "markup"

# -------- Auth Routes --------
@api_router.post("/auth/register")
async def register(payload: RegisterIn, response: Response):
    email = payload.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_doc = {
        "id": new_id(),
        "email": email,
        "name": payload.name,
        "password_hash": hash_password(payload.password),
        "role": "user",
        "created_at": now_iso(),
    }
    await db.users.insert_one(user_doc)
    access = create_access_token(user_doc["id"], email)
    refresh = create_refresh_token(user_doc["id"])
    set_auth_cookies(response, access, refresh)
    return {"id": user_doc["id"], "email": email, "name": payload.name, "role": "user"}

@api_router.post("/auth/login")
async def login(payload: LoginIn, response: Response, request: Request):
    email = payload.email.lower().strip()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"

    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if attempt and attempt.get("count", 0) >= 5:
        locked_until = attempt.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        new_count = (attempt.get("count", 0) + 1) if attempt else 1
        lock_until = None
        if new_count >= 5:
            lock_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$set": {"count": new_count, "locked_until": lock_until}},
            upsert=True,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await db.login_attempts.delete_one({"identifier": identifier})
    access = create_access_token(user["id"], email)
    refresh = create_refresh_token(user["id"])
    set_auth_cookies(response, access, refresh)
    return {"id": user["id"], "email": email, "name": user.get("name"), "role": user.get("role", "user")}

@api_router.post("/auth/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"ok": True}

@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        access = create_access_token(user["id"], user["email"])
        response.set_cookie("access_token", access, httponly=True, secure=True,
                            samesite="none", max_age=60 * 60 * 8, path="/")
        return {"ok": True}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# -------- Fund Routes --------
@api_router.get("/funds", response_model=List[Fund])
async def list_funds(user: dict = Depends(get_current_user)):
    docs = await db.funds.find({}, {"_id": 0}).sort("created_at", 1).to_list(100)
    return docs

@api_router.post("/funds", response_model=Fund)
async def create_fund(payload: FundIn, user: dict = Depends(get_current_user)):
    fund = Fund(**payload.model_dump())
    await db.funds.insert_one(fund.model_dump())
    return fund

# -------- Companies --------
@api_router.get("/companies", response_model=List[Company])
async def list_companies(fund_id: str = Query(...), user: dict = Depends(get_current_user)):
    docs = await db.companies.find({"fund_id": fund_id}, {"_id": 0}).sort("updated_at", -1).to_list(1000)
    return docs

@api_router.get("/companies/{company_id}", response_model=Company)
async def get_company(company_id: str, user: dict = Depends(get_current_user)):
    doc = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Company not found")
    return doc

@api_router.post("/companies", response_model=Company)
async def create_company(payload: CompanyIn, user: dict = Depends(get_current_user)):
    comp = Company(**payload.model_dump())
    await db.companies.insert_one(comp.model_dump())
    return comp

@api_router.patch("/companies/{company_id}", response_model=Company)
async def update_company(company_id: str, payload: CompanyUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = now_iso()
    result = await db.companies.update_one({"id": company_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    doc = await db.companies.find_one({"id": company_id}, {"_id": 0})
    return doc

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, user: dict = Depends(get_current_user)):
    await db.companies.delete_one({"id": company_id})
    await db.diligence.delete_many({"company_id": company_id})
    await db.investments.delete_many({"company_id": company_id})
    return {"ok": True}

# -------- Contacts --------
@api_router.get("/contacts", response_model=List[Contact])
async def list_contacts(fund_id: str = Query(...), company_id: Optional[str] = None,
                        user: dict = Depends(get_current_user)):
    q = {"fund_id": fund_id}
    if company_id:
        q["company_id"] = company_id
    docs = await db.contacts.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return docs

@api_router.post("/contacts", response_model=Contact)
async def create_contact(payload: ContactIn, user: dict = Depends(get_current_user)):
    c = Contact(**payload.model_dump())
    await db.contacts.insert_one(c.model_dump())
    return c

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, user: dict = Depends(get_current_user)):
    await db.contacts.delete_one({"id": contact_id})
    return {"ok": True}

# -------- Conversations --------
@api_router.get("/conversations", response_model=List[Conversation])
async def list_conversations(fund_id: str = Query(...), company_id: Optional[str] = None,
                             user: dict = Depends(get_current_user)):
    q = {"fund_id": fund_id}
    if company_id:
        q["company_id"] = company_id
    docs = await db.conversations.find(q, {"_id": 0}).sort("date", -1).to_list(1000)
    return docs

@api_router.post("/conversations", response_model=Conversation)
async def create_conversation(payload: ConversationIn, user: dict = Depends(get_current_user)):
    c = Conversation(**payload.model_dump())
    await db.conversations.insert_one(c.model_dump())
    return c

@api_router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user: dict = Depends(get_current_user)):
    await db.conversations.delete_one({"id": conv_id})
    return {"ok": True}

# -------- Diligence --------
@api_router.get("/diligence", response_model=List[Diligence])
async def list_diligence(fund_id: str = Query(...), company_id: Optional[str] = None,
                         user: dict = Depends(get_current_user)):
    q = {"fund_id": fund_id}
    if company_id:
        q["company_id"] = company_id
    docs = await db.diligence.find(q, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return docs

@api_router.post("/diligence", response_model=Diligence)
async def create_diligence(payload: DiligenceIn, user: dict = Depends(get_current_user)):
    d = Diligence(**payload.model_dump())
    await db.diligence.insert_one(d.model_dump())
    return d

@api_router.patch("/diligence/{item_id}", response_model=Diligence)
async def update_diligence(item_id: str, payload: DiligenceUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    result = await db.diligence.update_one({"id": item_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Diligence item not found")
    doc = await db.diligence.find_one({"id": item_id}, {"_id": 0})
    return doc

@api_router.delete("/diligence/{item_id}")
async def delete_diligence(item_id: str, user: dict = Depends(get_current_user)):
    await db.diligence.delete_one({"id": item_id})
    return {"ok": True}

# -------- Investments --------
@api_router.get("/investments", response_model=List[Investment])
async def list_investments(fund_id: str = Query(...), company_id: Optional[str] = None,
                           user: dict = Depends(get_current_user)):
    q = {"fund_id": fund_id}
    if company_id:
        q["company_id"] = company_id
    docs = await db.investments.find(q, {"_id": 0}).sort("close_date", -1).to_list(1000)
    return docs

@api_router.post("/investments", response_model=Investment)
async def create_investment(payload: InvestmentIn, user: dict = Depends(get_current_user)):
    inv = Investment(**payload.model_dump())
    # Seed initial cash flow (capital call) on close_date if provided
    if inv.close_date:
        inv.cash_flows = [{"date": inv.close_date, "amount": -abs(inv.amount), "kind": "call"}]
    await db.investments.insert_one(inv.model_dump())
    return inv

@api_router.patch("/investments/{inv_id}", response_model=Investment)
async def update_investment(inv_id: str, payload: InvestmentUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    result = await db.investments.update_one({"id": inv_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Investment not found")
    doc = await db.investments.find_one({"id": inv_id}, {"_id": 0})
    return doc

@api_router.post("/investments/{inv_id}/cash-flows", response_model=Investment)
async def add_cash_flow(inv_id: str, payload: CashFlowIn, user: dict = Depends(get_current_user)):
    doc = await db.investments.find_one({"id": inv_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Investment not found")
    flows = doc.get("cash_flows", []) or []
    flows.append({"date": payload.date, "amount": payload.amount, "kind": payload.kind or ("call" if payload.amount < 0 else "distribution")})
    flows.sort(key=lambda f: f["date"])
    await db.investments.update_one({"id": inv_id}, {"$set": {"cash_flows": flows}})
    updated = await db.investments.find_one({"id": inv_id}, {"_id": 0})
    return updated

@api_router.delete("/investments/{inv_id}/cash-flows/{idx}", response_model=Investment)
async def remove_cash_flow(inv_id: str, idx: int, user: dict = Depends(get_current_user)):
    doc = await db.investments.find_one({"id": inv_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Investment not found")
    flows = doc.get("cash_flows", []) or []
    if 0 <= idx < len(flows):
        flows.pop(idx)
    await db.investments.update_one({"id": inv_id}, {"$set": {"cash_flows": flows}})
    updated = await db.investments.find_one({"id": inv_id}, {"_id": 0})
    return updated

@api_router.delete("/investments/{inv_id}")
async def delete_investment(inv_id: str, user: dict = Depends(get_current_user)):
    await db.investments.delete_one({"id": inv_id})
    return {"ok": True}

# -------- IRR --------
def _xnpv(rate: float, flows: list) -> float:
    if not flows:
        return 0.0
    t0 = flows[0]["_t"]
    total = 0.0
    for f in flows:
        years = (f["_t"] - t0).days / 365.25
        total += f["amount"] / ((1 + rate) ** years)
    return total

def compute_xirr(cash_flows: list) -> Optional[float]:
    """Newton's method XIRR. cash_flows: [{date, amount}]"""
    if not cash_flows or len(cash_flows) < 2:
        return None
    parsed = []
    for f in cash_flows:
        try:
            parsed.append({"_t": datetime.fromisoformat(f["date"][:10]), "amount": float(f["amount"])})
        except Exception:
            return None
    parsed.sort(key=lambda x: x["_t"])
    # need at least one negative and one positive flow
    has_neg = any(p["amount"] < 0 for p in parsed)
    has_pos = any(p["amount"] > 0 for p in parsed)
    if not (has_neg and has_pos):
        return None
    rate = 0.1
    for _ in range(80):
        try:
            f = _xnpv(rate, parsed)
            # numerical derivative
            df = (_xnpv(rate + 1e-6, parsed) - f) / 1e-6
            if abs(df) < 1e-12:
                return None
            new_rate = rate - f / df
            if abs(new_rate - rate) < 1e-7:
                return round(new_rate, 6)
            rate = new_rate
            if rate <= -0.999:
                rate = -0.99
        except Exception:
            return None
    return None

# -------- Metrics --------
@api_router.get("/metrics/portfolio")
async def portfolio_metrics(fund_id: str = Query(...), user: dict = Depends(get_current_user)):
    fund = await db.funds.find_one({"id": fund_id}, {"_id": 0})
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    investments = await db.investments.find({"fund_id": fund_id}, {"_id": 0}).to_list(1000)
    companies = await db.companies.find({"fund_id": fund_id}, {"_id": 0}).to_list(1000)

    deployed = sum(i.get("amount", 0) or 0 for i in investments)
    current_val = sum((i.get("current_value") or i.get("amount", 0) or 0) for i in investments)
    moic = (current_val / deployed) if deployed > 0 else 0
    committed = fund.get("committed_capital", 0) or 0
    dry_powder = max(committed - deployed, 0)

    # Build fund-level cash flow list: existing flows + a synthetic mark-to-market outflow today for open positions
    all_flows = []
    today = datetime.now(timezone.utc).date().isoformat()
    for inv in investments:
        flows = inv.get("cash_flows") or []
        if flows:
            all_flows.extend(flows)
        else:
            # Fallback: use close_date as call, current_value as unrealized mark today
            if inv.get("close_date"):
                all_flows.append({"date": inv["close_date"], "amount": -abs(inv.get("amount", 0))})
        # Mark-to-market: add unrealized current_value as positive terminal flow (only if we have investment amount)
        cv = inv.get("current_value")
        if cv is not None and cv > 0:
            all_flows.append({"date": today, "amount": float(cv), "kind": "unrealized_mark"})

    fund_irr = compute_xirr(all_flows) if all_flows else None

    stage_breakdown = {}
    for c in companies:
        stage_breakdown[c.get("stage", "sourced")] = stage_breakdown.get(c.get("stage", "sourced"), 0) + 1

    sector_breakdown = {}
    for c in companies:
        if c.get("stage") == "invested":
            s = c.get("sector") or "Unknown"
            sector_breakdown[s] = sector_breakdown.get(s, 0) + 1

    return {
        "fund": fund,
        "deployed_capital": deployed,
        "committed_capital": committed,
        "dry_powder": dry_powder,
        "current_value": current_val,
        "moic": round(moic, 2),
        "irr": fund_irr,
        "num_investments": len(investments),
        "num_companies": len(companies),
        "num_invested_companies": len([c for c in companies if c.get("stage") == "invested"]),
        "stage_breakdown": stage_breakdown,
        "sector_breakdown": sector_breakdown,
    }

# -------- Dealroom CSV Import --------
DEALROOM_STAGE_MAP = {
    "seed": "screening",
    "series a": "diligence",
    "series b": "diligence",
    "series c": "diligence",
    "series d": "diligence",
    "growth": "diligence",
    "mature": "invested",
    "late growth": "diligence",
    "early growth": "diligence",
    "grown": "invested",
}

def _clean(v: str) -> str:
    return (v or "").strip()

def _parse_float(v: str) -> Optional[float]:
    if not v: return None
    try:
        return float(str(v).replace(",", "").replace("$", ""))
    except Exception:
        return None

@api_router.post("/import/dealroom")
async def import_dealroom(
    fund_id: str = Form(...),
    default_stage: str = Form("sourced"),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    fund = await db.funds.find_one({"id": fund_id})
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    # Dealroom exports have 2 metadata rows before the header. Detect the header row by looking for 'Name' as the 2nd column.
    header_idx = -1
    for i, r in enumerate(rows[:10]):
        if len(r) > 1 and r[0].strip().lower() == "id" and r[1].strip().lower() == "name":
            header_idx = i
            break
    if header_idx == -1:
        # Fallback: assume first row
        header_idx = 0
    headers = [h.strip() for h in rows[header_idx]]
    data_rows = rows[header_idx + 1:]

    def col(row, name):
        try:
            idx = headers.index(name)
            return row[idx] if idx < len(row) else ""
        except ValueError:
            return ""

    imported = 0
    updated = 0
    skipped = 0
    errors = []

    for r in data_rows:
        try:
            name = _clean(col(r, "Name"))
            if not name:
                skipped += 1
                continue

            dealroom_url = _clean(col(r, "Dealroom URL"))
            website = _clean(col(r, "Website"))
            tagline = _clean(col(r, "Tagline"))
            long_desc = _clean(col(r, "Long description"))
            industries = _clean(col(r, "Industries"))
            sub_industries = _clean(col(r, "Sub industries"))
            hq_city = _clean(col(r, "HQ city"))
            hq_country = _clean(col(r, "HQ country"))
            hq = ", ".join([x for x in [hq_city, hq_country] if x])
            last_round = _clean(col(r, "Last round"))
            growth_stage = _clean(col(r, "Growth stage")).lower()
            total_funding = _parse_float(col(r, "Total funding (USD M)"))
            last_amount = _parse_float(col(r, "Last funding amount"))
            valuation_usd = _parse_float(col(r, "Valuation (USD)"))
            investors_names = _clean(col(r, "Investors names"))
            founders = _clean(col(r, "Founders"))
            linkedin = _clean(col(r, "LinkedIn"))

            sector = industries.split(";")[0].strip() if industries else (sub_industries.split(";")[0].strip() if sub_industries else None)
            mapped_stage = DEALROOM_STAGE_MAP.get(growth_stage) or default_stage

            existing = await db.companies.find_one({"fund_id": fund_id, "name": name})

            if existing:
                updates = {
                    "sector": sector or existing.get("sector"),
                    "website": website or existing.get("website"),
                    "hq": hq or existing.get("hq"),
                    "one_liner": tagline or existing.get("one_liner"),
                    "description": long_desc or existing.get("description"),
                    "round_stage": last_round or existing.get("round_stage"),
                    "ask_amount": last_amount * 1_000_000 if last_amount and (col(r, "Last funding amount") == col(r, "Last funding amount")) else existing.get("ask_amount"),
                    "source": "Dealroom",
                    "dealroom_url": dealroom_url or existing.get("dealroom_url"),
                    "dealroom_total_funding_usd_m": total_funding,
                    "dealroom_valuation_usd": valuation_usd,
                    "dealroom_investors": investors_names,
                    "dealroom_founders": founders,
                    "linkedin": linkedin or existing.get("linkedin"),
                    "updated_at": now_iso(),
                }
                updates = {k: v for k, v in updates.items() if v is not None and v != ""}
                await db.companies.update_one({"id": existing["id"]}, {"$set": updates})
                updated += 1
            else:
                comp = Company(
                    fund_id=fund_id,
                    name=name,
                    sector=sector,
                    stage=mapped_stage,
                    website=website or None,
                    hq=hq or None,
                    one_liner=tagline or None,
                    description=long_desc or None,
                    round_stage=last_round or None,
                    ask_amount=(last_amount * 1_000_000) if last_amount is not None else None,
                    source="Dealroom",
                )
                doc = comp.model_dump()
                doc["dealroom_url"] = dealroom_url or None
                doc["dealroom_total_funding_usd_m"] = total_funding
                doc["dealroom_valuation_usd"] = valuation_usd
                doc["dealroom_investors"] = investors_names or None
                doc["dealroom_founders"] = founders or None
                doc["linkedin"] = linkedin or None
                await db.companies.insert_one(doc)
                imported += 1
        except Exception as e:
            errors.append(f"{name if 'name' in locals() else '?'}: {str(e)[:120]}")
            skipped += 1

    return {"imported": imported, "updated": updated, "skipped": skipped, "errors": errors[:20], "total_rows": len(data_rows)}

# -------- LP Report CSV Export --------
@api_router.get("/export/lp-report")
async def export_lp_report(fund_id: str = Query(...), user: dict = Depends(get_current_user)):
    fund = await db.funds.find_one({"id": fund_id}, {"_id": 0})
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    investments = await db.investments.find({"fund_id": fund_id}, {"_id": 0}).to_list(1000)
    companies = {c["id"]: c for c in await db.companies.find({"fund_id": fund_id}, {"_id": 0}).to_list(1000)}

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([f"Fund: {fund['name']}", f"Vintage: {fund.get('vintage','')}", f"Committed: {fund.get('committed_capital',0)}", f"Generated: {now_iso()}"])
    w.writerow([])
    w.writerow(["Company", "Sector", "Round", "Amount", "Valuation", "Ownership %", "Close Date", "Current Value", "MOIC", "IRR", "Board Seat", "Pro-rata"])
    for inv in investments:
        c = companies.get(inv["company_id"], {})
        amt = inv.get("amount") or 0
        cv = inv.get("current_value")
        moic = (cv / amt) if (amt and cv is not None) else ""
        irr = compute_xirr(inv.get("cash_flows") or []) if inv.get("cash_flows") else None
        w.writerow([
            c.get("name", ""), c.get("sector", ""), inv.get("round_stage", ""),
            amt, inv.get("valuation", ""), inv.get("ownership_pct", ""),
            inv.get("close_date", ""), cv if cv is not None else "",
            round(moic, 2) if isinstance(moic, float) else "",
            f"{irr*100:.2f}%" if irr is not None else "",
            "Yes" if inv.get("board_seat") else "No",
            "Yes" if inv.get("pro_rata") else "No",
        ])
    out.seek(0)
    filename = f"lp-report-{fund['slug']}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

# -------- Search --------
@api_router.get("/search")
async def global_search(q: str = Query(..., min_length=1), fund_id: str = Query(...),
                        user: dict = Depends(get_current_user)):
    regex = {"$regex": q, "$options": "i"}
    companies = await db.companies.find(
        {"fund_id": fund_id, "$or": [{"name": regex}, {"description": regex}, {"one_liner": regex}]},
        {"_id": 0}
    ).limit(10).to_list(10)
    contacts = await db.contacts.find(
        {"fund_id": fund_id, "$or": [{"name": regex}, {"email": regex}, {"title": regex}]},
        {"_id": 0}
    ).limit(10).to_list(10)
    conversations = await db.conversations.find(
        {"fund_id": fund_id, "$or": [{"summary": regex}, {"next_steps": regex}, {"attendees": regex}]},
        {"_id": 0}
    ).limit(10).to_list(10)
    return {"companies": companies, "contacts": contacts, "conversations": conversations}

@api_router.get("/")
async def root():
    return {"service": "Venture Fund CRM", "version": "1.0.0"}

# -------- Startup --------
async def seed_admin_and_funds():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@fund.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "id": new_id(),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Fund Admin",
            "role": "admin",
            "created_at": now_iso(),
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )

    # Seed default funds
    if not await db.funds.find_one({"slug": "beta"}):
        beta = Fund(name="Beta Fund", slug="beta", vintage=2024, committed_capital=5_000_000)
        await db.funds.insert_one(beta.model_dump())
    if not await db.funds.find_one({"slug": "fund-i"}):
        fund1 = Fund(name="Fund I", slug="fund-i", vintage=2025, committed_capital=25_000_000)
        await db.funds.insert_one(fund1.model_dump())

@app.on_event("startup")
async def on_startup():
    await db.users.create_index("email", unique=True)
    await db.companies.create_index("fund_id")
    await db.contacts.create_index("fund_id")
    await db.conversations.create_index("fund_id")
    await db.diligence.create_index([("fund_id", 1), ("company_id", 1)])
    await db.investments.create_index([("fund_id", 1), ("company_id", 1)])
    await db.login_attempts.create_index("identifier")
    await seed_admin_and_funds()

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ.get('FRONTEND_URL', 'http://localhost:3000')],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
