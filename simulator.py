import requests
import time
import math

SERVER = "http://127.0.0.1:8000"


# -------------------------
# CONSTANT SPEED MOVEMENT
# -------------------------
def move_towards(curr_lat, curr_lon, target_lat, target_lon, step=0.003):

    lat_diff = target_lat - curr_lat
    lon_diff = target_lon - curr_lon

    distance = math.sqrt(lat_diff**2 + lon_diff**2)

    # 🔥 snap if very close
    if distance < step:
        return target_lat, target_lon

    # 🔥 normalized movement
    new_lat = curr_lat + (lat_diff / distance) * step
    new_lon = curr_lon + (lon_diff / distance) * step

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
# SIMULATOR START
# -------------------------
print("🚑 Simulator started\n")

# store live positions
positions = {}

while True:

    ambulances = get_ambulances()
    tickets = get_tickets()

    print(f"Active ambulances: {len(ambulances)}")

    for amb in ambulances:

        amb_id = amb["ambulance_id"]

        # -------------------------
        # INIT FROM DB (REAL SOURCE)
        # -------------------------
        if amb_id not in positions:
            positions[amb_id] = (
                amb["latitude"],
                amb["longitude"]
            )

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

            # 🔥 use hospital coords from backend websocket logic
            # since DB doesn't store lat/lon, we fetch via hospitals API
            try:
                res = requests.get(
                    f"{SERVER}/hospitals/nearby?latitude={curr_lat}&longitude={curr_lon}"
                )
                hospitals = res.json()

                hospital = next(
                    (h for h in hospitals if h["hospital_id"] == active_ticket["hospital_id"]),
                    None
                )

                if hospital:
                    target_lat = hospital["latitude"]
                    target_lon = hospital["longitude"]

                    new_lat, new_lon = move_towards(
                        curr_lat, curr_lon,
                        target_lat, target_lon
                    )

                    print(f"➡️ {amb_id} → {active_ticket['hospital_id']}")

                else:
                    print(f"⚠️ Hospital not found for {amb_id}")
                    continue

            except:
                print("⚠️ Hospital fetch error")
                continue

        else:
            # 🔥 REALISTIC: NO MOVEMENT WHEN IDLE
            new_lat, new_lon = curr_lat, curr_lon

        # -------------------------
        # UPDATE POSITION
        # -------------------------
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