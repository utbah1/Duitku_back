"""Shared test fixtures.

Tests use an in-memory fake Firestore and a fake token verifier so that no
real Firebase credentials are required.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.main import app


class FakeRef:
    _id_counter = 0

    def __init__(self, store, collection, doc_id=None):
        self._store = store
        self._collection = collection
        self._doc_id = doc_id

    def document(self, doc_id=None):
        if doc_id is None:
            # Generate a new unique ID (mimic Firestore auto-ID)
            FakeRef._id_counter += 1
            doc_id = f"gen-{FakeRef._id_counter}"
        return FakeRef(self._store, self._collection, doc_id)

    @property
    def id(self):
        return self._doc_id

    def set(self, data):
        key = self._doc_id
        self._store[self._collection][key] = dict(data)

    def get(self):
        data = self._store[self._collection].get(self._doc_id)
        return FakeSnapshot(self._doc_id, data)

    def update(self, data):
        key = self._doc_id
        if key in self._store[self._collection]:
            self._store[self._collection][key].update(data)

    def delete(self):
        self._store[self._collection].pop(self._doc_id, None)

    def where(self, field, op, value):
        return FakeQuery(self._store, self._collection, [(field, op, value)])

    def order_by(self, field, direction="ASCENDING"):
        return FakeQuery(self._store, self._collection, [], order_by=(field, direction))


class FakeSnapshot:
    def __init__(self, id, data):
        self.id = id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class FakeQuery:
    def __init__(self, store, collection, filters, order_by=None):
        self._store = store
        self._collection = collection
        self._filters = list(filters)  # list of (field, op, value) tuples
        self._order = order_by
        self._limit_n = None

    def where(self, field, op, value):
        new_filters = self._filters + [(field, op, value)]
        return FakeQuery(self._store, self._collection, new_filters, self._order)

    def order_by(self, field, direction="ASCENDING"):
        return FakeQuery(self._store, self._collection, self._filters, (field, direction))

    def limit(self, n):
        q = FakeQuery(self._store, self._collection, self._filters, self._order)
        q._limit_n = n
        return q

    def stream(self):
        items = []
        for key, data in self._store[self._collection].items():
            match = True
            for field, op, value in self._filters:
                if op == "==":
                    if data.get(field) != value:
                        match = False
                        break
                elif op == ">=":
                    v = data.get(field)
                    if v is None or v < value:
                        match = False
                        break
                elif op == "<=":
                    v = data.get(field)
                    if v is None or v > value:
                        match = False
                        break
            if match:
                items.append(FakeSnapshot(key, data))
        if self._order:
            field, direction = self._order
            reverse = direction == "DESCENDING"
            items.sort(
                key=lambda s: (s.to_dict().get(field) is None, s.to_dict().get(field)),
                reverse=reverse,
            )
        if self._limit_n is not None:
            items = items[: self._limit_n]
        return iter(items)


class FakeFirestore:
    def __init__(self):
        self._store = {"users": {}, "transactions": {}}

    def collection(self, name):
        if name not in self._store:
            self._store[name] = {}
        return FakeRef(self._store, name)


@pytest.fixture
def fake_db():
    FakeRef._id_counter = 0
    return FakeFirestore()


@pytest.fixture
def client(fake_db):
    """TestClient with Firebase token verification and DB overridden."""

    def override_get_db():
        return fake_db

    # Override the imported `get_db` name in every module that uses it.
    import app.repositories.transaction_repository as tx_repo
    import app.repositories.user_repository as user_repo
    import app.routers.auth as auth_router
    import app.routers.dashboard as dash_router
    import app.routers.reports as report_router
    import app.routers.transactions as tx_router
    import app.routers.users as user_router

    for mod in (
        auth_router,
        dash_router,
        report_router,
        tx_router,
        user_router,
        tx_repo,
        user_repo,
    ):
        mod.get_db = override_get_db

    # Fake token verifier: accept any token and return a fixed uid.
    class FakeVerifier:
        def verify_token(self, token):
            return {"uid": "test-user-123", "email": "test@example.com", "name": "Test User"}

    security.token_verifier = FakeVerifier()

    with TestClient(app) as c:
        yield c

    security.token_verifier = security.FirebaseTokenVerifier()


@pytest.fixture
def auth_headers():
    from app.core.security import create_access_token

    token = create_access_token(
        subject="test-user-123",
        extra={"email": "test@example.com", "name": "Test User"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_transaction():
    return {
        "title": "Makan Siang",
        "amount": 25000,
        "category": "Makanan",
        "type": "expense",
        "note": "Warung",
        "date": "2026-08-08",
    }
