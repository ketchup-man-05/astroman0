"""Template narrator: turns engine facts into warm plain-language prose with
ZERO AI API calls. Deterministic, free forever. No emojis - the UI layer
adds icons."""

def _family(verdict):
    v = (verdict or "").upper()
    if v.startswith("DEFINITIVE YES"): return "def_yes"
    if v.startswith("YES WITH DELAYS"): return "yes_delays"
    if v.startswith("DELAYED"): return "delayed"
    if v.startswith("MIXED"): return "mixed"
    if v.startswith("DEFINITIVE NO"): return "def_no"
    if v.startswith("UNFAVORABLE"): return "no"
    return "mixed"

_VERDICT_HEADLINE = {
    "def_yes": "YES - the stars are strongly with you",
    "yes_delays": "YES - but with some delays on the way",
    "delayed": "NOT DENIED - delayed, not refused",
    "mixed": "MIXED - the chart shows a real tug-of-war",
    "no": "NO - the current moment does not favour this",
    "def_no": "NO - the chart is firmly against this right now",
}

_VERDICT_STORY = {
    "def_yes": ("The deciding planet of your question is powerfully connected to the houses "
                "of fulfilment. In KP terms, the significations line up clearly in your favour - "
                "this is one of the strongest answers the chart can give."),
    "yes_delays": ("The answer leans YES, but the chart also shows friction - a slow planet, a "
                   "retrograde influence, or a competing house. Expect the result, but give it "
                   "time and don't panic at the first obstacle."),
    "delayed": ("A retrograde planet is touching your question. In KP this never means a flat "
                "refusal - it means the matter is slowed, postponed, or needs a second attempt. "
                "The door is not closed; it is just opening slowly."),
    "mixed": ("Your chart shows genuinely conflicting pulls - some strong positive links and "
              "some real blocks. This usually means the outcome depends on timing or on a "
              "condition changing. Read the timing section below carefully."),
    "no": ("Right now the deciding planet is tied more strongly to the houses of denial than "
           "to the houses of fulfilment. A NO today is not a NO forever - horary answers the "
           "moment, and moments change."),
    "def_no": ("The chart is unusually one-sided here: the deciding planet's links to the "
               "houses of denial clearly outweigh everything else. It is better to conserve "
               "your energy for a better moment than to push against this one."),
}

_SCORE_BANDS = [
    (6, 8, "Very strong - rare, clear cosmic support."),
    (3, 5, "Positive - the balance of forces is with you."),
    (1, 2, "Mildly positive - leaning yes, but thin."),
    (0, 0, "Perfectly balanced - the chart refuses to take sides."),
    (-2, -1, "Mildly negative - leaning no, but not heavy."),
    (-5, -3, "Negative - the blocks outweigh the support."),
    (-8, -6, "Very strong negative - rare, heavy resistance."),
]


def score_band_text(kp_score):
    try:
        s = int(kp_score)
    except (TypeError, ValueError):
        return "The score could not be computed for this chart."
    for lo, hi, text in _SCORE_BANDS:
        if lo <= s <= hi:
            return f"Score {s:+d} (scale -8 to +8): {text}"
    return f"Score {s:+d} (scale -8 to +8)."


def score_legend_md():
    return ("**How to read the KP score:** the engine checks 4 mathematical steps - the star lord's "
            "occupation, the deciding planet's occupation, and each one's ownership - and adds them up. "
            "+8 is the maximum possible YES, -8 the maximum NO, 0 is perfectly balanced. "
            "Most real charts land between -5 and +5.")


def verdict_story(verdict, kp_score, decision=None):
    """Returns (headline, story_paragraph, extra_notes_list)."""
    fam = _family(verdict)
    notes = []
    d = decision or {}
    if d.get("deciding_planet_is_retrograde") and fam not in ("delayed",):
        who = d.get("retrograde_who") or "a key planet"
        notes.append(f"Timing note: {who} is retrograde right now, so even a favourable answer may arrive late.")
    rp = d.get("ruling_planet_support")
    if rp is False:
        notes.append("Ruling planets: the planets of this moment don't fully confirm the deciding planet - "
                     "treat the YES as hopeful rather than certain.")
    elif rp is True:
        notes.append("Ruling planets: the planets of this moment confirm the deciding planet - "
                     "a good sign the chart is readable.")
    return _VERDICT_HEADLINE[fam], _VERDICT_STORY[fam], notes


def timing_story(timing):
    """Plain-language timing paragraph, or None."""
    if not timing or timing.get("error"):
        return None
    bits = []
    active = timing.get("active") or {}
    if active:
        bits.append(f"Right now you are in {active.get('maha')} Mahadasha / {active.get('bhukti')} Bhukti "
                    f"({active.get('start')} to {active.get('end')}).")
    nxt = timing.get("next_supportive") or {}
    if nxt:
        bits.append(f"The next supportive window opens with {nxt.get('maha')} / {nxt.get('bhukti')}, "
                    f"{nxt.get('start')} to {nxt.get('end')}.")
        antara = timing.get("next_supportive_antara") or {}
        if antara:
            bits.append(f"Inside it, the finest window is the {antara.get('antara')} antara "
                        f"({antara.get('start')} to {antara.get('end')}).")
    elif active:
        bits.append("No strongly supportive period is visible in the computed range - patience is the strategy.")
    if timing.get("ruling_planet_filter_applied"):
        bits.append("These windows are filtered by the ruling planets, so only the genuinely fruitful periods are shown.")
    return " ".join(bits)


def transit_story(transit):
    if not transit or transit.get("error"):
        return None
    c = (transit.get("classification") or "").lower()
    if c == "supportive":
        return "The current planetary transits (gochar) support this chart - the sky agrees."
    if c == "mixed":
        return "Transits are mixed - some support, some resistance. Timing matters more than usual."
    if "not" in c:
        return "Current transits don't strongly support this chart - lean on the dasha timing above."
    return None


def share_text(question, verdict, kp_score, app_url):
    return (f"I asked Astroman AI: \"{question}\"\n"
            f"Answer: {verdict.split('.')[0]} (KP score {kp_score:+d})\n"
            f"Try your own free KP horary reading: {app_url}")


def outcome_prompt():
    return ("**Did it come true?** When you know the real outcome of your question, "
            "tap below. Your answer calibrates the engine and helps every future reading - "
            "and with your permission, becomes a testimonial.")
