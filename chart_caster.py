import swisseph as swe
from datetime import datetime, timezone, timedelta
import re
import kp_math
import location_engine
import transit_engine

# --- CORE SETTINGS ---
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

ZODIAC_SIGNS = kp_math.ZODIAC_SIGNS
SIGN_LORDS = kp_math.SIGN_LORDS
NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] * 3

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"] * 2
TITHIS[-1] = "Amavasya"

NODES = ["Rahu", "Ketu"]

def get_sign_lord(degree):
    return kp_math.get_sign_lord(degree)

def get_star_lord(degree):
    return kp_math.get_star_lord(degree)

def get_true_agent(planet, planets_dict):
    if planet not in NODES: return planet
    node_lon = planets_dict.get(planet, 0)
    nearest, nearest_dist = None, None
    for p_name, p_lon in planets_dict.items():
        if p_name not in NODES:
            dist = abs(node_lon - p_lon)
            if dist > 180: dist = 360 - dist
            if dist <= 3.33 and (nearest_dist is None or dist < nearest_dist):
                nearest, nearest_dist = p_name, dist
    if nearest is not None: return nearest  # closest planet within 3.33 deg wins
    return get_sign_lord(node_lon)

def get_sign_index(degree):
    return int((degree % 360) // 30)

def get_houses_owned_by_planet(planet, ownership, planets_dict):
    """
    House ownership = the houses whose CUSP falls in a sign ruled by the planet.
    `ownership` is the {planet: [houses]} map from kp_math.build_house_ownership().
    Rahu/Ketu are resolved to their true agent first.
    """
    agent = get_true_agent(planet, planets_dict)
    return list(ownership.get(agent, []))

def calculate_placidus_cusps(target_ascendant, lat, lon):
    """
    Finds the moment (within today's 24h UT window) whose Ascendant equals
    target_ascendant, then returns the 12 Placidus cusps for that moment.

    Uses bisection instead of a brute-force minute/second scan: the real
    Ascendant is monotonically increasing in time (it never runs backward),
    so a coarse scan just needs to find which bracket the target falls in,
    then bisection narrows it to sub-second precision in ~10-15 more calls.
    """
    now = datetime.now(timezone.utc)
    base_jd = swe.julday(now.year, now.month, now.day, 0.0)

    def signed_diff(jd):
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        # signed difference in [-180, 180), positive = ascendant is ahead of target
        d = (ascmc[0] - target_ascendant + 180) % 360 - 180
        return d, cusps, ascmc

    n_coarse = 96  # 15-minute steps across the day
    step = 1.0 / n_coarse

    prev_jd = base_jd
    prev_diff, _, _ = signed_diff(prev_jd)
    lo, hi = None, None

    for i in range(1, n_coarse + 1):
        jd = base_jd + i * step
        diff, _, _ = signed_diff(jd)
        crossed = (prev_diff <= 0 <= diff) or (prev_diff >= 0 >= diff)
        # ignore the 360->0 wrap itself, which also looks like a sign flip
        if crossed and abs(diff - prev_diff) < 180:
            lo, hi = prev_jd, jd
            break
        prev_jd, prev_diff = jd, diff

    if lo is None:
        lo, hi = base_jd, base_jd + 1.0

    lo_diff, _, _ = signed_diff(lo)
    mid = lo
    for _ in range(30):
        mid = (lo + hi) / 2.0
        mid_diff, cusps, ascmc = signed_diff(mid)
        if (mid_diff > 0) == (lo_diff > 0):
            lo, lo_diff = mid, mid_diff
        else:
            hi = mid
        if (hi - lo) < (0.5 / 86400.0):  # sub-second precision reached
            break

    final_cusps, _ = swe.houses_ex(mid, lat, lon, b'P', swe.FLG_SIDEREAL)
    # pyswisseph returns 12 cusps (index 0 = house 1); guard in case a 13-item tuple appears
    return list(final_cusps)[-12:]

def get_panchang_tithi(sun_lon, moon_lon):
    diff = (moon_lon - sun_lon) % 360
    tithi_index = int(diff / 12)
    paksha = "Shukla (Waxing)" if tithi_index < 15 else "Krishna (Waning)"
    return f"{paksha} {TITHIS[tithi_index]}"

def get_current_day_lord(lon):
    offset_hours = lon / 15.0
    local_time = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
    sun_index = (local_time.weekday() + 1) % 7
    if local_time.hour < 6: sun_index = (sun_index - 1) % 7
    return DAYS[sun_index], DAY_LORDS[sun_index]

def get_live_ascendant(lat, lon):
    now = datetime.now(timezone.utc)
    jd_ut = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0 + now.second/3600.0)
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
    return ascmc[0]

