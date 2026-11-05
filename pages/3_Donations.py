import streamlit as st
import ui
import pandas as pd
from datetime import datetime, time, date
from db import get_connected

ui.page_header("🍱", "Food Donations", "Post surplus food for redistribution.")

try:
    with get_connected() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT donor_id, donor_name FROM donor ORDER BY donor_name")
            donors = cur.fetchall()

    if not donors:
        st.warning("Register a donor first.")
        st.stop()

    options = {f"{name} (ID: {donor_id})": donor_id for donor_id, name in donors}
    with st.form("donation_form"):
        donor_label = st.selectbox("Select Donor", list(options))
        item_name = st.text_input("Food Item")
        quantity = st.number_input("Quantity (meals/units)", min_value=1, step=1)
        expiry_date = st.date_input("Expiry Date", min_value=date.today())
        expiry_clock = st.time_input("Expiry Time", value=time(23, 59))
        submitted = st.form_submit_button("Post Donation")

    if submitted:
        if not item_name.strip():
            st.warning("Please enter a food item.")
        else:
            expiry = datetime.combine(expiry_date, expiry_clock)
            if expiry <= datetime.now():
                st.error("Expiry must be in the future.")
            else:
                with get_connected() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO donation (expiry_time, donor_id)
                            VALUES (%s, %s)
                            RETURNING post_id
                        """, (expiry, options[donor_label]))
                        post_id = cur.fetchone()[0]
                        cur.execute("""
                            INSERT INTO donation_items (post_id, item_no, item_name, quantity)
                            VALUES (%s, 1, %s, %s)
                        """, (post_id, item_name.strip(), int(quantity)))
                st.success(f"Donation posted successfully! Post ID: {post_id}")

    st.subheader("Active donations")
    with get_connected() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.post_id, d.donor_name, i.item_name, i.quantity, p.expiry_time
                FROM donation p
                JOIN donor d ON d.donor_id = p.donor_id
                JOIN donation_items i ON i.post_id = p.post_id
                WHERE p.expiry_time > LOCALTIMESTAMP
                ORDER BY p.expiry_time LIMIT 20
            """)
            rows = cur.fetchall()
    if rows:
        st.dataframe(pd.DataFrame(rows, columns=["Post", "Donor", "Food", "Qty", "Expires"]),
                     width="stretch", hide_index=True)
    else:
        st.caption("No active donations.")
except Exception as e:
    st.error(f"Something went wrong: {e}")
