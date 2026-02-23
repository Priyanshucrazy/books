from fastapi import FastAPI, Body, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

app = FastAPI()

# PostgreSQL Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL" )
# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define Book model
class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    author = Column(String, index=True)
    category = Column(String, index=True)


# Create tables on startup
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Seed initial books on startup
@app.on_event("startup")
async def startup_event():
    """Seed initial books on application startup"""
    db = SessionLocal()
    
    initial_books = [
        {'title': 'Title One', 'author': 'Author One', 'category': 'science'},
        {'title': 'Title Two', 'author': 'Author Two', 'category': 'science'},
        {'title': 'Title Three', 'author': 'Author Three', 'category': 'history'},
        {'title': 'Title Four', 'author': 'Author Four', 'category': 'math'},
        {'title': 'Title Five', 'author': 'Author Five', 'category': 'math'},
        {'title': 'Title Six', 'author': 'Author Two', 'category': 'math'}
    ]
    
    for book_data in initial_books:
        # Check if book already exists
        existing_book = db.query(Book).filter(Book.title == book_data['title']).first()
        
        if not existing_book:
            book = Book(**book_data)
            db.add(book)
    
    db.commit()
    db.close()
    print("✓ Initial books seeded successfully!")


# GET all books
@app.get("/books")
async def read_all_books(db: Session = Depends(get_db)):
    """Get all books"""
    if db is None:
        db = SessionLocal()
    books = db.query(Book).all()
    return books


# GET book by title
@app.get("/books/{book_title}")
async def read_book(book_title: str, db: Session = Depends(get_db)):
    """Get a specific book by title"""
    if db is None:
        db = SessionLocal()
    book = db.query(Book).filter(Book.title.ilike(book_title)).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book


# GET books by category (query parameter)
@app.get("/books/")
async def read_category_by_query(category: str, db: Session = Depends(get_db)):
    """Get books by category"""
    if db is None:
        db = SessionLocal()
    books = db.query(Book).filter(Book.category.ilike(category)).all()
    return books


# GET books by author
@app.get("/books/byauthor/")
async def read_books_by_author(author: str, db: Session = Depends(get_db):
    """Get books by author"""
    if db is None:
        db = SessionLocal()
    books = db.query(Book).filter(Book.author.ilike(author)).all()
    return books


# GET books by author and category
@app.get("/books/{book_author}/")
async def read_author_category_by_query(book_author: str, category: str, db: Session = Depends(get_db)):
    """Get books by author and category"""
    if db is None:
        db = SessionLocal()
    books = db.query(Book).filter(
        Book.author.ilike(book_author),
        Book.category.ilike(category)
    ).all()
    return books


# POST create a new book
@app.post("/books/create_book")
async def create_book(new_book=Body(), db: Session = Depends(get_db)):
    """Create a new book"""
    if db is None:
        db = SessionLocal()
    
    # Check if book already exists
    existing_book = db.query(Book).filter(Book.title.ilike(new_book.get('title'))).first()
    if existing_book:
        raise HTTPException(status_code=400, detail="Book already exists")
    
    db_book = Book(
        title=new_book.get('title'),
        author=new_book.get('author'),
        category=new_book.get('category')
    )
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    return {"message": "Book created successfully", "book": {
        "id": db_book.id,
        "title": db_book.title,
        "author": db_book.author,
        "category": db_book.category
    }}


# PUT update a book
@app.put("/books/update_book")
async def update_book(updated_book=Body(), db: Session = Depends(get_db)):
    """Update an existing book"""
    if db is None:
        db = SessionLocal()
    
    db_book = db.query(Book).filter(Book.title.ilike(updated_book.get('title'))).first()
    
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db_book.author = updated_book.get('author', db_book.author)
    db_book.category = updated_book.get('category', db_book.category)
    
    db.commit()
    db.refresh(db_book)
    
    return {"message": "Book updated successfully", "book": {
        "id": db_book.id,
        "title": db_book.title,
        "author": db_book.author,
        "category": db_book.category
    }}


# DELETE a book
@app.delete("/books/delete_book/{book_title}")
async def delete_book(book_title: str, db: Session = Depends(get_db):
    """Delete a book by title"""
    if db is None:
        db = SessionLocal()
    
    db_book = db.query(Book).filter(Book.title.ilike(book_title)).first()
    
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(db_book)
    db.commit()
    
    return {"message": f"Book '{book_title}' deleted successfully"}
