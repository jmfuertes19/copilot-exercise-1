import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    original_activities = copy.deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(original_activities))

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert payload["Soccer Team"]["participants"] == []


def test_signup_for_activity_success(client):
    email = "newstudent@mergington.edu"
    response = client.post(f"/activities/Soccer Team/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Soccer Team"}
    assert email in app_module.activities["Soccer Team"]["participants"]


def test_signup_for_activity_returns_404_when_activity_missing(client):
    response = client.post("/activities/Unknown Activity/signup?email=student@example.com")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_for_activity_returns_400_when_student_already_signed_up(client):
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_unregister_from_activity_success(client):
    email = "michael@mergington.edu"
    response = client.delete(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_from_activity_returns_404_when_activity_missing(client):
    response = client.delete("/activities/Unknown Activity/signup?email=student@example.com")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_from_activity_returns_404_when_student_not_signed_up(client):
    response = client.delete("/activities/Chess Club/signup?email=not-a-member@example.com")

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
