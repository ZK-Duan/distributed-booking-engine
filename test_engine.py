import tempfile
import os
import datetime
from zoneinfo import ZoneInfo
from booking_system import BookingSystem

def run_integration_tests():
    # 1. Create a temporary, isolated database file just for this test run
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd) # Close the file descriptor so SQLite can take full control

    # 动态生成未来的日期，防止硬编码过期
    tz = ZoneInfo("Europe/Warsaw")
    future_date = (datetime.datetime.now(tz) + datetime.timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        print(f"🚀 Initializing ephemeral test database at: {temp_db_path}")
        sys = BookingSystem(db_path=temp_db_path)

        print(f"\n--- Test 1: First Booking (Should Succeed on {future_date}) ---")
        # ✅ 已修复：传入了正确的 username 和 barber_name，删除了重复的 hour
        bid = sys.create_booking(username="test_user", barber_name="alex", date=future_date, hour=14)
        if bid:
            print(f" Pass: Booking ID {bid} created successfully.")
        else:
            print(" Fail: First booking failed.")

        print("\n--- Test 2: Duplicate Booking (Should Be Blocked by Lock) ---")
        # ✅ 已修复：传入了正确的 username 和 barber_name，删除了重复的 hour
        duplicate_bid = sys.create_booking(username="test_user2", barber_name="alex", date=future_date, hour=14)
        if duplicate_bid is None:
            print(" Pass: Duplicate booking successfully blocked by database logic.")
        else:
            print(" Fail: Duplicate booking bypassed the check! Race condition detected.")

        if bid:
            print("\n--- Test 3: Confirm Booking (State Machine Transition) ---")
            success = sys.confirm_booking(booking_id=bid)
            if success:
                print(" Pass: Booking successfully confirmed.")
            else:
                print(" Fail: Confirmation rejected illegally.")

    finally:
        # 2. Guaranteed Cleanup: Wipe the temporary database from existence
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
            print("\n🧹 Ephemeral test database completely wiped from existence.")

if __name__ == "__main__":
    run_integration_tests()
