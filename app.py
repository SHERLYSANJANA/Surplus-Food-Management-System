import streamlit as st
import ui
from db import get_connected

ui.setup("Food Redistribution", "🍱")

st.markdown(
    '<div class="hero"><h1>🍱 Food Redistribution System</h1>'
    "<p>Connecting surplus food with the people who need it.</p></div>",
    unsafe_allow_html=True,
)

try:
    with get_connected() as conn:
        with conn.cursor() as cur:
            def one(sql):
                cur.execute(sql)
                return cur.fetchone()[0]

            donors = one("SELECT COUNT(*) FROM donor")
            receivers = one("SELECT COUNT(*) FROM receiver")
            donations = one("SELECT COUNT(*) FROM donation")
            active = one("SELECT COUNT(*) FROM donation WHERE expiry_time > LOCALTIMESTAMP")
            open_req = one("SELECT COUNT(*) FROM receiver_request WHERE status IN ('Pending','Partial')")
            fulfilled = one("SELECT COUNT(*) FROM receiver_request WHERE status = 'Fulfilled'")
            allocated = one("""SELECT COALESCE(SUM(allocated_quantity), 0) FROM match_allocation
                               WHERE allocation_status IN ('Approved','Completed')""")

    r1 = st.columns(4)
    r1[0].metric("🧑‍🍳 Donors", donors)
    r1[1].metric("🤝 Receivers", receivers)
    r1[2].metric("🍱 Donation Posts", donations)
    r1[3].metric("⏳ Active (unexpired)", active)
    r2 = st.columns(4)
    r2[0].metric("📬 Open Requests", open_req)
    r2[1].metric("✅ Fulfilled Requests", fulfilled)
    r2[2].metric("📦 Units Allocated", allocated)
except Exception as e:
    st.error(f"Database connection failed: {e}")

st.subheader("How it works")
steps = [
    ("1", "Register", "Donors and receivers sign up with their contact details."),
    ("2", "Post & request", "Donors post surplus food; receivers request what they need."),
    ("3", "Match", "Requests are matched to unexpired donations, best match first."),
]
for col, (n, title, text) in zip(st.columns(3), steps):
    col.markdown(
        f'<div class="step-card"><span class="num">{n}</span><h4>{title}</h4><p>{text}</p></div>',
        unsafe_allow_html=True,
    )

st.subheader("Quick actions")
links = [
    ("pages/1_Donor.py", "Register donor", "🧑‍🍳"),
    ("pages/2_Receivers.py", "Receivers & requests", "🤝"),
    ("pages/3_Donations.py", "Post a donation", "🍱"),
    ("pages/4_Matching.py", "Match & allocate", "🔗"),
    ("pages/5_Reports.py", "Reports", "📊"),
]
for col, (path, label, icon) in zip(st.columns(5), links):
    col.page_link(path, label=label, icon=icon, width="stretch")
