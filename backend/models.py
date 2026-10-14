from datetime import date

from database import get_db

TRIP_STATUSES = ("upcoming", "ongoing", "completed")


def get_trip_status(start_date, end_date):
    today = date.today().isoformat()
    if today < start_date:
        return "upcoming"
    if today > end_date:
        return "completed"
    return "ongoing"


def trip_to_dict(row):
    trip = dict(row)
    trip["status"] = get_trip_status(trip["start_date"], trip["end_date"])
    return trip


def find_trip(trip_id):
    return get_db().execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()


def find_activity(activity_id):
    return get_db().execute("SELECT * FROM activities WHERE id = ?", (activity_id,)).fetchone()


def find_duplicate_activity(trip_id, title, date, time, location, exclude_id=None):
    query = """SELECT * FROM activities
               WHERE trip_id = ? AND title = ? AND date = ? AND time = ? AND location = ?"""
    params = [trip_id, title, date, time, location]
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    return get_db().execute(query, params).fetchone()
