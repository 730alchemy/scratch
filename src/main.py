from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory stores: id -> record dict
books_store: dict[int, dict] = {}
libraries_store: dict[int, dict] = {}

_next_book_id_counter = 1
_next_library_id_counter = 1


class BookIn(BaseModel):
    title: str
    author: str


class Book(BaseModel):
    id: int
    title: str
    author: str


class LibraryIn(BaseModel):
    name: str
    book_ids: list[int]


class Library(BaseModel):
    id: int
    name: str
    books: list[Book]


def _next_book_id() -> int:
    global _next_book_id_counter
    book_id = _next_book_id_counter
    _next_book_id_counter += 1
    return book_id


def _next_library_id() -> int:
    global _next_library_id_counter
    library_id = _next_library_id_counter
    _next_library_id_counter += 1
    return library_id


def _resolve_books(book_ids: list[int]) -> list[dict]:
    books = []
    for book_id in book_ids:
        book = books_store.get(book_id)
        if book is None:
            raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
        books.append(book)
    return books


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


@app.get("/libraries", response_model=list[Library])
def list_libraries():
    return list(libraries_store.values())


@app.post("/libraries", response_model=Library, status_code=201)
def create_library(payload: LibraryIn):
    books = _resolve_books(payload.book_ids)
    library_id = _next_library_id()
    library = {"id": library_id, "name": payload.name, "books": books}
    libraries_store[library_id] = library
    return library


@app.get("/libraries/{library_id}", response_model=Library)
def get_library(library_id: int):
    library = libraries_store.get(library_id)
    if library is None:
        raise HTTPException(status_code=404, detail="Library not found")
    return library


@app.put("/libraries/{library_id}", response_model=Library)
def update_library(library_id: int, payload: LibraryIn):
    if library_id not in libraries_store:
        raise HTTPException(status_code=404, detail="Library not found")
    books = _resolve_books(payload.book_ids)
    library = {"id": library_id, "name": payload.name, "books": books}
    libraries_store[library_id] = library
    return library


@app.delete("/libraries/{library_id}", status_code=204)
def delete_library(library_id: int):
    if library_id not in libraries_store:
        raise HTTPException(status_code=404, detail="Library not found")
    del libraries_store[library_id]
