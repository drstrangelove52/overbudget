from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import SessionLocal
from app.dependencies import get_current_user
from app.routers import accounts, auth, backup, budgets, documents, health, rules, transactions
from app.services.auth import seed_credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_credentials(db)
    finally:
        db.close()
    yield


app = FastAPI(title="OverBudget API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth = [Depends(get_current_user)]

app.include_router(health.router, tags=["system"])
app.include_router(auth.router)
app.include_router(accounts.router, dependencies=_auth)
app.include_router(transactions.router, dependencies=_auth)
app.include_router(documents.router, dependencies=_auth)
app.include_router(rules.router, dependencies=_auth)
app.include_router(budgets.router, dependencies=_auth)
app.include_router(backup.router, dependencies=_auth)
