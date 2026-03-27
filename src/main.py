from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class BookIn(BaseModel):
    title: str
    author: str


class Book(BaseModel):
    id: int
    title: str
    author: str


_books: dict[int, Book] = {}
_next_id: int = 1


@app.get("/books", response_model=list[Book])
def list_books():
    return list(_books.values())


@app.post("/books", response_model=Book, status_code=201)
def create_book(payload: BookIn):
    global _next_id
    book = Book(id=_next_id, title=payload.title, author=payload.author)
    _books[_next_id] = book
    _next_id += 1
    return book


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    book = _books.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, payload: BookIn):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail="Book not found")
    updated = Book(id=book_id, title=payload.title, author=payload.author)
    _books[book_id] = updated
    return updated


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail="Book not found")
    del _books[book_id]
