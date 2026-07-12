       ┌─────────────────────────────────────────────────────────┐
       │             Browser Client (HTML5 / JS)                 │
       └────────────────────────────┬────────────────────────────┘
                                    │ Http Requests (HTTPOnly Cookies)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             FastAPI Web Router (main.py)                │
       │    - Session Validate  - Cookie Parser  - HTTP Response │
       └────────────────────────────┬────────────────────────────┘
                                    │ Python Object Calls (Clean APIs)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │           Booking Engine Service (booking_system.py)    │
       │    - PBKDF2 Hashing    - Concurrency Control            │
       │    - Business Logic    - Session State Machine          │
       └────────────────────────────┬────────────────────────────┘
                                    │ Raw SQL (Atomic Operations)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                 SQLite Engine (WAL Mode)                │
       │    - Filtered Unique Index  - Thread-safe Locks         │
       └─────────────────────────────────────────────────────────┘
