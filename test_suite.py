# test_suite.py
import os
import datetime
from zoneinfo import ZoneInfo
from booking_system import BookingSystem

def test_enterprise_flow():
    # 1. Initialize a clean, isolated database for testing
    test_db = "test_engine.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    sys = BookingSystem(db_path=test_db)
    
    # 动态生成未来的日期，防止硬编码过期
    tz = ZoneInfo("Europe/Warsaw")
    future_date = (datetime.datetime.now(tz) + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Scenario A: Standard creation and state transition
    bid = sys.create_booking(username="alice", barber_name="alex", date=future_date, hour=14)
    assert bid is not None, "Booking should be successfully created."
    
    # Scenario B: Slot locking to prevent double-booking (P0 concurrency defense)
    duplicate_bid = sys.create_booking(username="bob", barber_name="alex", date=future_date, hour=14)
    assert duplicate_bid is None, "The same time slot for the same resource must be locked, returning None."
    
    # Scenario C: Idempotency of confirmation
    assert sys.confirm_booking(bid) is True, "First confirmation should succeed."
    assert sys.confirm_booking(bid) is False, "Subsequent confirmations must return False (Idempotency)."
    
    # Scenario D: Past date cancellation restriction (P1 edge-case defense)
    past_bid = sys.create_booking(username="tom", barber_name="bob", date="2020-01-01", hour=10)
    assert sys.cancel_booking(past_bid) is False, "Cancellation of historical bookings must be rejected."
    
    # Clean up the test database after a successful run
    if os.path.exists(test_db):
        os.remove(test_db)
        
    print("All enterprise validation test cases passed successfully.")

if __name__ == "__main__":
    test_enterprise_flow()
