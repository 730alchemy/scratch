"""
Tests for Library CRUD endpoints.

These tests assume the application is structured as:
  - src/main.py  — FastAPI app instance
  - Library Pydantic model with: id (int), name (str), books (list[Book])
  - In-memory stores: books_store, libraries_store — reset between tests
  - Routes: GET/POST /libraries, GET/PUT/DELETE /libraries/{id}
  - Library books reference Book objects by their ids
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Return a TestClient with fresh in-memory stores for each test."""
    from src.main import app, books_store, libraries_store  # noqa: PLC0415

    books_store.clear()
    libraries_store.clear()
    return TestClient(app)


@pytest.fixture()
def book(client):
    """Create and return a single book for use in library tests."""
    response = client.post("/books", json={"title": "Dune", "author": "Frank Herbert"})
    return response.json()


@pytest.fixture()
def another_book(client):
    """Create and return a second book for multi-book library tests."""
    response = client.post("/books", json={"title": "Foundation", "author": "Isaac Asimov"})
    return response.json()


# ---------------------------------------------------------------------------
# GET /libraries
# ---------------------------------------------------------------------------

class TestListLibraries:
    def test_returns_empty_list_initially(self, client):
        response = client.get("/libraries")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_all_created_libraries(self, client):
        client.post("/libraries", json={"name": "City Library", "book_ids": []})
        client.post("/libraries", json={"name": "Town Library", "book_ids": []})

        response = client.get("/libraries")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_response_is_json(self, client):
        response = client.get("/libraries")

        assert response.headers["content-type"].startswith("application/json")


# ---------------------------------------------------------------------------
# POST /libraries
# ---------------------------------------------------------------------------

class TestCreateLibrary:
    def test_creates_library_with_name_and_empty_book_list(self, client):
        response = client.post("/libraries", json={"name": "City Library", "book_ids": []})

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "City Library"
        assert body["books"] == []

    def test_created_library_has_an_id(self, client):
        response = client.post("/libraries", json={"name": "City Library", "book_ids": []})

        assert "id" in response.json()
        assert response.json()["id"] is not None

    def test_each_created_library_gets_unique_id(self, client):
        r1 = client.post("/libraries", json={"name": "City Library", "book_ids": []})
        r2 = client.post("/libraries", json={"name": "Town Library", "book_ids": []})

        assert r1.json()["id"] != r2.json()["id"]

    def test_creates_library_with_existing_books(self, client, book):
        response = client.post(
            "/libraries",
            json={"name": "City Library", "book_ids": [book["id"]]},
        )

        assert response.status_code == 201
        body = response.json()
        assert len(body["books"]) == 1
        assert body["books"][0]["id"] == book["id"]
        assert body["books"][0]["title"] == book["title"]

    def test_creates_library_with_multiple_books(self, client, book, another_book):
        response = client.post(
            "/libraries",
            json={"name": "City Library", "book_ids": [book["id"], another_book["id"]]},
        )

        assert response.status_code == 201
        assert len(response.json()["books"]) == 2

    def test_missing_name_returns_422(self, client):
        response = client.post("/libraries", json={"book_ids": []})

        assert response.status_code == 422

    def test_referencing_nonexistent_book_id_returns_404(self, client):
        response = client.post("/libraries", json={"name": "City Library", "book_ids": [9999]})

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /libraries/{id}
# ---------------------------------------------------------------------------

class TestGetLibrary:
    def test_returns_existing_library(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()
        library_id = created["id"]

        response = client.get(f"/libraries/{library_id}")

        assert response.status_code == 200
        assert response.json()["id"] == library_id
        assert response.json()["name"] == "City Library"

    def test_returns_library_with_its_books(self, client, book):
        created = client.post(
            "/libraries",
            json={"name": "City Library", "book_ids": [book["id"]]},
        ).json()

        response = client.get(f"/libraries/{created['id']}")

        assert response.status_code == 200
        assert len(response.json()["books"]) == 1
        assert response.json()["books"][0]["id"] == book["id"]

    def test_returns_404_for_missing_library(self, client):
        response = client.get("/libraries/9999")

        assert response.status_code == 404

    def test_404_response_is_json(self, client):
        response = client.get("/libraries/9999")

        assert response.headers["content-type"].startswith("application/json")
        assert "detail" in response.json()


# ---------------------------------------------------------------------------
# PUT /libraries/{id}
# ---------------------------------------------------------------------------

class TestUpdateLibrary:
    def test_updates_library_name(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()
        library_id = created["id"]

        response = client.put(
            f"/libraries/{library_id}",
            json={"name": "Grand Library", "book_ids": []},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Grand Library"
        assert response.json()["id"] == library_id

    def test_update_persists(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()
        library_id = created["id"]
        client.put(f"/libraries/{library_id}", json={"name": "Grand Library", "book_ids": []})

        fetched = client.get(f"/libraries/{library_id}").json()

        assert fetched["name"] == "Grand Library"

    def test_updates_library_book_list(self, client, book, another_book):
        created = client.post(
            "/libraries",
            json={"name": "City Library", "book_ids": [book["id"]]},
        ).json()
        library_id = created["id"]

        response = client.put(
            f"/libraries/{library_id}",
            json={"name": "City Library", "book_ids": [another_book["id"]]},
        )

        assert response.status_code == 200
        updated_book_ids = [b["id"] for b in response.json()["books"]]
        assert another_book["id"] in updated_book_ids
        assert book["id"] not in updated_book_ids

    def test_update_can_clear_book_list(self, client, book):
        created = client.post(
            "/libraries",
            json={"name": "City Library", "book_ids": [book["id"]]},
        ).json()
        library_id = created["id"]

        response = client.put(
            f"/libraries/{library_id}",
            json={"name": "City Library", "book_ids": []},
        )

        assert response.status_code == 200
        assert response.json()["books"] == []

    def test_update_returns_404_for_missing_library(self, client):
        response = client.put("/libraries/9999", json={"name": "Ghost", "book_ids": []})

        assert response.status_code == 404

    def test_update_missing_name_returns_422(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()

        response = client.put(f"/libraries/{created['id']}", json={"book_ids": []})

        assert response.status_code == 422

    def test_update_referencing_nonexistent_book_id_returns_404(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()

        response = client.put(
            f"/libraries/{created['id']}",
            json={"name": "City Library", "book_ids": [9999]},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /libraries/{id}
# ---------------------------------------------------------------------------

class TestDeleteLibrary:
    def test_deletes_existing_library(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()
        library_id = created["id"]

        response = client.delete(f"/libraries/{library_id}")

        assert response.status_code in (200, 204)

    def test_deleted_library_no_longer_retrievable(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()
        library_id = created["id"]
        client.delete(f"/libraries/{library_id}")

        response = client.get(f"/libraries/{library_id}")

        assert response.status_code == 404

    def test_deleted_library_absent_from_list(self, client):
        created = client.post(
            "/libraries", json={"name": "City Library", "book_ids": []}
        ).json()
        library_id = created["id"]
        client.delete(f"/libraries/{library_id}")

        libraries = client.get("/libraries").json()

        assert all(lib["id"] != library_id for lib in libraries)

    def test_delete_returns_404_for_missing_library(self, client):
        response = client.delete("/libraries/9999")

        assert response.status_code == 404

    def test_deleting_library_does_not_delete_its_books(self, client, book):
        created = client.post(
            "/libraries",
            json={"name": "City Library", "book_ids": [book["id"]]},
        ).json()
        client.delete(f"/libraries/{created['id']}")

        book_response = client.get(f"/books/{book['id']}")

        assert book_response.status_code == 200
