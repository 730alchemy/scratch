import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_books(client):
    """Reset book storage before each test."""
    # Delete all books between tests so each test starts fresh.
    response = client.get("/books")
    for book in response.json():
        client.delete(f"/books/{book['id']}")
    yield


class TestGetBooks:
    def test_get_books_returns_empty_list_initially(self, client):
        # Given: no books have been created
        # When: GET /books is requested
        response = client.get("/books")

        # Then: response is 200 with an empty list
        assert response.status_code == 200
        assert response.json() == []

    def test_get_books_returns_json(self, client):
        # Given: no books
        # When: GET /books is requested
        response = client.get("/books")

        # Then: content type is JSON
        assert "application/json" in response.headers["content-type"]


class TestCreateBook:
    def test_post_books_creates_book(self, client):
        # Given: valid book payload
        payload = {"title": "Clean Code", "author": "Robert Martin"}

        # When: POST /books is requested
        response = client.post("/books", json=payload)

        # Then: book is created and returned
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Clean Code"
        assert data["author"] == "Robert Martin"

    def test_post_books_returns_id(self, client):
        # Given: valid book payload
        payload = {"title": "Clean Code", "author": "Robert Martin"}

        # When: POST /books is requested
        response = client.post("/books", json=payload)

        # Then: response includes an id field
        data = response.json()
        assert "id" in data
        assert data["id"] is not None

    def test_post_books_returns_json(self, client):
        # Given: valid book payload
        payload = {"title": "Clean Code", "author": "Robert Martin"}

        # When: POST /books
        response = client.post("/books", json=payload)

        # Then: content type is JSON
        assert "application/json" in response.headers["content-type"]

    def test_post_books_appears_in_list(self, client):
        # Given: a book is created
        payload = {"title": "The Pragmatic Programmer", "author": "Hunt and Thomas"}
        client.post("/books", json=payload)

        # When: GET /books is requested
        response = client.get("/books")

        # Then: the new book appears in the list
        titles = [b["title"] for b in response.json()]
        assert "The Pragmatic Programmer" in titles


class TestGetBookById:
    def test_get_book_by_id_returns_book(self, client):
        # Given: a book is created
        payload = {"title": "Design Patterns", "author": "Gang of Four"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]

        # When: GET /books/{id} is requested
        response = client.get(f"/books/{book_id}")

        # Then: the book is returned
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book_id
        assert data["title"] == "Design Patterns"
        assert data["author"] == "Gang of Four"

    def test_get_book_by_id_returns_404_for_missing_book(self, client):
        # Given: a book id that does not exist
        missing_id = 99999

        # When: GET /books/{id} is requested
        response = client.get(f"/books/{missing_id}")

        # Then: 404 is returned
        assert response.status_code == 404

    def test_get_book_by_id_returns_json(self, client):
        # Given: a book is created
        payload = {"title": "Refactoring", "author": "Martin Fowler"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]

        # When: GET /books/{id}
        response = client.get(f"/books/{book_id}")

        # Then: content type is JSON
        assert "application/json" in response.headers["content-type"]


class TestUpdateBook:
    def test_put_book_updates_title_and_author(self, client):
        # Given: a book is created
        payload = {"title": "Old Title", "author": "Old Author"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]

        # When: PUT /books/{id} with new data
        update = {"title": "New Title", "author": "New Author"}
        response = client.put(f"/books/{book_id}", json=update)

        # Then: book is updated and returned
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"
        assert data["id"] == book_id

    def test_put_book_persists_update(self, client):
        # Given: a book is created and updated
        payload = {"title": "Old Title", "author": "Old Author"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]
        client.put(f"/books/{book_id}", json={"title": "New Title", "author": "New Author"})

        # When: GET /books/{id} is called
        response = client.get(f"/books/{book_id}")

        # Then: updated values are returned
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"

    def test_put_book_returns_404_for_missing_book(self, client):
        # Given: a book id that does not exist
        missing_id = 99999

        # When: PUT /books/{id} is requested
        response = client.put(f"/books/{missing_id}", json={"title": "T", "author": "A"})

        # Then: 404 is returned
        assert response.status_code == 404

    def test_put_book_returns_json(self, client):
        # Given: a book is created
        payload = {"title": "Original", "author": "Author"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]

        # When: PUT /books/{id}
        response = client.put(f"/books/{book_id}", json={"title": "Updated", "author": "Author"})

        # Then: content type is JSON
        assert "application/json" in response.headers["content-type"]


class TestDeleteBook:
    def test_delete_book_removes_book(self, client):
        # Given: a book is created
        payload = {"title": "To Be Deleted", "author": "Some Author"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]

        # When: DELETE /books/{id} is requested
        response = client.delete(f"/books/{book_id}")

        # Then: 200 or 204 is returned
        assert response.status_code in (200, 204)

    def test_delete_book_is_no_longer_retrievable(self, client):
        # Given: a book is created and deleted
        payload = {"title": "To Be Deleted", "author": "Some Author"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]
        client.delete(f"/books/{book_id}")

        # When: GET /books/{id} is requested
        response = client.get(f"/books/{book_id}")

        # Then: 404 is returned
        assert response.status_code == 404

    def test_delete_book_no_longer_in_list(self, client):
        # Given: a book is created and deleted
        payload = {"title": "Gone", "author": "Nobody"}
        created = client.post("/books", json=payload).json()
        book_id = created["id"]
        client.delete(f"/books/{book_id}")

        # When: GET /books is requested
        response = client.get("/books")

        # Then: deleted book is not in the list
        ids = [b["id"] for b in response.json()]
        assert book_id not in ids

    def test_delete_book_returns_404_for_missing_book(self, client):
        # Given: a book id that does not exist
        missing_id = 99999

        # When: DELETE /books/{id} is requested
        response = client.delete(f"/books/{missing_id}")

        # Then: 404 is returned
        assert response.status_code == 404
