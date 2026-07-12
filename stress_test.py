# stress_test.py
import os
import random
import datetime
from zoneinfo import ZoneInfo
import concurrent.futures
from booking_system import BookingSystem

def attempt_random_booking(user_id: int, sys: BookingSystem, barbers: list, dates: list, hours: list) -> dict:
    """
    Simulates a user booking a random barber at a random time slot.
    """
    username = f"user_{user_id}"
    barber = random.choice(barbers)
    date = random.choice(dates)
    hour = random.choice(hours)
    
    try:
        booking_id = sys.create_booking(
            username=username,
            barber_name=barber,
            date=date,
            hour=hour
        )
        return {
            "username": username,
            "success": booking_id is not None,
            "booking_id": booking_id,
            "target": f"{barber} @ {date} {hour}:00",
            "key": (barber, date, hour),
            "error": None
        }
    except Exception as e:
        return {
            "username": username,
            "success": False,
            "booking_id": None,
            "target": f"{barber} @ {date} {hour}:00",
            "key": (barber, date, hour),
            "error": str(e)
        }

def run_distributed_stress_test():
    test_db = "stress_test_engine.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    sys = BookingSystem(db_path=test_db)
    
    # Realistic resource pool
    barbers = ["alex", "bob", "charlie"]
    
    # 动态生成未来的日期，防止硬编码过期
    tz = ZoneInfo("Europe/Warsaw")
    future_date = (datetime.datetime.now(tz) + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    dates = [future_date]
    
    hours = [14, 15, 16]  # 3 barbers * 3 slots = 9 unique available slots in total
    
    concurrency_limit = 100 # 100 parallel users racing for these 9 slots
    
    print(f"🚀 Initializing Distributed Concurrency Stress Test...")
    print(f"🔥 Spawning {concurrency_limit} parallel threads distributing requests across:")
    print(f"   - Barbers : {barbers}")
    print(f"   - Slots   : {hours}:00")
    print("-" * 75)

    results = []
    
    # Trigger parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
        futures = {
            executor.submit(attempt_random_booking, i, sys, barbers, dates, hours): i 
            for i in range(1, concurrency_limit + 1)
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # --- POST-TEST METRIC ANALYSIS ---
    successes = [r for r in results if r["success"] is True]
    failures = [r for r in results if r["success"] is False]
    
    # Track successful bookings per unique slot
    slot_winners = {}
    double_booking_detected = False

    for s in successes:
        slot_key = s["key"]
        if slot_key in slot_winners:
            double_booking_detected = True
            slot_winners[slot_key].append(s["username"])
        else:
            slot_winners[slot_key] = [s["username"]]

    print("\n" + "=" * 30 + " DISTRIBUTED RESULTS " + "=" * 30)
    print(f"Total Parallel Requests Sent : {concurrency_limit}")
    print(f"Successful Bookings Created  : {len(successes)} (Max theoretical: 9)")
    print(f"Blocked/Failed Bookings      : {len(failures)}")
    print("=" * 75)

    # --- CRITICAL INTEGRITY ASSERTIONS ---
    print("\n🔑 System Integrity Verification:")
    if double_booking_detected:
        print("❌ CRITICAL FAILURE: Double-booking/race condition detected!")
        for slot, users in slot_winners.items():
            if len(users) > 1:
                print(f"   Conflict on Slot {slot[0]} @ {slot[2]}:00 -> Booked by: {users}")
    else:
        print("   SUCCESS: Zero double-bookings detected.")
        print("   Detailed Slot Allocations:")
        for slot, users in slot_winners.items():
            print(f"   - Slot [{slot[0]} at {slot[2]}:00] successfully claimed by: {users[0]}")

    # Resource Teardown
    if os.path.exists(test_db):
        os.remove(test_db)
        print("\n🧹 Stress test database cleaned up successfully.")

if __name__ == "__main__":
    run_distributed_stress_test()
