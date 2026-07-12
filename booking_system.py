# User id(PK) name email

# booking id(PK) user_id(FK) barber_id(FK) date hour status

# barber  id(PK) name specialty

import sqlite3

class BookingSystem:
    def __init__(self, db_path="booking_system.db"):
        self.db_path = db_path

    def _get_connection(self):
        # internal Database connector injection
        return sqlite3.connect(self.db_path)

    def create_booking(self, barber_id, hour):
        # 1. Start an IMMEDIATE transaction to lock the database file during write phase
        conn = self._get_connection()
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        try:
            # 2. Check duplicate slot
            cursor.execute('''
                SELECT id FROM bookings 
                WHERE barber_id = ? AND hour = ? AND status != 'cancelled'
            ''', (barber_id, hour))
            
            if cursor.fetchone():
                print(f"Error: Slot {hour}:00 for {barber_id} taken!")
                return None
                
            # 3. Insert pending record safely
            cursor.execute('''
                INSERT INTO bookings (barber_id, hour, status) 
                VALUES (?, ?, 'pending')
            ''', (barber_id, hour))
            
            booking_id = cursor.lastrowid
            conn.commit()
            print(f"Success: Created booking ID {booking_id}")
            return booking_id
            
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()
      
    def confirm_booking(self, booking_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. verify status machine
        cursor.execute('SELECT status FROM bookings WHERE id = ?', (booking_id,))
        result = cursor.fetchone()
        
        if not result:
            print("Error: Booking ID does not exist in DB.")
            conn.close()
            return False
            
        current_status = result[0]
        
        # 2. State transition
        if current_status != 'pending':
            print(f"Error: Cannot confirm. Current status is '{current_status}', not 'pending'.")
            conn.close()
            return False
            
        # 3. Update execution
        cursor.execute('UPDATE bookings SET status = "confirmed" WHERE id = ?', (booking_id,))
        
        conn.commit()
        conn.close()
        print(f"Success: Booking ID {booking_id} is now CONFIRMED in DB!")
        return True