# --- PRE-CALCULATED FACT BUILDERS (all math lives here, never in the LLM) ---

def build_planet_facts(planets, retrogrades, cusps, ownership):
    """Explicit per-planet fact records + a ready-to-read summary string."""
    facts = []
    for name, lon_val in planets.items():
        d = kp_math.get_kp_dignities(lon_val)
        house = kp_math.get_house_from_cusps(lon_val, cusps)
        retro = bool(retrogrades.get(name, False))

        if name in NODES:
            agent = get_true_agent(name, planets)
            owned = list(ownership.get(agent, []))
            owns_text = (
                f"no cusps of its own; acts as agent of {agent}, "
                f"which owns {kp_math.format_house_list(owned)}"
            )
        else:
            agent = name
            owned = list(ownership.get(name, []))
            owns_text = kp_math.format_house_list(owned)

        facts.append({
            "planet": name,
            "sign": d["sign"],
            "degree_in_sign": kp_math.format_degree_in_sign(lon_val),
            "sign_lord": d["sign_lord"],
            "star_lord": d["star_lord"],
            "sub_lord": d["sub_lord"],
            "house_occupied": house,
            "acts_as_agent_of": agent,
            "owns_houses": owned,
            "is_retrograde": retro,
            "summary": (
                f"Planet: {name}, Sign: {d['sign']} ({kp_math.format_degree_in_sign(lon_val)}), "
                f"Occupies: {kp_math.ordinal(house)} House, Owns: {owns_text}"
                f"{', Retrograde: Yes' if retro else ''}"
            ),
        })
    return facts

def _classify(house, positive_set, negative_set):
    if house in positive_set: return "positive"
    if house in negative_set: return "negative"
    return "neutral"

def compute_step_breakdown(star_lord, sub_lord, planet_houses, ownership, planets, positive_set, negative_set):
    """
    KP signification of the DECIDING planet = the sub lord of the key house's cusp
    (`sub_lord`), read through the star it sits in (`star_lord`). Steps follow the classical
    KP order of strength, and the weights are +-4 / +-3 / +-2 / +-1:

      1. houses occupied by its Star Lord        (weight 4)
      2. house occupied by the planet itself     (weight 3)
      3. houses owned by its Star Lord           (weight 2)
      4. houses owned by the planet itself       (weight 1)

    Ownership steps (3 and 4) are CAPPED: the weight counts once for "any owned house is
    positive" and once for "any owned house is negative", never once per house. If both are
    present the step is flagged mixed/volatile instead of looking neutral.
    If the planet sits in its own star (star_lord == sub_lord), steps 2 and 4 would only repeat
    steps 1 and 3, so they are not counted a second time.
    """
    weights = {"positive": 1, "negative": -1, "neutral": 0}

    def occupation_step(step_no, label, planet, weight):
        house = planet_houses.get(planet, 0)
        cls = _classify(house, positive_set, negative_set)
        pts = weights[cls] * weight
        return {
            "step": step_no, "name": label, "planet": planet,
            "houses": [house], "weight": weight,
            "house_results": [{"house": house, "classification": cls, "points": pts}],
            "mixed": False, "skipped": False,
            "step_points": pts,
            "text": f"Step {step_no} ({label}): {planet} occupies the {kp_math.ordinal(house)} House -> {cls} -> {pts:+d}",
        }

    def ownership_step(step_no, label, planet, weight):
        owned = get_houses_owned_by_planet(planet, ownership, planets)
        results = [{"house": h, "classification": _classify(h, positive_set, negative_set)} for h in owned]
        has_pos = any(r["classification"] == "positive" for r in results)
        has_neg = any(r["classification"] == "negative" for r in results)
        mixed = has_pos and has_neg
        total = (weight if has_pos else 0) - (weight if has_neg else 0)
        if owned:
            detail = "; ".join(f"{kp_math.ordinal(r['house'])} House -> {r['classification']}" for r in results)
            if mixed:
                outcome = f"MIXED/VOLATILE (positive {weight:+d} and negative {-weight:+d}) = {total:+d}"
            elif has_pos:
                outcome = f"positive, counted once (not stacked) = {total:+d}"
            elif has_neg:
                outcome = f"negative, counted once (not stacked) = {total:+d}"
            else:
                outcome = "neutral = +0"
            text = f"Step {step_no} ({label}): {planet} owns {kp_math.format_house_list(owned)}: {detail} => {outcome}"
        else:
            text = f"Step {step_no} ({label}): {planet} owns no house cusps = 0"
        return {
            "step": step_no, "name": label, "planet": planet,
            "houses": owned, "weight": weight,
            "house_results": results, "mixed": mixed, "skipped": False,
            "step_points": total, "text": text,
        }

    def repeated_step(step_no, label, planet, weight, same_as):
        return {
            "step": step_no, "name": label, "planet": planet,
            "houses": [], "weight": weight,
            "house_results": [], "mixed": False, "skipped": True,
            "step_points": 0,
            "text": f"Step {step_no} ({label}): {planet} sits in its own star, so this repeats Step {same_as} and is not counted again = 0",
        }

    own_star = (star_lord == sub_lord)
    steps = [
        occupation_step(1, "Star Lord Occupation", star_lord, 4),
        repeated_step(2, "Cusp Sub Lord Occupation", sub_lord, 3, 1) if own_star
            else occupation_step(2, "Cusp Sub Lord Occupation", sub_lord, 3),
        ownership_step(3, "Star Lord Ownership", star_lord, 2),
        repeated_step(4, "Cusp Sub Lord Ownership", sub_lord, 1, 3) if own_star
            else ownership_step(4, "Cusp Sub Lord Ownership", sub_lord, 1),
    ]
    return steps, sum(s["step_points"] for s in steps)

