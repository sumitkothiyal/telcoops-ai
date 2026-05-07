def get_complaints(location):
    complaints = {
        "Dallas": ["Slow internet", "No signal"],
        "New York": []
    }
    return complaints.get(location, [])