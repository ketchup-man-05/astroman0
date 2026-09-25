"""Free database: Google Sheets via a service account. Every function fails soft --
if Sheets is not configured (or the network hiccups) the app keeps working and
returns safe empty values. Nothing here may ever break a reading."""
import uuid
from datetime import datetime, timezone

try:
    import streamlit as st
except ImportError:  # pragma: no cover - lets lib import outside streamlit
    st = None

READINGS_HEADERS = ["reading_id", "username", "created_at_utc", "question", "topic",
                    "city", "horary_number", "verdict", "kp_score", "outcome", "outcome_at"]
USERS_HEADERS = ["username", "name", "pass_hash", "created_at_utc"]
REVIEWS_HEADERS = ["created_at_utc", "name", "rating", "text", "approved", "reading_id"]


def is_configured():
    if st is None:
        return False
    try:
        s = st.secrets
        return ("gcp_service_account" in s and "sheets" in s
                and "spreadsheet_key" in s["sheets"])
    except Exception:
        return False


def _client():
    import gspread
    from google.oauth2.service_account import Credentials
    info = dict(st.secrets["gcp_service_account"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


def _spreadsheet():
    return _client().open_by_key(st.secrets["sheets"]["spreadsheet_key"])


def _ws(tab, headers):
    ss = _spreadsheet()
    try:
        ws = ss.worksheet(tab)
    except Exception:
        ws = ss.add_worksheet(title=tab, rows=1000, cols=len(headers) + 2)
        ws.append_row(headers)
        return ws
    if not ws.get_all_values():
        ws.append_row(headers)
    return ws


def _rows(tab, headers):
    try:
        return _ws(tab, headers).get_all_records()
    except Exception:
        return []


# ---------------- users ----------------
def user_exists(username):
    un = (username or "").strip().lower()
    return any((r.get("username") or "").strip().lower() == un
               for r in _rows("users", USERS_HEADERS))


def get_pass_hash(username):
    un = (username or "").strip().lower()
    for r in _rows("users", USERS_HEADERS):
        if (r.get("username") or "").strip().lower() == un:
            return r.get("pass_hash"), r.get("name")
    return None, None


def create_user(username, name, pass_hash):
    try:
        _ws("users", USERS_HEADERS).append_row([
            username.strip().lower(), name.strip(), pass_hash,
            datetime.now(timezone.utc).isoformat()])
        return True
    except Exception:
        return False


# ---------------- readings & outcomes ----------------
def new_reading_id(horary_number):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{horary_number}_{uuid.uuid4().hex[:6]}"


def log_reading(reading_id, username, question, topic, city, horary_number,
                verdict, kp_score):
    try:
        _ws("readings", READINGS_HEADERS).append_row([
            reading_id, username or "anon",
            datetime.now(timezone.utc).isoformat(), question, topic, city,
            horary_number, (verdict or "")[:80], kp_score, "", ""])
        return True
    except Exception:
        return False


def set_outcome(reading_id, outcome):
    """outcome: YES / NO / PARTIAL"""
    try:
        ws = _ws("readings", READINGS_HEADERS)
        cell = ws.find(reading_id)
        # outcome is column 10, outcome_at column 11 (1-indexed)
        ws.update_cell(cell.row, 10, outcome)
        ws.update_cell(cell.row, 11, datetime.now(timezone.utc).isoformat())
        return True
    except Exception:
        return False


def get_user_readings(username, limit=50):
    rows = [r for r in _rows("readings", READINGS_HEADERS)
            if (r.get("username") or "") == username]
    rows.sort(key=lambda r: r.get("created_at_utc") or "", reverse=True)
    return rows[:limit]


def pending_outcomes(username):
    return [r for r in get_user_readings(username, limit=200) if not r.get("outcome")]


# ---------------- reviews ----------------
def add_review(name, rating, text, reading_id=""):
    try:
        _ws("reviews", REVIEWS_HEADERS).append_row([
            datetime.now(timezone.utc).isoformat(), name.strip(), int(rating),
            text.strip(), "FALSE", reading_id])
        return True
    except Exception:
        return False


def get_reviews(limit=30):
    rows = [r for r in _rows("reviews", REVIEWS_HEADERS)
            if str(r.get("approved")).strip().upper() == "TRUE"]
    rows.sort(key=lambda r: r.get("created_at_utc") or "", reverse=True)
    return rows[:limit]
