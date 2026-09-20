import swisseph as swe
from datetime import datetime, timezone, timedelta
from geopy.geocoders import Nominatim
import kp_math

# --- CORE SETTINGS ---
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# --- PANCHANG CONSTANTS ---
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", 
          "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima", "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", 
          "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"]

# --- ASTRONOMY HELPER FUNCTIONS ---
def get_sign_lord(degree):
    return SIGN_LORDS[int(degree // 30)]

def get_star_lord(degree):
    nak_index = int(degree / (13 + 1/3))
    return NAKSHATRA_LORDS[nak_index % 9]

def get_true_agent(planet, planets_dict):
    """ADVANCED KP RULE: Rahu/Ketu steal identity via Conjunction first, then Sign Lord."""
    if planet not in ["Rahu", "Ketu"]:
        return planet
        
    node_lon = planets_dict[planet]
    
    # 1. Conjunction Check (Is any planet within 3.33 degrees?)
    for p_name, p_lon in planets_dict.items():
        if p_name not in ["Rahu", "Ketu"]:
            dist = abs(node_lon - p_lon)
            if dist > 180: dist = 360 - dist
            if dist <= 3.33:
                return p_name # Stole conjunct planet's identity!
                
    # 2. Sign Lord Check (If no conjunction, steal Landlord's identity)
    return get_sign_lord(node_lon)

def get_houses_owned_by_planet(planet, cusps, planets_dict):
    owned_houses = []
    planet_to_check = get_true_agent(planet, planets_dict)

    for i in range(1, 13):
        if get_sign_lord(cusps[i]) == planet_to_check:
            owned_houses.append(i)
    return owned_houses

def get_coordinates(city_name):
    # THE FIX: Restored the fast-track bypass and timeout
    if city_name.lower() == "shimla":
        return 31.10, 77.17
        
    geolocator = Nominatim(user_agent="kp_astrology_bot")
    try:
        location = geolocator.geocode(city_name, timeout=3)
        if location: return location.latitude, location.longitude
    except Exception: pass
    return None, None

def calculate_placidus_cusps(target_ascendant, lat, lon):
    now = datetime.now(timezone.utc)
    base_jd = swe.julday(now.year, now.month, now.day, 0.0)
    
    # STAGE 1: Coarse Search
    best_jd, min_diff = base_jd, 360.0
    for minute in range(24 * 60):
        test_jd = base_jd + (minute / 1440.0)
        cusps, ascmc = swe.houses_ex(test_jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        diff = abs(ascmc[0] - target_ascendant)
        if diff > 180: diff = 360 - diff
        if diff < min_diff: min_diff, best_jd = diff, test_jd

    # STAGE 2: Fine Search
    final_best_jd = best_jd
    min_diff = 360.0
    for sec in range(-120, 120):
        test_jd = best_jd + (sec / 86400.0)
        cusps, ascmc = swe.houses_ex(test_jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        diff = abs(ascmc[0] - target_ascendant)
        if diff > 180: diff = 360 - diff
        if diff < min_diff:
            min_diff, final_best_jd = diff, test_jd

    final_cusps, _ = swe.houses_ex(final_best_jd, lat, lon, b'P', swe.FLG_SIDEREAL)
    return final_cusps

def get_live_planets():
    """Returns planet longitudes AND Retrograde status"""
    now = datetime.now(timezone.utc)
    jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0 + now.second/3600.0)
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, 
               "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    
    positions = {}
    retrogrades = {}
    
    for name, p_id in planets.items():
        raw = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        positions[name] = raw[0][0]
        speed = raw[0][3]
        
        if name in ["Sun", "Moon", "Rahu", "Ketu"]:
            retrogrades[name] = False
        else:
            retrogrades[name] = speed < 0 

    positions["Ketu"] = (positions["Rahu"] + 180) % 360
    retrogrades["Ketu"] = False
    return positions, retrogrades

def find_planet_house(planet_lon, cusps):
    for i in range(1, 13):
        next_i = 1 if i == 12 else i + 1
        if cusps[i] <= planet_lon < cusps[next_i]: 
            return i
        if cusps[i] > cusps[next_i]:
            if planet_lon >= cusps[i] or planet_lon < cusps[next_i]:
                return i
    return 1

# --- PANCHANG & RULING PLANET ENGINES ---
def get_panchang_tithi(sun_lon, moon_lon):
    diff = (moon_lon - sun_lon) % 360
    tithi_index = int(diff / 12)
    paksha = "Shukla (Waxing)" if tithi_index < 15 else "Krishna (Waning)"
    return f"{paksha} {TITHIS[tithi_index]}"

def get_current_day_lord(lon):
    # Dynamically calculate the user's timezone offset based on their GPS Longitude
    # The Earth rotates 15 degrees per hour.
    offset_hours = lon / 15.0
    
    now = datetime.now(timezone.utc)
    local_time = now + timedelta(hours=offset_hours)
    
    weekday = local_time.weekday() # Monday = 0
    sun_index = (weekday + 1) % 7
    
    # Hindu day changes at roughly 6 AM local time, not midnight.
    if local_time.hour < 6:
        sun_index = (sun_index - 1) % 7
        
    return DAYS[sun_index], DAY_LORDS[sun_index]

def get_live_ascendant(lat, lon):
    now = datetime.now(timezone.utc)
    jd_ut = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0 + now.second/3600.0)
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
    return ascmc[0]

# --- THE MASTER PIPELINE ---
def execute_kp_reading(city, horary_number, positive_houses, negative_houses):
    lat, lon = get_coordinates(city)
    if not lat: return {"error": "Location not found."}
    
    asc_data = kp_math.get_horary_chart(horary_number)
    target_asc = asc_data["ascendant_longitude"]
    horary_sub_lord = asc_data["sub_lord"]
    
    # 1. Cast the Horary Chart
    cusps = calculate_placidus_cusps(target_asc, lat, lon)
    planets, retrogrades = get_live_planets()
    planet_houses = {p: find_planet_house(lon_val, cusps) for p, lon_val in planets.items()}
    
    # 2. Run the Panchang & Ruling Planets (The "When" Engine)
    live_asc = get_live_ascendant(lat, lon)
    rp_asc_sign_lord = get_sign_lord(live_asc)
    rp_asc_star_lord = get_star_lord(live_asc)
    
    moon_lon = planets["Moon"]
    moon_sign_lord = get_sign_lord(moon_lon)
    moon_star_lord = get_star_lord(moon_lon)
    
    day_name, day_lord = get_current_day_lord()
    current_tithi = get_panchang_tithi(planets["Sun"], moon_lon)
    
    # 3. Validation & Punarphoo
    saturn_lon = planets["Saturn"]
    dist = abs(moon_lon - saturn_lon)
    if dist > 180: dist = 360 - dist
    punarphoo_active = dist <= 3.33 

    # 4. 4-Step Significators
    sl_lon = planets[horary_sub_lord]
    sl_star_lord = get_star_lord(sl_lon)
    
    true_sl_star_lord = get_true_agent(sl_star_lord, planets)
    is_retrograde = retrogrades.get(true_sl_star_lord, False)
    
    step_1_house = planet_houses[sl_star_lord]
    step_2_houses = get_houses_owned_by_planet(sl_star_lord, cusps, planets)
    step_3_house = planet_houses[horary_sub_lord]
    step_4_houses = get_houses_owned_by_planet(horary_sub_lord, cusps, planets)

    # 5. Scoring Engine
    score = 0
    if step_1_house in positive_houses: score += 4
    elif step_1_house in negative_houses: score -= 4
        
    for h in step_2_houses:
        if h in positive_houses: score += 3
        elif h in negative_houses: score -= 3
            
    if step_3_house in positive_houses: score += 2
    elif step_3_house in negative_houses: score -= 2
        
    for h in step_4_houses:
        if h in positive_houses: score += 1
        elif h in negative_houses: score -= 1

    strong_houses = [step_1_house] + step_2_houses
    weak_houses = [step_3_house] + step_4_houses
    all_signified_houses = strong_houses + weak_houses
    
    if is_retrograde:
        verdict = f"DENIED. The Star Lord is Retrograde (Vakri). The event will fail or be heavily delayed."
    elif score >= 5:
        verdict = f"DEFINITIVE YES. Strong positive dominance (Score: +{score}). Success is highly likely."
    elif 1 <= score <= 4:
        verdict = f"YES WITH DELAYS. Positives slightly outweigh negatives (Score: +{score}). Expect success but with obstacles."
    elif -4 <= score <= 0:
        verdict = f"UNFAVORABLE / NO. Negatives overpower positives or lack strong support (Score: {score})."
    elif score <= -5:
        verdict = f"DEFINITIVE NO. Strong negative dominance (Score: {score}). The chart denies the event."
    else:
        verdict = "NEUTRAL. The active houses do not indicate a clear win or loss."
        
    # 6. Build the Massive Return JSON
    return {
        "verdict": verdict,
        "kp_score": score,
        "sub_lord": horary_sub_lord,
        "is_retrograde": is_retrograde,
        "all_houses": list(set(all_signified_houses)),
        "moon_star_lord": moon_star_lord,
        "punarphoo": punarphoo_active,
        
        # THE FIX: I added the significators here so the AI can finally see the math!
        "significators": {
            "step_1_house": step_1_house,
            "step_2_houses": step_2_houses,
            "step_3_house": step_3_house,
            "step_4_houses": step_4_houses
        },
        
        "panchang": {
            "day_name": day_name,
            "tithi": current_tithi
        },
        "ruling_planets": {
            "asc_sign_lord": rp_asc_sign_lord,
            "asc_star_lord": rp_asc_star_lord,
            "moon_sign_lord": moon_sign_lord,
            "moon_star_lord": moon_star_lord,
            "day_lord": day_lord
        },
        "chart_data": {
            "cusps": list(cusps[1:]), # Strips the 0 index so it matches Houses 1-12
            "planets": planets,
            "planet_houses": planet_houses
        }
    }