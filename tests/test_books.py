"""
Tests for Book CRUD endpoints.

These tests assume the application is structured as:
  - src/main.py  — FastAPI app instance
  - Book Pydantic model with: id (int), title (str), author (str)
  - In-memory store, reset between requests via app state or module-level dict
  - Routes: GET/POST /books, GET/PUT/DELETE /books/{id}
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Return a TestClient with a fresh in-memory store for each test."""
    from src.main import app, books_store  # noqa: PLC0415

    books_store.clear()
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /books
# ---------------------------------------------------------------------------

class TestListBooks:
    def test_returns_empty_list_initially(self, client):
        response = client.get("/books")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_all_created_books(self, client):
        client.post("/books", json={"title": "Dune", "author": "Frank Herbert"})
        client.post("/books", json={"title": "Foundation", "author": "Isaac Asimov"})

        response = client.get("/books")

        assert response.status_code == 200
        assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# POST /books
# ---------------------------------------------------------------------------

class TestCreateBook:
    def test_creates_book_and_returns_it(self, client):
        payload = {"title": "Dune", "author": "Frank Herbert"}

        response = client.post("/books", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Dune"
        assert body["author"] == "Frank Herbert"

    def test_created_book_has_an_id(self, client):
        response = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"})

        assert "id" in response.json()
        assert response.json()["id"] is not None

    def test_each_created_book_gets_unique_id(self, client):
        r1 = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"})
        r2 = client.post("/books", json={"title": "Foundation", "author": "Isaac Asimov"})

        assert r1.json()["id"] != r2.json()["id"]

    def test_missing_title_returns_422(self, client):
        response = client.post("/books", json={"author": "Frank Herbert"})

        assert response.status_code == 422

    def test_missing_author_returns_422(self, client):
        response = client.post("/books", json={"title": "Dune"})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /books/{id}
# ---------------------------------------------------------------------------

class TestGetBook:
    def test_returns_existing_book(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
        book_id = created["id"]

        response = client.get(f"/books/{book_id}")

        assert response.status_code == 200
        assert response.json()["id"] == book_id
        assert response.json()["title"] == "Dune"
        assert response.json()["author"] == "Frank Herbert"

    def test_returns_404_for_missing_book(self, client):
        response = client.get("/books/9999")

        assert response.status_code == 404

    def test_404_response_is_json(self, client):
        response = client.get("/books/9999")

        assert response.headers["content-type"].startswith("application/json")
        assert "detail" in response.json()


# ---------------------------------------------------------------------------
# PUT /books/{id}
# ---------------------------------------------------------------------------

class TestUpdateBook:
    def test_updates_existing_book(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
        book_id = created["id"]

        response = client.put(
            f"/books/{book_id}",
            json={"title": "Dune Messiah", "author": "Frank Herbert"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Dune Messiah"
        assert response.json()["author"] == "Frank Herbert"
        assert response.json()["id"] == book_id

    def test_update_persists(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
        book_id = created["id"]
        client.put(f"/books/{book_id}", json={"title": "Dune Messiah", "author": "Frank Herbert"})

        fetched = client.get(f"/books/{book_id}").json()

        assert fetched["title"] == "Dune Messiah"

    def test_update_returns_404_for_missing_book(self, client):
        response = client.put("/books/9999", json={"title": "Ghost", "author": "Nobody"})

        assert response.status_code == 404

    def test_update_missing_title_returns_422(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()

        response = client.put(f"/books/{created['id']}", json={"author": "Frank Herbert"})

        assert response.status_code == 422

    def test_update_missing_author_returns_422(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()

        response = client.put(f"/books/{created['id']}", json={"title": "Dune Messiah"})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /books/{id}
# ---------------------------------------------------------------------------

class TestDeleteBook:
    def test_deletes_existing_book(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
        book_id = created["id"]

        response = client.delete(f"/books/{book_id}")

        assert response.status_code in (200, 204)

    def test_deleted_book_no_longer_retrievable(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
        book_id = created["id"]
        client.delete(f"/books/{book_id}")

        response = client.get(f"/books/{book_id}")

        assert response.status_code == 404

    def test_deleted_book_absent_from_list(self, client):
        created = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"}).json()
        book_id = created["id"]
        client.delete(f"/books/{book_id}")

        books = client.get("/books").json()

        assert all(b["id"] != book_id for b in books)

    def test_delete_returns_404_for_missing_book(self, client):
        response = client.delete("/books/9999")

        assert response.status_code == 404
