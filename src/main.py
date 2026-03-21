from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory store: id -> Book dict
books_store: dict[int, dict] = {}
_next_id = 1


class BookIn(BaseModel):
    title: str
    author: str


class Book(BaseModel):
    id: int
    title: str
    author: str


def _next_book_id() -> int:
    global _next_id
    book_id = _next_id
    _next_id += 1
    return book_id


@app.get("/books", response_model=list[Book])
def list_books():
    return list(books_store.values())


@app.post("/books", response_model=Book, status_code=201)
def create_book(payload: BookIn):
    book_id = _next_book_id()
    book = {"id": book_id, "title": payload.title, "author": payload.author}
    books_store[book_id] = book
    return book


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    book = books_store.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, payload: BookIn):
    if book_id not in books_store:
        raise HTTPException(status_code=404, detail="Book not found")
    book = {"id": book_id, "title": payload.title, "author": payload.author}
    books_store[book_id] = book
    return book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    if book_id not in books_store:
        raise HTTPException(status_code=404, detail="Book not found")
    del books_store[book_id]
