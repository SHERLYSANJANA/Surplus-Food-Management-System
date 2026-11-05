from db import get_connected

with get_connected() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE donor_photos, match_allocation, donation_items,
                     receiver_request, donation, receiver, donor
            RESTART IDENTITY CASCADE
        """)
print("All data deleted.")