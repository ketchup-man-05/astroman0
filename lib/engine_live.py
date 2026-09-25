"""Organ 1 - the live engine bridge.

Connects the website to your real KP engine (chart_caster.py at the repo root).
One function in, one reading dict out. If the engine files are missing or a
city can't be resolved, it returns an error string instead of raising - the
page shows a friendly message, never a crash.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from . import topics  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))


def ist_now():
    return datetime.now(timezone.utc).astimezone(IST)


def cosmic_weather():
    """Returns (tithi, weekday, date_str) for the top banner, or (None, None, None)."""
    try:
        import chart_caster
        import ephemeris_utils as eu
        now_utc = datetime.now(timezone.utc)
        pl, _ = eu.planets_at(eu.to_jd(now_utc))
        tithi = chart_caster.get_panchang_tithi(pl["Sun"], pl["Moon"])
        ist = ist_now()
        return tithi, ist.strftime("%A"), ist.strftime("%-d %B %Y")
    except Exception:
        return None, None, None


def cast(question, city, horary_number, topic_label):
    """Cast a real KP horary chart.

    Returns (reading_dict, None) on success, (None, error_message) on failure.
    reading_dict keys: result, question, city, number, topic, topic_label, cast_at.
    """
    topic_key = topics.TOPIC_OPTIONS.get(topic_label)
    houses = topics.get_query_houses(question, topic_key)
    try:
        import chart_caster
    except ImportError:
        return None, ("The KP engine files (chart_caster.py etc.) are not in the app folder yet. "
                      "Paste them at the repo root next to app.py.")
    try:
        result = chart_caster.execute_kp_reading(
            city.strip(), int(horary_number),
            houses["positive_houses"], houses["negative_houses"], houses["key_house"],
            log=False)
    except Exception as e:
        return None, (f"The chart could not be cast ({type(e).__name__}). "
                       "Try a nearby major city like Delhi or Mumbai.")
    if not result or "error" in result:
        return None, ("The chart could not be cast for that city. "
                       "Try a nearby major city (e.g. Delhi, Mumbai).")
    return {
        "result": result,
        "question": question.strip(),
        "city": city.strip(),
        "number": int(horary_number),
        "topic": houses.get("topic", "general"),
        "topic_label": topic_label,
        "cast_at": ist_now().strftime("%-d %b %Y, %-I:%M %p IST"),
    }, None
