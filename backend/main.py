from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import Item, ItemCreate
from services import ItemService

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HackNU API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to HackNU FastAPI!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Items endpoints
@app.get("/api/items", response_model=list[Item])
async def get_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all items with pagination"""
    item_service = ItemService(db)
    return item_service.get_items(skip=skip, limit=limit)

@app.get("/api/items/{item_id}", response_model=Item)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get item by ID"""
    item_service = ItemService(db)
    item = item_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/api/items", response_model=Item)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create new item"""
    item_service = ItemService(db)
    return item_service.create_item(item)

@app.put("/api/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    """Update existing item"""
    item_service = ItemService(db)
    updated_item = item_service.update_item(item_id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Delete item by ID"""
    item_service = ItemService(db)
    success = item_service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

