"""Tiny auth: bcrypt-hashed passwords in the Google Sheets `users` tab.
Session lives in st.session_state. Adequate for a free-readings app; not
bank-grade, and it never claims to be."""
import streamlit as st
import bcrypt
from . import sheets


def _init():
    st.session_state.setdefault("user", None)  # {"username":..., "name":...}


def current_user():
    _init()
    return st.session_state["user"]


def logout():
    st.session_state["user"] = None


def _hash(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _check(pw, hashed):
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def login_box():
    """Renders login/signup UI. Returns the user dict or None."""
    _init()
    if not sheets.is_configured():
        st.info("Login is unavailable right now (database not connected yet) - "
                "you can still get a free reading below.")
        return None
    user = st.session_state["user"]
    if user:
        return user
    tab_login, tab_signup = st.tabs(["Login", "Sign up"])
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")
            go = st.form_submit_button("Login")
        if go:
            if not username or not password:
                st.warning("Enter both username and password.")
            else:
                hashed, name = sheets.get_pass_hash(username)
                if hashed and _check(password, hashed):
                    st.session_state["user"] = {"username": username, "name": name or username}
                    st.success(f"Welcome back, {name or username}!")
                    st.rerun()
                else:
                    st.error("Wrong username or password.")
    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Your name").strip()
            username = st.text_input("Choose a username").strip().lower()
            pw1 = st.text_input("Choose a password", type="password")
            pw2 = st.text_input("Repeat the password", type="password")
            go = st.form_submit_button("Create account")
        if go:
            if not name or not username or not pw1:
                st.warning("Please fill all fields.")
            elif pw1 != pw2:
                st.error("Passwords don't match.")
            elif len(pw1) < 6:
                st.error("Password must be at least 6 characters.")
            elif sheets.user_exists(username):
                st.error("That username is taken - try another.")
            else:
                if sheets.create_user(username, name, _hash(pw1)):
                    st.session_state["user"] = {"username": username, "name": name}
                    st.success("Account created - your readings will now be saved!")
                    st.rerun()
                else:
                    st.error("Could not create the account. Try again in a bit.")
    return st.session_state["user"]


def user_badge():
    """Small badge with logout."""
    user = current_user()
    if user:
        st.write(f"Signed in as **{user['name']}**")
        if st.button("Logout", key="logout_btn"):
            logout()
            st.rerun()