def decide_verdict(score, steps, is_retrograde, deciding_planet):
    """
    Turns the score into a verdict.
      * Definitive thresholds are +-6.
      * With the step weights (4/3/2/1) a score of +-6 or more can only happen when the two
        occupation steps (the strongest KP levels) agree with it, so no extra guard is needed.
      * A retrograde deciding planet means delay/obstruction: it can never be DEFINITIVE YES.
    """
    classes = [r["classification"] for st in steps for r in st["house_results"]]
    has_pos, has_neg = "positive" in classes, "negative" in classes
    retro_note = (f" The deciding planet ({deciding_planet}) is retrograde, so expect delay or obstruction."
                  if is_retrograde else "")

    if score >= 6:
        if is_retrograde:
            return (f"YES WITH DELAYS. Positives dominate (Score: +{score}) but the deciding planet "
                    f"({deciding_planet}) is retrograde, so the result cannot be called definitive. "
                    f"Expect success only after delay or obstacles.")
        return f"DEFINITIVE YES. Strong positive dominance (Score: +{score}). Success is highly likely."
    if 1 <= score <= 5:
        return (f"YES WITH DELAYS. Positives slightly outweigh negatives (Score: +{score}). "
                f"Expect success but with obstacles." + retro_note)
    if score == 0:
        if has_pos and has_neg:
            return ("MIXED / CONFLICTING. Supporting and opposing influences cancel out (Score: 0). "
                    "The outcome is uncertain and may swing either way." + retro_note)
        return ("MIXED / UNCLEAR. The chart shows no strong link to the houses of this question (Score: 0). "
                "The outcome cannot be judged from this chart." + retro_note)
    if -5 <= score <= -1:
        return f"UNFAVORABLE / NO. Negatives overpower positives or lack strong support (Score: {score})."
    return f"DEFINITIVE NO. Strong negative dominance (Score: {score}). The chart denies the event."

