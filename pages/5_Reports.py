import streamlit as st
import ui
import pandas as pd
from db import get_connected

ui.page_header("📊", "Reports", "Overview of donors, requests and allocations.")

try:
    with get_connected() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM donor")
            donors = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM receiver")
            receivers = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM donation")
            donations = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM receiver_request")
            requests = cur.fetchone()[0]
            cur.execute("""
                SELECT COALESCE(SUM(allocated_quantity), 0) FROM match_allocation
                WHERE allocation_status IN ('Approved', 'Completed')
            """)
            allocated = cur.fetchone()[0]
            cur.execute("""
                SELECT status, COUNT(*) FROM receiver_request
                GROUP BY status ORDER BY status
            """)
            status_data = cur.fetchall()
            cur.execute("""
                SELECT d.donor_name, COUNT(DISTINCT p.post_id), COALESCE(SUM(i.quantity), 0)
                FROM donor d
                LEFT JOIN donation p ON p.donor_id = d.donor_id
                LEFT JOIN donation_items i ON i.post_id = p.post_id
                GROUP BY d.donor_id, d.donor_name
                ORDER BY 3 DESC
            """)
            donor_data = cur.fetchall()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Donors", donors)
    c2.metric("Receivers", receivers)
    c3.metric("Donation Posts", donations)
    c4.metric("Food Requests", requests)
    st.metric("Food Allocated (units)", allocated)

    st.subheader("Request Status Summary")
    if status_data:
        st.bar_chart(pd.DataFrame(status_data, columns=["Status", "Count"]).set_index("Status"))
    else:
        st.info("No requests available yet.")

    st.subheader("Donor-wise Donation Report")
    if donor_data:
        st.dataframe(
            pd.DataFrame(donor_data, columns=["Donor", "Donation Posts", "Food Quantity"]),
            width="stretch",
        )
    else:
        st.info("No donors registered yet.")
except Exception as e:
    st.error(f"Could not generate reports: {e}")
