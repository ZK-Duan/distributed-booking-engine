from fastapi import FastAPI, HTTPException, status, Query, Request, Response, Cookie
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from booking_system import BookingSystem
from zoneinfo import ZoneInfo
import datetime

app = FastAPI(title="Booksy Enterprise Production Engine with Auth")
engine = BookingSystem()

# 数据传输模型
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=4, max_length=50)

class LoginRequest(BaseModel):
    username: str
    password: str

class BookingRequest(BaseModel):
    barber_name: str
    date: str
    hour: int

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    tz = ZoneInfo("Europe/Warsaw")
    today_str = datetime.datetime.now(tz).strftime("%Y-%m-%d")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Booksy Production Panel</title>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 700px; margin: 30px auto; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 12px; background-color: #f9f9f9; }}
            h2 {{ color: #FF5A5F; text-align: center; margin-bottom: 25px; }}
            .card {{ background: white; padding: 20px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input[type="text"], input[type="password"], input[type="date"], select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
            .slots-container {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }}
            .slot-btn {{ padding: 12px; text-align: center; border-radius: 6px; font-weight: bold; border: 2px solid; cursor: pointer; transition: all 0.2s; font-size: 13px; }}
            .slot-btn.free {{ background-color: #e6f4ea; color: #137333; border-color: #c4eed0; }}
            .slot-btn.free:hover {{ background-color: #34a853; color: white; }}
            .slot-btn.taken {{ background-color: #fce8e6; color: #c5221f; border-color: #fad2cf; cursor: not-allowed; opacity: 0.6; }}
            .booking-list {{ margin-top: 30px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #eee; }}
            .booking-item {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; }}
            .booking-item:last-child {{ border-bottom: none; }}
            .btn-group {{ display: flex; gap: 5px; }}
            .confirm-btn {{ background-color: #28a745; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }}
            .confirm-btn:hover {{ background-color: #218838; }}
            .cancel-btn {{ background-color: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }}
            .cancel-btn:hover {{ background-color: #bd2130; }}
            
            /* 登录/注册模块样式 */
            .auth-btn-group {{ display: flex; gap: 10px; margin-top: 15px; }}
            .primary-btn {{ background-color: #FF5A5F; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; flex: 1; }}
            .secondary-btn {{ background-color: #f0f0f0; color: #333; border: 1px solid #ccc; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; flex: 1; }}
            .logout-btn {{ background-color: #6c757d; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }}
            .user-badge {{ background-color: #e8f0fe; padding: 8px 12px; border-radius: 6px; display: inline-flex; align-items: center; gap: 10px; font-weight: bold; color: #1a73e8; }}
            
            #dashboard_content {{ display: none; }}
        </style>
    </head>
    <body>
        <h2>💈 Booksy Enterprise Closed-Loop Dashboard</h2>
        
        <div class="card">
            <div id="auth_view">
                <div class="form-group">
                    <label>👤 Username:</label>
                    <input type="text" id="username" placeholder="e.g., tom">
                </div>
                <div class="form-group">
                    <label>🔑 Password (Min 4 chars):</label>
                    <input type="password" id="password" placeholder="••••••••">
                </div>
                <div class="auth-btn-group">
                    <button class="primary-btn" onclick="handleAuth('login')">Login</button>
                    <button class="secondary-btn" onclick="handleAuth('register')">Register New Account</button>
                </div>
            </div>
            
            <div id="welcome_view" style="display: none; justify-content: space-between; align-items: center;">
                <div class="user-badge">
                    <span>👤 Active Safe Session:</span>
                    <span id="active_user_span"></span>
                </div>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>

        <div id="dashboard_content">
            <div class="card">
                <div class="form-group">
                    <label>💈 1. Choose Barber:</label>
                    <select id="barber_name" onchange="fetchAvailability()"><option value="alex">Alex</option><option value="bob">Bob</option></select>
                </div>
                <div class="form-group">
                    <label>📅 2. Select Date:</label>
                    <input type="date" id="date" value="{today_str}" onchange="fetchAvailability()">
                </div>
                <div class="form-group">
                    <label>🕒 3. Real-time Availability (Click to Book):</label>
                    <div id="slots_board" class="slots-container"></div>
                </div>
            </div>

            <div class="booking-list">
                <h3>📋 My Secure Active Sessions</h3>
                <div id="my_bookings_container">Loading sessions...</div>
            </div>
        </div>

        <script>
            let current_user = null;

            // 🌟 统一调用安全注册/登录 API
            async function handleAuth(action) {{
                const username = document.getElementById('username').value.trim();
                const password = document.getElementById('password').value;
                if(!username || !password) {{ alert("Please fill in both fields!"); return; }}
                
                const response = await fetch(`/${{action}}`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ username, password }})
                }});

                const data = await response.json();
                if (response.ok) {{
                    if(action === 'register') {{
                        alert("Registration successful! You can now log in.");
                    }} else {{
                        // 登录成功，锁定会话
                        current_user = username;
                        enterApp();
                    }}
                }} else {{
                    alert(`Error: ${{data.detail}}`);
                }}
            }}

            function enterApp() {{
                document.getElementById('active_user_span').innerText = current_user;
                document.getElementById('auth_view').style.display = 'none';
                document.getElementById('welcome_view').style.display = 'flex';
                document.getElementById('dashboard_content').style.display = 'block';
                
                // 清空密码输入框保障安全
                document.getElementById('password').value = '';
                
                fetchAvailability();
                fetchMyBookings();
            }}

            async function logout() {{
                await fetch('/logout', {{ method: 'POST' }});
                current_user = null;
                document.getElementById('username').value = '';
                document.getElementById('password').value = '';
                document.getElementById('auth_view').style.display = 'block';
                document.getElementById('welcome_view').style.display = 'none';
                document.getElementById('dashboard_content').style.display = 'none';
            }}

            async function fetchAvailability() {{
                if(!current_user) return;
                const barber_name = document.getElementById('barber_name').value;
                const date = document.getElementById('date').value;
                const board = document.getElementById('slots_board');
                try {{
                    const response = await fetch(`/availability?barber_name=${{barber_name}}&date=${{date}}`);
                    const slots = await response.json();
                    board.innerHTML = "";
                    slots.forEach(slot => {{
                        const btn = document.createElement('div');
                        btn.className = `slot-btn ${{slot.status}}`;
                        btn.innerText = `${{slot.hour}}:00 (${{slot.status.toUpperCase()}})`;
                        if(slot.status === 'free') {{
                            btn.onclick = () => makeBooking(slot.hour);
                        }}
                        board.appendChild(btn);
                    }});
                }} catch (err) {{ board.innerHTML = "Error loading slots."; }}
            }}

            async function makeBooking(hour) {{
                if(!current_user) return;
                // 🌟 前端 Payload 彻底不再包含 username，安全交由后端 Cookie 处理
                const payload = {{ barber_name: document.getElementById('barber_name').value, date: document.getElementById('date').value, hour }};
                const response = await fetch('/bookings', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});
                if (response.ok) {{ fetchAvailability(); fetchMyBookings(); }} 
                else {{ const data = await response.json(); alert(`Failed: ${{data.detail}}`); }}
            }}

            async function fetchMyBookings() {{
                if(!current_user) return;
                const container = document.getElementById('my_bookings_container');
                try {{
                    // 🌟 查询自己的预约不再通过路径变量传用户名，后端直接解析 Cookie
                    const response = await fetch('/my-bookings');
                    const bookings = await response.json();
                    if(bookings.length === 0) {{ container.innerHTML = "No active bookings found."; return; }}
                    container.innerHTML = "";
                    bookings.forEach(b => {{
                        const item = document.createElement('div');
                        item.className = "booking-item";
                        item.innerHTML = `
                            <div><b>[ID: ${{b.id}}]</b> ${{b.date}} @ ${{b.hour}}:00 with <b>${{b.barber}}</b> [${{b.status.toUpperCase()}}]</div>
                            <div class="btn-group">
                                ${{b.status === 'pending' ? `<button class="confirm-btn" onclick="confirmBooking(${{b.id}})">Confirm</button>` : ''}}
                                <button class="cancel-btn" onclick="cancelBooking(${{b.id}})">Cancel</button>
                            </div>
                        `;
                        container.appendChild(item);
                    }});
                }} catch(err) {{ container.innerHTML = "Error loading data."; }}
            }}

            async function confirmBooking(id) {{
                const response = await fetch(`/bookings/${{id}}/confirm`, {{ method: 'POST' }});
                if(response.ok) {{ fetchMyBookings(); }} 
                else {{ const data = await response.json(); alert(`Confirmation failed.`); }}
            }}

            async function cancelBooking(id) {{
                const response = await fetch(`/bookings/${{id}}`, {{ method: 'DELETE' }});
                if(response.ok) {{ fetchAvailability(); fetchMyBookings(); }} 
                else {{ const data = await response.json(); alert(`Cancel failed.`); }}
            }}
        </script>
    </body>
    </html>
    """

# 安全中间件逻辑（验证 Cookie 中的 Session）
def get_current_user_from_cookie(request: Request) -> str:
    user = request.cookies.get("session_user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session expired or unauthorized. Please log in."
        )
    return user

# 路由定义

@app.post("/register")
async def register(request: RegisterRequest):
    success = engine.register_user(request.username, request.password)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists.")
    return {"status": "success", "message": "User registered successfully."}

@app.post("/login")
async def login(request: LoginRequest, response: Response):
    is_valid = engine.verify_user(request.username, request.password)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    
    # 写入安全 Session Cookie，不允许 JavaScript 修改（httponly 防止 XSS 攻击）
    response.set_cookie(key="session_user", value=request.username, httponly=True, max_age=3600)
    return {"status": "success", "message": "Logged in successfully."}

@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session_user")
    return {"status": "success", "message": "Logged out."}

@app.get("/availability")
async def get_availability(barber_name: str, date: str):
    return engine.get_availability(barber_name=barber_name, date_str=date)

@app.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_new_booking(request: Request, booking: BookingRequest):
    # 直接从 Cookie 中获取当前登录用户名
    username = get_current_user_from_cookie(request)
    booking_id = engine.create_booking(username, booking.barber_name, booking.date, booking.hour)
    if booking_id is None:
        raise HTTPException(status_code=409, detail="Slot is locked or already taken.")
    return {"status": "success", "booking_id": booking_id}

@app.get("/my-bookings")
async def get_my_bookings(request: Request):
    # 从 Cookie 提取用户名，用户无法伪造他人名字查询
    username = get_current_user_from_cookie(request)
    return engine.get_user_bookings(username)

@app.post("/bookings/{booking_id}/confirm")
async def confirm_existing_booking(booking_id: int, request: Request):
    # 从 Cookie 获取当前操作者用户名
    username = get_current_user_from_cookie(request)
    success = engine.confirm_booking(booking_id, username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unauthorized or appointment already expired."
        )
    return {"status": "success", "message": "Booking confirmed."}

@app.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: int, request: Request):
    # 从 Cookie 获取当前操作者用户名
    username = get_current_user_from_cookie(request)
    success = engine.cancel_booking(booking_id, username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unauthorized, past appointment or already cancelled."
        )
    return {"status": "success", "message": "Booking cancelled."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