# --- THE MASTER PIPELINE ---
def execute_kp_reading(city, horary_number, positive_houses, negative_houses, key_house=None):
    def _parse_houses(h_input):
        if not h_input: return set()
        if isinstance(h_input, list): return set(int(str(x).strip()) for x in h_input if str(x).strip().isdigit())
        if isinstance(h_input, str): return set(int(x) for x in re.findall(r'\d+', h_input))
        if isinstance(h_input, dict):
            vals = []
            for v in h_input.values():
                if isinstance(v, list): vals.extend(v)
                elif isinstance(v, str): vals.extend(re.findall(r'\d+', v))
            return set(int(x) for x in vals if str(x).isdigit())
        return set()

    positive_set = _parse_houses(positive_houses)
    negative_set = _parse_houses(negative_houses)

    # The "key house": the cusp whose SUB LORD decides this kind of question (default 11 = fulfilment of desire)
    try:
        key_house = int(key_house)
    except (TypeError, ValueError):
        key_house = 11
    if not 1 <= key_house <= 12:
        key_house = 11

    lat, lon = location_engine.get_coordinates(city)
    if lat is None or lon is None: return {"error": "Location not found or GPS block active."}
    
    asc_data = kp_math.get_horary_chart(horary_number)
    if "error" in asc_data: return asc_data
    target_asc = asc_data["ascendant_longitude"]
    horary_asc_lord = asc_data["sign_lord"]
    horary_sign = asc_data["sign"]
    horary_sub_lord = asc_data["sub_lord"]
    horary_star_lord = asc_data["star_lord"]  # the fixed Nakshatra lord from the 1-249 table
    
    # --- 1. Cusps, and the sign on every cusp ---
    cusps = calculate_placidus_cusps(target_asc, lat, lon)
    cusp_facts = kp_math.build_cusp_facts(cusps)

    # --- 2. House ownership: cusp sign -> ruling planet ---
    ownership = kp_math.build_house_ownership(cusp_facts)

    # --- 3. Planets: sign (degree // 30), house from cusp boundaries ---
    planets, retrogrades = transit_engine.get_live_planets()
    planet_houses = {p: kp_math.get_house_from_cusps(lon_val, cusps) for p, lon_val in planets.items()}
    planet_facts = build_planet_facts(planets, retrogrades, cusps, ownership)

    # --- 4. The deciding planet: SUB LORD of the key house's cusp, read through the star it sits in ---
    key_cusp = cusp_facts[key_house - 1]
    cusp_sub_lord = key_cusp["sub_lord"]
    deciding_planet = get_true_agent(cusp_sub_lord, planets)              # Rahu/Ketu act through their agent
    deciding_star_raw = kp_math.get_star_lord(planets[deciding_planet])   # the star the PLANET sits in (not the cusp's star)
    deciding_star = get_true_agent(deciding_star_raw, planets)
    is_retrograde = bool(retrogrades.get(deciding_planet, False))

    live_asc = get_live_ascendant(lat, lon)
    rp_asc_sign_lord = get_sign_lord(live_asc)
    rp_asc_star_lord = get_star_lord(live_asc)
    
    moon_lon = planets["Moon"]
    day_name, day_lord = get_current_day_lord(lon)
    current_tithi = get_panchang_tithi(planets["Sun"], moon_lon)
    
    saturn_lon = planets["Saturn"]
    dist = abs(moon_lon - saturn_lon)
    if dist > 180: dist = 360 - dist
    punarphoo_active = dist <= 3.33 

    # Ruling-planet confirmation (informational only - it does not change the score)
    rp_names = {rp_asc_sign_lord, rp_asc_star_lord, get_sign_lord(moon_lon), get_star_lord(moon_lon), day_lord}
    sub_in_rp = cusp_sub_lord in rp_names or deciding_planet in rp_names
    star_in_rp = deciding_star_raw in rp_names or deciding_star in rp_names
    rp_text = (f"Ruling planet check (confirmation only, not scored): Cusp Sub Lord {deciding_planet} is "
               f"{'' if sub_in_rp else 'not '}among the ruling planets; its Star Lord {deciding_star} is "
               f"{'' if star_in_rp else 'not '}among the ruling planets.")

    # --- 5. Scoring and verdict, fully in Python ---
    step_breakdown, score = compute_step_breakdown(
        deciding_star, deciding_planet, planet_houses, ownership, planets, positive_set, negative_set
    )
    verdict = decide_verdict(score, step_breakdown, is_retrograde, deciding_planet)

    step_1_house = planet_houses.get(deciding_star, 0)
    step_2_house = planet_houses.get(deciding_planet, 0)
    step_3_houses = get_houses_owned_by_planet(deciding_star, ownership, planets)
    step_4_houses = get_houses_owned_by_planet(deciding_planet, ownership, planets)
    all_signified_houses = [step_1_house, step_2_house] + step_3_houses + step_4_houses

    house_ownership_text = {
        p: f"{p} owns {kp_math.format_house_list(hs)}" for p, hs in ownership.items()
    }

    decision = {
        "key_house": key_house,
        "key_house_cusp": key_cusp["summary"],
        "cusp_sub_lord": cusp_sub_lord,
        "deciding_planet": deciding_planet,
        "deciding_planet_star_lord": deciding_star,
        "deciding_planet_is_retrograde": is_retrograde,
        "note": (f"{cusp_sub_lord} is a node and acts through its agent {deciding_planet}. " if cusp_sub_lord != deciding_planet else "")
                + (f"{deciding_planet} sits in its own star, so its occupation and ownership are counted once."
                   if deciding_star == deciding_planet else ""),
    }

    # Text-only payload for the LLM: no raw longitudes, nothing left to calculate.
    ai_facts = {
        "verdict": verdict,
        "kp_score": score,
        "is_retrograde": is_retrograde,
        "punarphoo": punarphoo_active,
        "horary": {
            "number": horary_number,
            "ascendant_sign": horary_sign,
            "ascendant_sign_lord": horary_asc_lord,
            "ascendant_star_lord": horary_star_lord,
            "ascendant_sub_lord": horary_sub_lord,
        },
        "decision": decision,
        "ruling_planet_check": {
            "cusp_sub_lord_in_ruling_planets": sub_in_rp,
            "star_lord_in_ruling_planets": star_in_rp,
            "text": rp_text,
        },
        "target_positive_houses": sorted(positive_set),
        "target_negative_houses": sorted(negative_set),
        "step_breakdown": step_breakdown,
        "house_cusps": [f["summary"] for f in cusp_facts],
        "house_ownership": house_ownership_text,
        "planets": [f["summary"] for f in planet_facts],
        "panchang": {"day_name": day_name, "tithi": current_tithi},
        "ruling_planets": {
            "asc_sign_lord": rp_asc_sign_lord,
            "asc_star_lord": rp_asc_star_lord,
            "moon_sign_lord": get_sign_lord(moon_lon),
            "moon_star_lord": get_star_lord(moon_lon),
            "day_lord": day_lord,
        },
    }
        
    return {
        "verdict": verdict, "kp_score": score, "horary_number": horary_number, "horary_sign": horary_sign,
        "horary_ascendant_longitude": target_asc, "horary_asc_lord": horary_asc_lord,
        "sub_lord": horary_sub_lord, "star_lord": horary_star_lord, "is_retrograde": is_retrograde,
        "all_houses": list(set(all_signified_houses)), "moon_star_lord": get_star_lord(moon_lon),
        "punarphoo": punarphoo_active,
        "key_house": key_house, "cusp_sub_lord": cusp_sub_lord, "deciding_planet": deciding_planet,
        "horary_chart": {
            "number": horary_number,
            "sign": horary_sign,
            "ascendant_longitude": target_asc,
            "sign_lord": horary_asc_lord,
            "star_lord": horary_star_lord,
            "sub_lord": horary_sub_lord
        },
        "significators": {
            "true_star_lord": deciding_star,
            "true_sub_lord": deciding_planet,
            "step_1_house": step_1_house,
            "step_2_house": step_2_house,
            "step_3_houses": step_3_houses,
            "step_4_houses": step_4_houses
        },
        "step_breakdown": step_breakdown,
        "cusp_facts": cusp_facts,
        "planet_facts": planet_facts,
        "house_ownership": ownership,
        "panchang": {"day_name": day_name, "tithi": current_tithi},
        "ruling_planets": {"asc_sign_lord": rp_asc_sign_lord, "asc_star_lord": rp_asc_star_lord, "moon_sign_lord": get_sign_lord(moon_lon), "moon_star_lord": get_star_lord(moon_lon), "day_lord": day_lord},
        "chart_data": {"cusps": list(cusps), "planets": planets, "planet_houses": planet_houses},
        "ai_facts": ai_facts,
    }