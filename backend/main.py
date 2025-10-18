from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from services.auth.router import router as auth_router
from services.account.router import router as account_router
from services.transaction.router import router as transaction_router
from services.product.router import router as product_router
from faceid.router import router as faceid_router
from rag_agent.routes.router import router as rag_router
from database import Base, engine


app = FastAPI(
    title="Zamanbank API",
    version="1.0.0",
    description="Zamanbank API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
router.prefix = "/api"

@router.get("/health", tags=["system"])
async def health():
    return {"health": "ok"}

app.include_router(router)
app.include_router(auth_router, prefix="/api/auth")
app.include_router(account_router, prefix="/api")
app.include_router(transaction_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(faceid_router, prefix="/api/faceid", tags=["Face Verification"])
app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)