import difflib
from datetime import datetime

import pandas as pd
import streamlit as st
import ui
from db import get_connected

ui.page_header("🔗", "Food Matching & Allocation", "Match requests with the best available donations.")
st.caption(
    "Matches requests with unexpired donations by food name (exact or similar), "
    "ranked by name similarity, how much of the need is covered, and expiry urgency. "
    "A donor with more food than requested is a valid match; the surplus stays available."
)

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))


def approve_allocation(sel, qty):
    """Allocate qty units inside one transaction. Returns (match_id, new_status)."""
    with get_connected() as conn:
        with conn.cursor() as cur:
            # Lock the donated item row (also tells us whether the donation is still unexpired)
            cur.execute("""
                SELECT di.quantity, d.expiry_time > LOCALTIMESTAMP
                FROM donation_items di
                JOIN donation d ON d.post_id = di.post_id
                WHERE di.post_id = %s AND di.item_no = %s
                FOR UPDATE OF di
            """, (sel["post_id"], sel["item_no"]))
            item_row = cur.fetchone()
            if not item_row:
                raise ValueError("Donated item no longer exists.")
            item_qty, active = item_row
            if not active:
                raise ValueError("This donation has expired.")

            # Lock the request row
            cur.execute("""
                SELECT quantity, status FROM receiver_request
                WHERE request_id = %s FOR UPDATE
            """, (sel["request_id"],))
            request_row = cur.fetchone()
            if not request_row:
                raise ValueError("Request no longer exists.")
            req_qty, req_status = request_row
            if req_status not in ("Pending", "Partial"):
                raise ValueError("This request is no longer available.")

            cur.execute("""
                SELECT COALESCE(SUM(allocated_quantity), 0) FROM match_allocation
                WHERE post_id = %s AND item_no = %s
                  AND allocation_status IN ('Approved', 'Completed')
            """, (sel["post_id"], sel["item_no"]))
            already_from_item = cur.fetchone()[0]

            cur.execute("""
                SELECT COALESCE(SUM(allocated_quantity), 0) FROM match_allocation
                WHERE request_id = %s
                  AND allocation_status IN ('Approved', 'Completed')
            """, (sel["request_id"],))
            already_for_request = cur.fetchone()[0]

            if qty > item_qty - already_from_item or qty > req_qty - already_for_request:
                raise ValueError("Available quantity changed. Refresh the page and try again.")

            percent = min(100, (already_for_request + qty) / req_qty * 100)
            cur.execute("""
                INSERT INTO match_allocation
                    (match_percent, allocation_status, post_id, item_no, request_id, allocated_quantity)
                VALUES (%s, 'Approved', %s, %s, %s, %s)
                RETURNING match_id
            """, (percent, sel["post_id"], sel["item_no"], sel["request_id"], qty))
            match_id = cur.fetchone()[0]

            new_status = "Fulfilled" if already_for_request + qty >= req_qty else "Partial"
            cur.execute("UPDATE receiver_request SET status = %s WHERE request_id = %s",
                        (new_status, sel["request_id"]))
    return match_id, new_status



SIMILARITY_THRESHOLD = 0.75


def name_similarity(a, b):
    """1.0 exact, 0.9 one name contains the other, else fuzzy ratio."""
    a, b = a.strip().casefold(), b.strip().casefold()
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.9
    return difflib.SequenceMatcher(None, a, b).ratio()


def score_match(similarity, need, available, expiry):
    coverage = min(need, available) / need            # donor can cover more of the need -> better
    hours_left = max((expiry - datetime.now()).total_seconds() / 3600, 0)
    urgency = 1 / (1 + hours_left / 24)               # sooner expiry -> use it first
    return 0.50 * similarity + 0.35 * coverage + 0.15 * urgency


