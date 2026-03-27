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


class LibraryIn(BaseModel):
    name: str
    book_ids: list[int] = []


class Library(BaseModel):
    id: int
    name: str
    books: list[Book]


_books: dict[int, Book] = {}
_next_book_id: int = 1

_libraries: dict[int, tuple[str, list[int]]] = {}
_next_library_id: int = 1


@app.get("/books", response_model=list[Book])
def list_books():
    return list(_books.values())


@app.post("/books", response_model=Book, status_code=201)
def create_book(payload: BookIn):
    global _next_book_id
    book = Book(id=_next_book_id, **payload.model_dump())
    _books[_next_book_id] = book
    _next_book_id += 1
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
    updated = Book(id=book_id, **payload.model_dump())
    _books[book_id] = updated
    return updated


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail="Book not found")
    del _books[book_id]


def _resolve_library(library_id: int, name: str, book_ids: list[int]) -> Library:
    books = [_books[bid] for bid in book_ids if bid in _books]
    return Library(id=library_id, name=name, books=books)


@app.get("/libraries", response_model=list[Library])
def list_libraries():
    return [_resolve_library(lid, name, book_ids) for lid, (name, book_ids) in _libraries.items()]


@app.post("/libraries", response_model=Library, status_code=201)
def create_library(payload: LibraryIn):
    global _next_library_id
    for bid in payload.book_ids:
        if bid not in _books:
            raise HTTPException(status_code=404, detail=f"Book {bid} not found")
    _libraries[_next_library_id] = (payload.name, list(payload.book_ids))
    library = _resolve_library(_next_library_id, payload.name, payload.book_ids)
    _next_library_id += 1
    return library


@app.get("/libraries/{library_id}", response_model=Library)
def get_library(library_id: int):
    entry = _libraries.get(library_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Library not found")
    name, book_ids = entry
    return _resolve_library(library_id, name, book_ids)


@app.put("/libraries/{library_id}", response_model=Library)
def update_library(library_id: int, payload: LibraryIn):
    if library_id not in _libraries:
        raise HTTPException(status_code=404, detail="Library not found")
    for bid in payload.book_ids:
        if bid not in _books:
            raise HTTPException(status_code=404, detail=f"Book {bid} not found")
    _libraries[library_id] = (payload.name, list(payload.book_ids))
    return _resolve_library(library_id, payload.name, payload.book_ids)


@app.delete("/libraries/{library_id}", status_code=204)
def delete_library(library_id: int):
    if library_id not in _libraries:
        raise HTTPException(status_code=404, detail="Library not found")
    del _libraries[library_id]
