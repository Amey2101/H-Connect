import requests
import random
import time

SERVER = "http://127.0.0.1:8000"

base_lat = 16.9944
base_lon = 73.3000


# -------------------------
# FETCH AMBULANCES FROM DB
# -------------------------
def get_ambulances():
    try:
        res = requests.get(f"{SERVER}/ambulances")
        return res.json()
    except Exception as e:
        print("⚠️ Cannot reach server. Is backend running?")
        return []


# -------------------------
# SIMULATION LOOP
# -------------------------
print("🚑 Simulator started")
print("👉 Waiting for ambulances to be registered via Swagger...\n")

while True:

    ambulances = get_ambulances()

    # 🔥 Debug visibility
    print(f"Active ambulances: {len(ambulances)}")

    if not ambulances:
        print("⚠️ No ambulances registered\n")
        time.sleep(3)
        continue

    for amb in ambulances:

        # 🔥 Skip busy ambulances (important fix)
        if amb["status"] == "BUSY":
            continue

        payload = {
            "ambulance_id": amb["ambulance_id"],
            "latitude": base_lat + random.uniform(-0.01, 0.01),
            "longitude": base_lon + random.uniform(-0.01, 0.01)
        }

        try:
            requests.post(f"{SERVER}/ambulances/location", json=payload)
        except Exception:
            print("⚠️ Skipping update (server issue)")

        # 🔥 Prevent overload
        time.sleep(0.5)

    print("")  # spacing for readability
    time.sleep(3)