try:
    with get_connected() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT q.request_id, r.receiver_name, q.food_item, q.quantity,
                       COALESCE((SELECT SUM(a.allocated_quantity) FROM match_allocation a
                                 WHERE a.request_id = q.request_id
                                   AND a.allocation_status IN ('Approved', 'Completed')), 0)
                FROM receiver_request q
                JOIN receiver r ON r.receiver_id = q.receiver_id
                WHERE q.status IN ('Pending', 'Partial')
                ORDER BY q.request_date
            """)
            requests = cur.fetchall()

            cur.execute("""
                SELECT d.post_id, dn.donor_name, di.item_no, di.item_name, di.quantity,
                       d.expiry_time,
                       GREATEST(di.quantity - COALESCE((
                           SELECT SUM(a.allocated_quantity) FROM match_allocation a
                           WHERE a.post_id = di.post_id AND a.item_no = di.item_no
                             AND a.allocation_status IN ('Approved', 'Completed')), 0), 0)
                FROM donation d
                JOIN donor dn ON dn.donor_id = d.donor_id
                JOIN donation_items di ON di.post_id = d.post_id
                WHERE d.expiry_time > LOCALTIMESTAMP
            """)
            donations = cur.fetchall()

    candidates = []
    for order, (reqid, rname, food, req_qty, allocated) in enumerate(requests):
        need = req_qty - allocated
        if need <= 0:
            continue
        for post_id, donor_name, item_no, item_name, total_qty, expiry, available in donations:
            if available <= 0:
                continue
            sim = name_similarity(food, item_name)
            if sim < SIMILARITY_THRESHOLD:
                continue
            suggested = min(need, available)
            candidates.append({
                "order": order, "receiver": rname, "request_id": reqid, "food": food,
                "need": need, "post_id": post_id, "donor": donor_name, "item_no": item_no,
                "donated_item": item_name, "available": available, "suggested": suggested,
                "surplus": available - suggested, "expiry": expiry,
                "score": score_match(sim, need, available, expiry),
            })

    # Best score first; ties go to the older request
    candidates.sort(key=lambda m: (-m["score"], m["order"]))

    if not candidates:
        st.info("No compatible requests and available donations found.")
    else:
        st.subheader(f"{len(candidates)} possible match(es), best first")
        st.dataframe(
            pd.DataFrame([{
                "Request": f"#{m['request_id']} {m['receiver']}",
                "Needs": f"{m['food']} x{m['need']}",
                "Donation": f"#{m['post_id']} {m['donor']}",
                "Offers": f"{m['donated_item']} x{m['available']}",
                "Will allocate": m["suggested"],
                "Donor surplus left": m["surplus"],
                "Expires": m["expiry"].strftime("%d %b %H:%M"),
                "Score %": round(m["score"] * 100),
            } for m in candidates]),
            width="stretch", hide_index=True,
        )

        st.subheader("Approve a match")
        labels = [
            f"Request #{m['request_id']} ({m['receiver']}) <- Donation #{m['post_id']} "
            f"({m['donor']}) | {m['suggested']} units | score {round(m['score'] * 100)}%"
            for m in candidates
        ]
        selected = candidates[labels.index(st.selectbox("Choose a match", labels))]

        if selected["surplus"] > 0:
            st.info(f"Donor has {selected['surplus']} more unit(s) than this request needs; "
                    "the surplus stays available for other requests.")

        qty = st.number_input(
            "Quantity to allocate", min_value=1,
            max_value=int(selected["suggested"]),
            value=int(selected["suggested"]), step=1,
        )

        col1, col2 = st.columns(2)
        if col1.button("Approve Allocation", type="primary"):
            try:
                match_id, new_status = approve_allocation(selected, int(qty))
            except Exception as e:
                st.error(f"Allocation failed: {e}")
            else:
                st.session_state["flash"] = (
                    f"Allocation #{match_id} approved: {qty} units. Request status: {new_status}."
                )
                st.rerun()

        if col2.button("Auto-match all (best first)"):
            need_left, avail_left, done, units = {}, {}, 0, 0
            try:
                for m in candidates:
                    n = need_left.setdefault(m["request_id"], m["need"])
                    a = avail_left.setdefault((m["post_id"], m["item_no"]), m["available"])
                    q = min(n, a)
                    if q <= 0:
                        continue
                    approve_allocation(m, q)
                    need_left[m["request_id"]] = n - q
                    avail_left[(m["post_id"], m["item_no"])] = a - q
                    done += 1
                    units += q
            except Exception as e:
                st.error(f"Auto-match stopped after {done} allocation(s): {e}")
            else:
                st.session_state["flash"] = f"Auto-match created {done} allocation(s), {units} units in total."
                st.rerun()
except Exception as e:
    st.error(f"Could not load matching data: {e}")
