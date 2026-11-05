import re
import streamlit as st
import ui
import pandas as pd
from psycopg import errors
from db import get_connected

ui.page_header("🤝", "Receiver Portal", "Register receivers and request the food they need.")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{10,15}$")

tab1, tab2 = st.tabs(["Register Receiver", "Request Food"])

with tab1:
    st.subheader("Receiver Registration")
    with st.form("receiver_form"):
        receiver_name = st.text_input("Receiver Name")
        email = st.text_input("Email")
        phone_no = st.text_input("Phone Number")
        register = st.form_submit_button("Register Receiver")

    if register:
        if not all(v.strip() for v in [receiver_name, email, phone_no]):
            st.warning("Please fill in all fields.")
        elif not EMAIL_RE.match(email.strip()):
            st.warning("Please enter a valid email address.")
        elif not PHONE_RE.match(phone_no.strip()):
            st.warning("Phone number must be 10-15 digits (optional leading +).")
        else:
            try:
                with get_connected() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO receiver (receiver_name, email, phone_no)
                            VALUES (%s, %s, %s)
                            RETURNING receiver_id
                        """, (receiver_name.strip(), email.strip().lower(), phone_no.strip()))
                        receiver_id = cur.fetchone()[0]
                st.success(f"Receiver registered successfully! ID: {receiver_id}")
            except errors.UniqueViolation:
                st.error("A receiver with this email already exists.")
            except Exception as e:
                st.error(f"Registration failed: {e}")

with tab2:
    st.subheader("Request Food")
    try:
        with get_connected() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT receiver_id, receiver_name FROM receiver ORDER BY receiver_name")
                receivers = cur.fetchall()

        if not receivers:
            st.info("Register a receiver before requesting food.")
        else:
            options = {f"{name} (ID: {rid})": rid for rid, name in receivers}
            with st.form("request_form"):
                receiver_label = st.selectbox("Select Receiver", list(options))
                food_item = st.text_input("Food Item Needed")
                quantity = st.number_input("Quantity Required", min_value=1, step=1)
                submitted = st.form_submit_button("Submit Request")

            if submitted:
                if not food_item.strip():
                    st.warning("Please enter the food item.")
                else:
                    with get_connected() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO receiver_request (receiver_id, food_item, quantity)
                                VALUES (%s, %s, %s)
                                RETURNING request_id
                            """, (options[receiver_label], food_item.strip(), int(quantity)))
                            request_id = cur.fetchone()[0]
                    st.success(f"Request submitted successfully! Request ID: {request_id}")

            st.subheader("Open requests")
            with get_connected() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT q.request_id, r.receiver_name, q.food_item, q.quantity,
                               q.status, q.request_date
                        FROM receiver_request q JOIN receiver r ON r.receiver_id = q.receiver_id
                        WHERE q.status IN ('Pending', 'Partial')
                        ORDER BY q.request_date DESC LIMIT 20
                    """)
                    rows = cur.fetchall()
            if rows:
                st.dataframe(pd.DataFrame(rows, columns=["ID", "Receiver", "Food", "Qty", "Status", "Requested"]),
                             width="stretch", hide_index=True)
            else:
                st.caption("No open requests.")
    except Exception as e:
        st.error(f"Request operation failed: {e}")
