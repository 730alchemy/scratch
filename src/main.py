from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

_books: dict[int, "Book"] = {}
_libraries: dict[int, "Library"] = {}
_next_book_id: int = 1
_next_library_id: int = 1


class BookIn(BaseModel):
    title: str
    author: str


class Book(BookIn):
    id: int


class LibraryIn(BaseModel):
    name: str
    book_ids: list[int] = []


class Library(BaseModel):
    id: int
    name: str
    books: list[Book] = []


# Book endpoints


@app.get("/books", response_model=list[Book])
def list_books():
    return list(_books.values())


@app.post("/books", response_model=Book, status_code=201)
def create_book(payload: BookIn):
    global _next_book_id
    book = Book(id=_next_book_id, title=payload.title, author=payload.author)
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
    _books[book_id] = Book(id=book_id, title=payload.title, author=payload.author)
    return _books[book_id]


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail="Book not found")
    del _books[book_id]


# Library endpoints


@app.get("/libraries", response_model=list[Library])
def list_libraries():
    return list(_libraries.values())


@app.post("/libraries", response_model=Library, status_code=201)
def create_library(payload: LibraryIn):
    global _next_library_id
    books = _resolve_books(payload.book_ids)
    library = Library(id=_next_library_id, name=payload.name, books=books)
    _libraries[_next_library_id] = library
    _next_library_id += 1
    return library


@app.get("/libraries/{library_id}", response_model=Library)
def get_library(library_id: int):
    library = _libraries.get(library_id)
    if library is None:
        raise HTTPException(status_code=404, detail="Library not found")
    return library


@app.put("/libraries/{library_id}", response_model=Library)
def update_library(library_id: int, payload: LibraryIn):
    if library_id not in _libraries:
        raise HTTPException(status_code=404, detail="Library not found")
    books = _resolve_books(payload.book_ids)
    _libraries[library_id] = Library(id=library_id, name=payload.name, books=books)
    return _libraries[library_id]


@app.delete("/libraries/{library_id}", status_code=204)
def delete_library(library_id: int):
    if library_id not in _libraries:
        raise HTTPException(status_code=404, detail="Library not found")
    del _libraries[library_id]


def _resolve_books(book_ids: list[int]) -> list[Book]:
    books = []
    for book_id in book_ids:
        book = _books.get(book_id)
        if book is None:
            raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
        books.append(book)
    return books
