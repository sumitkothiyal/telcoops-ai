def get_network_status(input_data):
    # Expected format: "Location | Scenario"
    parts = input_data.split("|")

    location = parts[0].strip()
    scenario = parts[1].strip() if len(parts) > 1 else "Normal Day"

    scenarios = {
        "Normal Day": {
            "status": "healthy",
            "latency": "low",
            "packet_loss": 1
        },
        "Peak Traffic": {
            "status": "degraded",
            "latency": "high",
            "packet_loss": 5
        },
        "Local Outage": {
            "status": "degraded",
            "latency": "very high",
            "packet_loss": 15
        },
        "Major Outage": {
            "status": "down",
            "latency": "no connectivity",
            "packet_loss": 30
        }
    }

    data = scenarios.get(scenario, scenarios["Normal Day"])

    return {
        "location": location,
        "scenario": scenario,
        "status": data["status"],
        "latency": data["latency"],
        "packet_loss": data["packet_loss"]
    }