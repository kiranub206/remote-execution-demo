import streamlit as st
import sqlite3
import time
import threading
import os
from datetime import datetime

# ===================== CONFIG =====================
DB = "db.sqlite"
LOG_FILE = "execution.log"

# ===================== LOGGING =====================
def log_event(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} | {msg}\n")

# ===================== DATABASE =====================
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller TEXT,
    pc_name TEXT,
    hours INTEGER,
    price INTEGER,
    status TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER,
    buyer TEXT,
    start REAL,
    end REAL,
    active INTEGER
)
""")

conn.commit()

# ===================== UI =====================
st.set_page_config(page_title="PC Capacity Marketplace", layout="centered")
st.title("🖥 PC Capacity Marketplace — Prototype Demo")

role = st.sidebar.selectbox("Login as", ["Admin", "Seller", "Buyer"])

# ===================== ADMIN =====================
if role == "Admin":
    st.header("👑 Admin Panel")

    rows = c.execute("SELECT * FROM slots").fetchall()

    if not rows:
        st.info("No slots submitted yet.")

    for r in rows:
        st.write(
            f"🆔 {r[0]} | Seller: {r[1]} | PC: {r[2]} | "
            f"{r[3]} hrs | ₹{r[4]}/hr | Status: {r[5]}"
        )

        if r[5] == "pending":
            if st.button(f"Approve Slot {r[0]}"):
                c.execute("UPDATE slots SET status='approved' WHERE id=?", (r[0],))
                conn.commit()
                log_event(f"Admin approved slot {r[0]}")
                st.success("Slot approved")

# ===================== SELLER =====================
elif role == "Seller":
    st.header("🖥 Seller Dashboard")

    seller = st.text_input("Seller name")
    pc = st.text_input("PC name (e.g., Gaming-PC-01)")
    hrs = st.number_input("Hours available", 1, 24, 2)
    price = st.number_input("Price per hour (₹)", 50, 1000, 100)

    if st.button("Create Slot"):
        if seller and pc:
            c.execute(
                "INSERT INTO slots VALUES (NULL,?,?,?,?,?)",
                (seller, pc, hrs, price, "pending")
            )
            conn.commit()
            log_event(f"Seller {seller} created slot for {pc}")
            st.success("Slot submitted for admin approval")
        else:
            st.error("Fill all fields")

# ===================== BUYER =====================
elif role == "Buyer":
    st.header("🧑‍💻 Buyer Dashboard")

    buyer = st.text_input("Your name")

    slots = c.execute("SELECT * FROM slots WHERE status='approved'").fetchall()

    if not slots:
        st.info("No approved slots available.")

    for r in slots:
        st.write(
            f"🖥 {r[2]} | {r[3]} hrs | ₹{r[4]}/hr"
        )

        if st.button(f"Book Slot {r[0]}"):
            if not buyer:
                st.error("Enter your name")
            else:
                start = time.time()
                end = start + r[3] * 3600

                c.execute(
                    "INSERT INTO bookings VALUES (NULL,?,?,?,?,1)",
                    (r[0], buyer, start, end)
                )
                conn.commit()

                log_event(f"Buyer {buyer} booked slot {r[0]}")
                st.success("Session started 🎮")

                # ===== BACKGROUND EXECUTION =====
                def launch_demo_app():
                    try:
                        log_event("Launching demo application")
                        if os.name == "nt":
                            os.startfile("notepad.exe")
                        else:
                            os.system("xeyes &")  # Linux demo-safe
                        log_event("Application launched successfully")
                    except Exception as e:
                        log_event(f"Launch failed: {e}")

                threading.Thread(target=launch_demo_app, daemon=True).start()

# ===================== ACTIVE SESSIONS =====================
st.divider()
st.subheader("⏱ Active Sessions")

active = c.execute("SELECT * FROM bookings WHERE active=1").fetchall()

if not active:
    st.info("No active sessions.")

for a in active:
    remaining = int(a[4] - time.time())

    if remaining <= 0:
        c.execute("UPDATE bookings SET active=0 WHERE id=?", (a[0],))
        conn.commit()
        log_event(f"Session {a[0]} ended")
        st.warning(f"Booking {a[0]} ended")
    else:
        st.write(
            f"Booking {a[0]} | Buyer: {a[2]} | "
            f"Remaining: {remaining//3600}h {(remaining%3600)//60}m {(remaining%60)}s"
        )

# ===================== LOG VIEW =====================
st.divider()
st.subheader("📜 Execution Logs")

if st.button("View Logs"):
    try:
        with open(LOG_FILE) as f:
            st.text(f.read())
    except:
        st.text("No logs yet.")
