from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


ACTIVITY = "Soccer Club"
ACTIVITY_PATH = f"/activities/{quote(ACTIVITY, safe='')}"
EMAIL = "student@mergington.edu"


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_disables_caching(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert ACTIVITY in response.json()


def test_successful_signup_appears_in_activities(client):
    signup_response = client.post(
        f"{ACTIVITY_PATH}/signup",
        params={"email": EMAIL},
    )

    assert signup_response.status_code == 200
    assert signup_response.json()["message"] == f"Signed up {EMAIL} for {ACTIVITY}"

    activities_response = client.get("/activities")
    assert EMAIL in activities_response.json()[ACTIVITY]["participants"]


def test_signup_rejects_duplicate_registration(client):
    first_response = client.post(
        f"{ACTIVITY_PATH}/signup",
        params={"email": EMAIL},
    )
    duplicate_response = client.post(
        f"{ACTIVITY_PATH}/signup",
        params={"email": EMAIL},
    )

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert activities[ACTIVITY]["participants"].count(EMAIL) == 1


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": EMAIL},
    )

    assert response.status_code == 404


def test_unregister_removes_participant_from_activities(client):
    other_email = "another@mergington.edu"
    activities[ACTIVITY]["participants"][:] = [EMAIL, EMAIL, other_email]

    response = client.delete(
        f"{ACTIVITY_PATH}/participants",
        params={"email": EMAIL},
    )

    assert response.status_code == 200
    assert activities[ACTIVITY]["participants"] == [other_email]

    activities_response = client.get("/activities")
    assert activities_response.json()[ACTIVITY]["participants"] == [other_email]


def test_unregister_returns_not_found_for_missing_participant_or_activity(client):
    missing_participant = client.delete(
        f"{ACTIVITY_PATH}/participants",
        params={"email": EMAIL},
    )
    unknown_activity = client.delete(
        "/activities/Unknown%20Club/participants",
        params={"email": EMAIL},
    )

    assert missing_participant.status_code == 404
    assert unknown_activity.status_code == 404
