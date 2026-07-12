# User id(PK) name email

# booking id(PK) user_id(FK) barber_id(FK) date hour status

# barber  id(PK) name specialty

class BookingSystem:
    def __init__(self):
        # number {barber_name,hour,status}
        self.bookings = {}
        self.next_id = 1

    def create_booking(self, barber_id, hour):
        """Create a booking with a default 'pending' status."""

        # check slot already taken or not
        for existing_booking in self.bookings.values():
            if existing_booking['barber_id'] == barber_id and existing_booking['hour'] == hour:
                if existing_booking['status'] != 'cancelled':
                    print(f"Error: Slot {hour}:00 for {barber_id} is already taken!")
                    return None
        # if free
        booking_id = self.next_id
        self.bookings[booking_id] = {
            'barber_id': barber_id,
            'hour': hour,
            'status': 'pending'
        }
        self.next_id += 1;
        print(f"Success: Created pending booking ID{booking_id} at {hour}:00")
        return booking_id

    def confirm_booking(self, booking_id):
        """Strict State Machine: Only 'pending' bookings can be confirmed."""
        if booking_id not in self.bookings:
            print("Error: Booking ID does not exist.")
            return False

        current_status = self.bookings[booking_id]['status']

        if current_status != 'pending':
            print(f" Error: Cannot confirm. Current status is '{current_status}', not 'pending'.")
            return False

        self.bookings[booking_id]['status'] = 'confirmed'
        print(f" Success: Booking ID {booking_id} is now CONFIRMED!")
        return True
