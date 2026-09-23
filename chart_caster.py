import swisseph as swe
from datetime import datetime, timezone, timedelta
import re
import kp_math
import location_engine
import transit_engine

# --- CORE SETTINGS ---
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] * 3

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"] * 2
TITHIS[-1] = "Amavasya"

def get_sign_lord(degree):
    return SIGN_LORDS[int(degree // 30)]

def get_star_lord(degree):
    nak_index = min(int(degree / (13 + 1/3)), 26)
    return NAKSHATRA_LORDS[nak_index]

def get_true_agent(planet, planets_dict):
    if planet not in ["Rahu", "Ketu"]: return planet
    node_lon = planets_dict.get(planet, 0)
    for p_name, p_lon in planets_dict.items():
        if p_name not in ["Rahu", "Ketu"]:
            dist = abs(node_lon - p_lon)
            if dist > 180: dist = 360 - dist
            if dist <= 3.33: return p_name 
    return get_sign_lord(node_lon)

def get_houses_owned_by_planet(planet, cusps, planets_dict):
    owned_houses = []
    planet_to_check = get_true_agent(planet, planets_dict)
    for i in range(1, 13):
        if get_sign_lord(cusps[i]) == planet_to_check:
            owned_houses.append(i)
    return owned_houses

def calculate_placidus_cusps(target_ascendant, lat, lon):
    """
    Finds the moment (within today's 24h UT window) whose Ascendant equals
    target_ascendant, then returns the Placidus cusps for that moment.

    Uses bisection instead of a brute-force minute/second scan: the real
    Ascendant is monotonically increasing in time (it never runs backward),
    so a coarse scan just needs to find which bracket the target falls in,
    then bisection narrows it to sub-second precision in ~10-15 more calls.
    This replaces ~1,680 swe.houses_ex calls with ~110, and is *more*
    precise than the old fixed 1-second resolution.
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
        # Fallback: shouldn't normally happen since the ascendant completes
        # a full 360 degree cycle roughly once per day.
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
    return final_cusps

def find_planet_house(planet_lon, cusps):
    for i in range(1, 13):
        next_i = 1 if i == 12 else i + 1
        if cusps[i] <= planet_lon < cusps[next_i]: return i
        if cusps[i] > cusps[next_i]:
            if planet_lon >= cusps[i] or planet_lon < cusps[next_i]: return i
    return 1

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

    # Calling your new Modular Engines
    lat, lon = location_engine.get_coordinates(city)
    if not lat: return {"error": "Location not found or GPS block active."}
    
    asc_data = kp_math.get_horary_chart(horary_number)
    target_asc = asc_data["ascendant_longitude"]
    horary_sub_lord = asc_data["sub_lord"]
    horary_star_lord = asc_data["star_lord"]  # the fixed Nakshatra lord from the 1-249 table
    
    cusps = calculate_placidus_cusps(target_asc, lat, lon)
    planets, retrogrades = transit_engine.get_live_planets()
    planet_houses = {p: find_planet_house(lon_val, cusps) for p, lon_val in planets.items()}
    
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
    is_retrograde = retrogrades.get(true_sl_star_lord, False)
    
    step_1_house = planet_houses.get(true_sl_star_lord, 0)
    step_2_houses = get_houses_owned_by_planet(true_sl_star_lord, cusps, planets)
    step_3_house = planet_houses.get(true_sub_lord, 0)
    step_4_houses = get_houses_owned_by_planet(true_sub_lord, cusps, planets)

    score = 0
    if step_1_house in positive_set: score += 4
    elif step_1_house in negative_set: score -= 4
        
    for h in step_2_houses:
        if h in positive_set: score += 3
        elif h in negative_set: score -= 3
            
    if step_3_house in positive_set: score += 2
    elif step_3_house in negative_set: score -= 2
        
    for h in step_4_houses:
        if h in positive_set: score += 1
        elif h in negative_set: score -= 1

    all_signified_houses = [step_1_house] + step_2_houses + [step_3_house] + step_4_houses
    
    if is_retrograde:
        verdict = f"DENIED. The Star Lord is Retrograde (Vakri). The event will fail or be heavily delayed."
    elif score >= 5:
        verdict = f"DEFINITIVE YES. Strong positive dominance (Score: +{score}). Success is highly likely."
    elif 1 <= score <= 4:
        verdict = f"YES WITH DELAYS. Positives slightly outweigh negatives (Score: +{score}). Expect success but with obstacles."
    elif -4 <= score <= 0:
        verdict = f"UNFAVORABLE / NO. Negatives overpower positives or lack strong support (Score: {score})."
    else:
        verdict = f"DEFINITIVE NO. Strong negative dominance (Score: {score}). The chart denies the event."
        
    return {
        "verdict": verdict, "kp_score": score, "sub_lord": horary_sub_lord, "star_lord": horary_star_lord, "is_retrograde": is_retrograde,
        "all_houses": list(set(all_signified_houses)), "moon_star_lord": get_star_lord(moon_lon),
        "punarphoo": punarphoo_active,
        "significators": {
            "true_star_lord": true_sl_star_lord,
            "true_sub_lord": true_sub_lord,
            "step_1_house": step_1_house,
            "step_2_houses": step_2_houses,
            "step_3_house": step_3_house,
            "step_4_houses": step_4_houses
        },
        "panchang": {"day_name": day_name, "tithi": current_tithi},
        "ruling_planets": {"asc_sign_lord": rp_asc_sign_lord, "asc_star_lord": rp_asc_star_lord, "moon_sign_lord": get_sign_lord(moon_lon), "moon_star_lord": get_star_lord(moon_lon), "day_lord": day_lord},
        "chart_data": {"cusps": list(cusps[1:]), "planets": planets, "planet_houses": planet_houses}
    }