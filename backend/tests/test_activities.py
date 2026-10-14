import pytest


def activity_data(**changes):
    data = {
        "title": "Dinner",
        "date": "2026-11-11",
        "time": "20:00",
        "location": "Fisherman's Wharf",
        "notes": "Book a table",
    }
    return {**data, **changes}


def test_get_activities_empty(client, trip):
    response = client.get(f"/api/trips/{trip['id']}/activities")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_activity(client, trip):
    response = client.post(f"/api/trips/{trip['id']}/activities", json=activity_data())
    assert response.status_code == 201
    activity = response.get_json()
    assert activity["trip_id"] == trip["id"]
    assert activity["title"] == "Dinner"
    assert activity["time"] == "20:00"


def test_create_activity_with_only_required_fields(client, trip):
    data = {"title": "Free day", "date": "2026-11-12"}
    response = client.post(f"/api/trips/{trip['id']}/activities", json=data)
    assert response.status_code == 201
    assert response.get_json()["location"] == ""


def test_get_activities_sorted_by_date_and_time(client, trip):
    url = f"/api/trips/{trip['id']}/activities"
    client.post(url, json=activity_data(title="Late", date="2026-11-12", time="09:00"))
    client.post(url, json=activity_data(title="Evening", date="2026-11-11", time="20:00"))
    client.post(url, json=activity_data(title="Morning", date="2026-11-11", time="08:00"))

    titles = [a["title"] for a in client.get(url).get_json()]
    assert titles == ["Morning", "Evening", "Late"]


def test_get_activities_only_returns_own_trip(client, trip, activity):
    other = client.post("/api/trips", json={
        "name": "Other", "destination": "Elsewhere",
        "start_date": "2026-11-10", "end_date": "2026-11-14",
    }).get_json()
    assert client.get(f"/api/trips/{other['id']}/activities").get_json() == []


def test_update_activity(client, activity):
    data = activity_data(title="Sunset at Baga", date="2026-11-13", time="17:30")
    response = client.put(f"/api/activities/{activity['id']}", json=data)
    assert response.status_code == 200
    updated = response.get_json()
    assert updated["title"] == "Sunset at Baga"
    assert updated["date"] == "2026-11-13"
    assert updated["trip_id"] == activity["trip_id"]


def test_delete_activity(client, trip, activity):
    response = client.delete(f"/api/activities/{activity['id']}")
    assert response.status_code == 200
    assert client.get(f"/api/trips/{trip['id']}/activities").get_json() == []


def test_activities_for_missing_trip(client):
    assert client.get("/api/trips/999/activities").status_code == 404
    response = client.post("/api/trips/999/activities", json=activity_data())
    assert response.status_code == 404
    assert response.get_json() == {"error": "Trip not found"}


def test_activity_not_found(client):
    assert client.put("/api/activities/999", json=activity_data()).status_code == 404
    response = client.delete("/api/activities/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Activity not found"}


def test_invalid_activity_id(client):
    response = client.delete("/api/activities/abc")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid activity id"}


@pytest.mark.parametrize("changes, message", [
    ({"title": ""}, "Title is required"),
    ({"date": ""}, "Date is required"),
    ({"date": "tomorrow"}, "Date must be a valid date (YYYY-MM-DD)"),
    ({"date": "2026-11-09"}, "Activity date must be within the trip dates"),
    ({"date": "2026-11-15"}, "Activity date must be within the trip dates"),
    ({"time": "9:00"}, "Time must be in HH:MM format"),
    ({"time": "25:00"}, "Time must be in HH:MM format"),
    ({"time": "12:75"}, "Time must be in HH:MM format"),
    ({"time": "abc"}, "Time must be in HH:MM format"),
    ({"time": "10:2"}, "Time must be in HH:MM format"),
])
def test_create_activity_invalid_data(client, trip, changes, message):
    response = client.post(f"/api/trips/{trip['id']}/activities", json=activity_data(**changes))
    assert response.status_code == 400
    assert response.get_json() == {"error": message}


@pytest.mark.parametrize("valid_time", ["09:00", "12:30", "23:59", ""])
def test_create_activity_valid_time(client, trip, valid_time):
    response = client.post(f"/api/trips/{trip['id']}/activities", json=activity_data(time=valid_time))
    assert response.status_code == 201
    assert response.get_json()["time"] == valid_time


def test_activity_allowed_on_first_and_last_trip_day(client, trip):
    url = f"/api/trips/{trip['id']}/activities"
    assert client.post(url, json=activity_data(date="2026-11-10")).status_code == 201
    assert client.post(url, json=activity_data(date="2026-11-14")).status_code == 201


def test_update_activity_invalid_date(client, activity):
    response = client.put(f"/api/activities/{activity['id']}", json=activity_data(date="2027-01-01"))
    assert response.status_code == 400


def test_update_activity_invalid_time(client, activity):
    response = client.put(f"/api/activities/{activity['id']}", json=activity_data(time="9:00"))
    assert response.status_code == 400
    assert response.get_json() == {"error": "Time must be in HH:MM format"}
