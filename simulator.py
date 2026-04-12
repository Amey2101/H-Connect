import requests
import random
import time

SERVER = "http://127.0.0.1:8000"

base_lat = 16.9944
base_lon = 73.3000


# -------------------------
# MOVE TOWARDS TARGET
# -------------------------
def move_towards(curr_lat, curr_lon, target_lat, target_lon, step=0.1):
    lat_diff = target_lat - curr_lat
    lon_diff = target_lon - curr_lon

    new_lat = curr_lat + step * lat_diff
    new_lon = curr_lon + step * lon_diff

    return new_lat, new_lon


# -------------------------
# FETCH DATA
# -------------------------
def get_ambulances():
    try:
        return requests.get(f"{SERVER}/ambulances").json()
    except:
        return []


def get_tickets():
    try:
        return requests.get(f"{SERVER}/tickets").json()
    except:
        return []


# -------------------------
# HOSPITAL STORAGE (TEMP)
# -------------------------
HOSPITALS = {
    "HOSP1": (16.991, 73.302),
    "HOSP2": (16.996, 73.305),
    "HOSP3": (16.989, 73.298),
    "HOSP4": (16.993, 73.307),
}


print("🚑 Simulator started\n")

positions = {}

while True:

    ambulances = get_ambulances()
    tickets = get_tickets()

    print(f"Active ambulances: {len(ambulances)}")

    for amb in ambulances:

        amb_id = amb["ambulance_id"]

        # INIT POSITION
        if amb_id not in positions:
            positions[amb_id] = (amb["latitude"], amb["longitude"])

        curr_lat, curr_lon = positions[amb_id]

        # -------------------------
        # FIND ACTIVE TICKET
        # -------------------------
        active_ticket = None

        for t in tickets:
            if t["ambulance_id"] == amb_id and t["hospital_id"]:
                active_ticket = t
                break

        # -------------------------
        # MOVEMENT LOGIC
        # -------------------------
        if active_ticket:

            hospital_id = active_ticket["hospital_id"]

            if hospital_id in HOSPITALS:
                target_lat, target_lon = HOSPITALS[hospital_id]

                new_lat, new_lon = move_towards(
                    curr_lat, curr_lon,
                    target_lat, target_lon
                )

                print(f"➡️ {amb_id} → {hospital_id}")

            else:
                continue

        else:
            # idle slow movement
            new_lat = curr_lat + random.uniform(-0.001, 0.001)
            new_lon = curr_lon + random.uniform(-0.001, 0.001)

        positions[amb_id] = (new_lat, new_lon)

        payload = {
            "ambulance_id": amb_id,
            "latitude": new_lat,
            "longitude": new_lon
        }

        try:
            requests.post(f"{SERVER}/ambulances/location", json=payload)
        except:
            print("⚠️ Server error")

        time.sleep(0.1)

    print("")
    time.sleep(1)