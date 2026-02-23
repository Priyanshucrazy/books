import os
from typing import Generator, Optional

from fastapi import FastAPI, Body, Depends, HTTPException
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

app = FastAPI()

# --- Database config ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Model ---
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)


# --- DB session dependency ---
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Startup: create table + seed data ---
@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        initial_books = [
            {"title": "Title One", "author": "Author One", "category": "science"},
            {"title": "Title Two", "author": "Author Two", "category": "science"},
            {"title": "Title Three", "author": "Author Three", "category": "history"},
            {"title": "Title Four", "author": "Author Four", "category": "math"},
            {"title": "Title Five", "author": "Author Five", "category": "math"},
            {"title": "Title Six", "author": "Author Two", "category": "math"},
        ]

        for book_data in initial_books:
            exists = db.query(Book).filter(Book.title == book_data["title"]).first()
            if not exists:
                db.add(Book(**book_data))

        db.commit()
    finally:
        db.close()


# --- Routes ---
@app.get("/books")
def list_books(
    db: Session = Depends(get_db),
    title: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[str] = None,
):
    """
    List books. Optionally filter by title, author, and/or category using query params.
    Examples:
      GET /books
      GET /books?category=math
      GET /books?author=Author%20Two&category=math
      GET /books?title=Title%20One
    """
    q = db.query(Book)
    if title:
        q = q.filter(Book.title.ilike(title))
    if author:
        q = q.filter(Book.author.ilike(author))
    if category:
        q = q.filter(Book.category.ilike(category))
    return q.all()


@app.get("/books/title/{book_title}")
def get_book_by_title(book_title: str, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.title.ilike(book_title)).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books", status_code=201)
def create_book(new_book=Body(...), db: Session = Depends(get_db)):
    title = new_book.get("title")
    author = new_book.get("author")
    category = new_book.get("category")

    if not title or not author or not category:
        raise HTTPException(status_code=400, detail="title, author, category are required")

    existing = db.query(Book).filter(Book.title.ilike(title)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Book already exists")

    db_book = Book(title=title, author=author, category=category)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.put("/books/title/{book_title}")
def update_book(book_title: str, updated_book=Body(...), db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.title.ilike(book_title)).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    if "author" in updated_book and updated_book["author"]:
        db_book.author = updated_book["author"]
    if "category" in updated_book and updated_book["category"]:
        db_book.category = updated_book["category"]

    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/books/title/{book_title}")
def delete_book(book_title: str, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.title.ilike(book_title)).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(db_book)
    db.commit()
    return {"message": f"Book '{book_title}' deleted successfully"}
