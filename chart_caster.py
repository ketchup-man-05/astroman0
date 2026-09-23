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
    for p_name, p_lon in planets_dict.items():
        if p_name not in NODES:
            dist = abs(node_lon - p_lon)
            if dist > 180: dist = 360 - dist
            if dist <= 3.33: return p_name 
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

def compute_step_breakdown(true_star, true_sub, planet_houses, ownership, planets, positive_set, negative_set):
    """
    The four KP steps, scored entirely in Python.
    Step weights: 1 = ±4, 2 = ±3 (per owned house), 3 = ±2, 4 = ±1 (per owned house).
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
            "step_points": pts,
            "text": f"Step {step_no} ({label}): {planet} occupies the {kp_math.ordinal(house)} House -> {cls} -> {pts:+d}",
        }

    def ownership_step(step_no, label, planet, weight):
        owned = get_houses_owned_by_planet(planet, ownership, planets)
        results = []
        for h in owned:
            cls = _classify(h, positive_set, negative_set)
            results.append({"house": h, "classification": cls, "points": weights[cls] * weight})
        total = sum(r["points"] for r in results)
        if owned:
            detail = "; ".join(
                f"{kp_math.ordinal(r['house'])} House -> {r['classification']} ({r['points']:+d})" for r in results
            )
            text = f"Step {step_no} ({label}): {planet} owns {kp_math.format_house_list(owned)}: {detail} = {total:+d}"
        else:
            text = f"Step {step_no} ({label}): {planet} owns no house cusps = 0"
        return {
            "step": step_no, "name": label, "planet": planet,
            "houses": owned, "weight": weight,
            "house_results": results, "step_points": total, "text": text,
        }

    steps = [
        occupation_step(1, "Star Lord Occupation", true_star, 4),
        ownership_step(2, "Star Lord Ownership", true_star, 3),
        occupation_step(3, "Sub Lord Occupation", true_sub, 2),
        ownership_step(4, "Sub Lord Ownership", true_sub, 1),
    ]
    return steps, sum(s["step_points"] for s in steps)

# --- THE MASTER PIPELINE ---
def execute_kp_reading(city, horary_number, positive_houses, negative_houses):
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

    lat, lon = location_engine.get_coordinates(city)
    if not lat: return {"error": "Location not found or GPS block active."}
    
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

    true_sl_star_lord = get_true_agent(horary_star_lord, planets)
    true_sub_lord = get_true_agent(horary_sub_lord, planets)
    is_retrograde = bool(retrogrades.get(true_sl_star_lord, False))
    
    # --- 4. Scoring, fully in Python ---
    step_breakdown, score = compute_step_breakdown(
        true_sl_star_lord, true_sub_lord, planet_houses, ownership, planets, positive_set, negative_set
    )

    step_1_house = planet_houses.get(true_sl_star_lord, 0)
    step_2_houses = get_houses_owned_by_planet(true_sl_star_lord, ownership, planets)
    step_3_house = planet_houses.get(true_sub_lord, 0)
    step_4_houses = get_houses_owned_by_planet(true_sub_lord, ownership, planets)
    all_signified_houses = [step_1_house] + step_2_houses + [step_3_house] + step_4_houses
    
    if is_retrograde:
        verdict = "DENIED. The Star Lord is Retrograde (Vakri). The event will fail or be heavily delayed."
    elif score >= 5:
        verdict = f"DEFINITIVE YES. Strong positive dominance (Score: +{score}). Success is highly likely."
    elif 1 <= score <= 4:
        verdict = f"YES WITH DELAYS. Positives slightly outweigh negatives (Score: +{score}). Expect success but with obstacles."
    elif -4 <= score <= 0:
        verdict = f"UNFAVORABLE / NO. Negatives overpower positives or lack strong support (Score: {score})."
    else:
        verdict = f"DEFINITIVE NO. Strong negative dominance (Score: {score}). The chart denies the event."

    house_ownership_text = {
        p: f"{p} owns {kp_math.format_house_list(hs)}" for p, hs in ownership.items()
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
            "star_lord": horary_star_lord,
            "sub_lord": horary_sub_lord,
            "true_star_lord_agent": true_sl_star_lord,
            "true_sub_lord_agent": true_sub_lord,
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
        "horary_chart": {
            "number": horary_number,
            "sign": horary_sign,
            "ascendant_longitude": target_asc,
            "sign_lord": horary_asc_lord,
            "star_lord": horary_star_lord,
            "sub_lord": horary_sub_lord
        },
        "significators": {
            "true_star_lord": true_sl_star_lord,
            "true_sub_lord": true_sub_lord,
            "step_1_house": step_1_house,
            "step_2_houses": step_2_houses,
            "step_3_house": step_3_house,
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