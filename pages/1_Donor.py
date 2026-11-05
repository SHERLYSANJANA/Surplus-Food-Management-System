import re
import streamlit as st
import ui
from psycopg import errors
from db import get_connected

ui.page_header("🧑‍🍳", "Donor Registration", "Register to donate surplus food.")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{10,15}$")

with st.form("donor_form"):
    donor_name = st.text_input("Donor Name")
    donor_location = st.text_input("Location")
    email_id = st.text_input("Email")
    phone_no = st.text_input("Phone Number")
    submitted = st.form_submit_button("Register Donor")

if submitted:
    if not all(v.strip() for v in [donor_name, donor_location, email_id, phone_no]):
        st.warning("Please fill in all fields.")
    elif not EMAIL_RE.match(email_id.strip()):
        st.warning("Please enter a valid email address.")
    elif not PHONE_RE.match(phone_no.strip()):
        st.warning("Phone number must be 10-15 digits (optional leading +).")
    else:
        try:
            with get_connected() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO donor (donor_name, donor_location, email_id, phone_no)
                        VALUES (%s, %s, %s, %s)
                        RETURNING donor_id
                    """, (donor_name.strip(), donor_location.strip(),
                          email_id.strip().lower(), phone_no.strip()))
                    donor_id = cur.fetchone()[0]
            st.success(f"Donor registered successfully! ID: {donor_id}")
        except errors.UniqueViolation:
            st.error("A donor with this email already exists.")
        except Exception as e:
            st.error(f"Could not register donor: {e}")
