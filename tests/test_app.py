import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities.clear()
        app_module.activities.update(original_activities)


def test_root_redirects_to_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity_names = set(app_module.activities.keys())

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert set(data.keys()) == expected_activity_names
    assert data["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"


def test_signup_for_activity_success():
    # Arrange
    activity_name = "Art Club"
    email = "newstudent@mergington.edu"
    original_participants = list(app_module.activities[activity_name]["participants"])

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert app_module.activities[activity_name]["participants"] == original_participants + [email]


def test_signup_for_activity_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_for_missing_activity_returns_404():
    # Arrange
    missing_activity = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{missing_activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_from_activity_success():
    # Arrange
    activity_name = "Basketball Team"
    email = app_module.activities[activity_name]["participants"][0]
    original_participants = list(app_module.activities[activity_name]["participants"])

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert app_module.activities[activity_name]["participants"] == [participant for participant in original_participants if participant != email]


def test_unregister_non_signed_up_student_returns_400():
    # Arrange
    activity_name = "Gym Class"
    email = "notregistered@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_missing_activity_returns_404():
    # Arrange
    missing_activity = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{missing_activity}/unregister", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
