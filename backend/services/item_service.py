from sqlalchemy.orm import Session
from models import Item, ItemCreate, ItemDB
from typing import List, Optional


class ItemService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get all items with pagination"""
        items = self.db.query(ItemDB).offset(skip).limit(limit).all()
        return [Item.model_validate(item) for item in items]
    
    def get_item(self, item_id: int) -> Optional[Item]:
        """Get item by ID"""
        item = self.db.query(ItemDB).filter(ItemDB.id == item_id).first()
        return Item.model_validate(item) if item else None
    
    def create_item(self, item: ItemCreate) -> Item:
        """Create new item"""
        db_item = ItemDB(**item.model_dump())
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return Item.model_validate(db_item)
    
    def update_item(self, item_id: int, item: ItemCreate) -> Optional[Item]:
        """Update existing item"""
        db_item = self.db.query(ItemDB).filter(ItemDB.id == item_id).first()
        if not db_item:
            return None
        
        for key, value in item.model_dump().items():
            setattr(db_item, key, value)
        
        self.db.commit()
        self.db.refresh(db_item)
        return Item.model_validate(db_item)
    
    def delete_item(self, item_id: int) -> bool:
        """Delete item by ID"""
        db_item = self.db.query(ItemDB).filter(ItemDB.id == item_id).first()
        if not db_item:
            return False
        
        self.db.delete(db_item)
        self.db.commit()
        return True
