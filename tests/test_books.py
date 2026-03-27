import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_books(client):
    # Delete all books before each test to ensure isolation
    response = client.get("/books")
    for book in response.json():
        client.delete(f"/books/{book['id']}")
    yield


class TestGetBooks:
    def test_get_books_returns_empty_list_initially(self, client):
        # Given no books exist
        # When GET /books is called
        response = client.get("/books")

        # Then it returns 200 with an empty list
        assert response.status_code == 200
        assert response.json() == []

    def test_get_books_returns_json(self, client):
        # Given no books exist
        # When GET /books is called
        response = client.get("/books")

        # Then content-type is application/json
        assert "application/json" in response.headers["content-type"]


class TestCreateBook:
    def test_post_books_creates_a_book(self, client):
        # Given a valid book payload
        payload = {"title": "Clean Code", "author": "Robert C. Martin"}

        # When POST /books is called
        response = client.post("/books", json=payload)

        # Then it returns 201 (or 200) with the created book
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["title"] == "Clean Code"
        assert data["author"] == "Robert C. Martin"

    def test_post_books_returns_id(self, client):
        # Given a valid book payload
        payload = {"title": "The Pragmatic Programmer", "author": "David Thomas"}

        # When POST /books is called
        response = client.post("/books", json=payload)

        # Then the response includes an id field
        data = response.json()
        assert "id" in data
        assert data["id"] is not None

    def test_post_books_assigns_unique_ids(self, client):
        # Given two book payloads
        payload1 = {"title": "Book One", "author": "Author A"}
        payload2 = {"title": "Book Two", "author": "Author B"}

        # When both are created
        id1 = client.post("/books", json=payload1).json()["id"]
        id2 = client.post("/books", json=payload2).json()["id"]

        # Then their ids are different
        assert id1 != id2

    def test_post_books_appears_in_list(self, client):
        # Given a book is created
        payload = {"title": "Refactoring", "author": "Martin Fowler"}
        created = client.post("/books", json=payload).json()

        # When GET /books is called
        response = client.get("/books")

        # Then the created book appears in the list
        assert any(b["id"] == created["id"] for b in response.json())


class TestGetBookById:
    def test_get_book_by_id_returns_the_book(self, client):
        # Given a book exists
        payload = {"title": "Domain-Driven Design", "author": "Eric Evans"}
        created = client.post("/books", json=payload).json()

        # When GET /books/{id} is called
        response = client.get(f"/books/{created['id']}")

        # Then it returns 200 with the book
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["title"] == "Domain-Driven Design"
        assert data["author"] == "Eric Evans"

    def test_get_book_by_id_returns_404_for_missing_book(self, client):
        # Given no book exists with id 99999
        # When GET /books/99999 is called
        response = client.get("/books/99999")

        # Then it returns 404
        assert response.status_code == 404

    def test_get_book_by_id_404_response_is_json(self, client):
        # Given no book exists with id 99999
        # When GET /books/99999 is called
        response = client.get("/books/99999")

        # Then the response body is valid JSON
        assert "application/json" in response.headers["content-type"]
        assert response.json() is not None


class TestUpdateBook:
    def test_put_book_updates_title_and_author(self, client):
        # Given a book exists
        created = client.post("/books", json={"title": "Old Title", "author": "Old Author"}).json()

        # When PUT /books/{id} is called with new data
        update = {"title": "New Title", "author": "New Author"}
        response = client.put(f"/books/{created['id']}", json=update)

        # Then it returns 200 with the updated book
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"

    def test_put_book_preserves_id(self, client):
        # Given a book exists
        created = client.post("/books", json={"title": "Old Title", "author": "Old Author"}).json()

        # When PUT /books/{id} is called
        response = client.put(f"/books/{created['id']}", json={"title": "New Title", "author": "New Author"})

        # Then the id is unchanged
        assert response.json()["id"] == created["id"]

    def test_put_book_is_reflected_in_get(self, client):
        # Given a book exists and is updated
        created = client.post("/books", json={"title": "Old Title", "author": "Old Author"}).json()
        client.put(f"/books/{created['id']}", json={"title": "Updated Title", "author": "Updated Author"})

        # When GET /books/{id} is called
        response = client.get(f"/books/{created['id']}")

        # Then the updated data is returned
        assert response.json()["title"] == "Updated Title"

    def test_put_book_returns_404_for_missing_book(self, client):
        # Given no book exists with id 99999
        # When PUT /books/99999 is called
        response = client.put("/books/99999", json={"title": "X", "author": "Y"})

        # Then it returns 404
        assert response.status_code == 404


class TestDeleteBook:
    def test_delete_book_removes_the_book(self, client):
        # Given a book exists
        created = client.post("/books", json={"title": "To Delete", "author": "Someone"}).json()

        # When DELETE /books/{id} is called
        response = client.delete(f"/books/{created['id']}")

        # Then it returns 200 or 204
        assert response.status_code in (200, 204)

    def test_delete_book_is_no_longer_accessible(self, client):
        # Given a book is created then deleted
        created = client.post("/books", json={"title": "To Delete", "author": "Someone"}).json()
        client.delete(f"/books/{created['id']}")

        # When GET /books/{id} is called
        response = client.get(f"/books/{created['id']}")

        # Then it returns 404
        assert response.status_code == 404

    def test_delete_book_is_not_in_list(self, client):
        # Given a book is created then deleted
        created = client.post("/books", json={"title": "To Delete", "author": "Someone"}).json()
        client.delete(f"/books/{created['id']}")

        # When GET /books is called
        books = client.get("/books").json()

        # Then the deleted book is not in the list
        assert all(b["id"] != created["id"] for b in books)

    def test_delete_book_returns_404_for_missing_book(self, client):
        # Given no book exists with id 99999
        # When DELETE /books/99999 is called
        response = client.delete("/books/99999")

        # Then it returns 404
        assert response.status_code == 404
