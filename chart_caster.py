import swisseph as swe
from datetime import datetime, timezone
from geopy.geocoders import Nominatim
import kp_math

# --- CORE SETTINGS ---
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# --- ASTRONOMY HELPER FUNCTIONS ---
def get_sign_lord(degree):
    return SIGN_LORDS[int(degree // 30)]

def get_star_lord(degree):
    nak_index = int(degree / (13 + 1/3))
    return NAKSHATRA_LORDS[nak_index % 9]

def get_true_agent(planet, planets_dict):
    """ADVANCED KP RULE: Rahu/Ketu steal identity via Conjunction first, then Sign Lord."""
    if planet not in ["Rahu", "Ketu"]:
        return planet # Normal planets just return themselves
        
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
    # Get the true planet (or the stolen identity if it's Rahu/Ketu)
    planet_to_check = get_true_agent(planet, planets_dict)

    # pysweph v2.10.3.6 returns 13 elements, index 1 is 1st cusp
    for i in range(1, 13):
        if get_sign_lord(cusps[i]) == planet_to_check:
            owned_houses.append(i)
    return owned_houses

def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="kp_astrology_bot")
    try:
        location = geolocator.geocode(city_name)
        if location: return location.latitude, location.longitude
    except Exception: pass
    return None, None

def calculate_placidus_cusps(target_ascendant, lat, lon):
    now = datetime.now(timezone.utc)
    base_jd = swe.julday(now.year, now.month, now.day, 0.0)
    
    # STAGE 1: Coarse Search (Minute-by-Minute)
    best_jd, min_diff = base_jd, 360.0
    for minute in range(24 * 60):
        test_jd = base_jd + (minute / 1440.0)
        cusps, ascmc = swe.houses_ex(test_jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        diff = abs(ascmc[0] - target_ascendant)
        if diff > 180: diff = 360 - diff
        if diff < min_diff: min_diff, best_jd = diff, test_jd

    # STAGE 2: Fine Search (Second-by-Second micro-tuning for KP Sub-Lords)
    final_best_jd = best_jd
    min_diff = 360.0
    for sec in range(-120, 120): # Scan 2 minutes in either direction
        test_jd = best_jd + (sec / 86400.0)
        cusps, ascmc = swe.houses_ex(test_jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        diff = abs(ascmc[0] - target_ascendant)
        if diff > 180: diff = 360 - diff
        if diff < min_diff:
            min_diff, final_best_jd = diff, test_jd

    final_cusps, _ = swe.houses_ex(final_best_jd, lat, lon, b'P', swe.FLG_SIDEREAL)
    return final_cusps

def get_live_planets():
    """Returns planet longitudes AND Retrograde status (Speed < 0)"""
    now = datetime.now(timezone.utc)
    jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0 + now.second/3600.0)
    planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, 
               "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    
    positions = {}
    retrogrades = {}
    
    for name, p_id in planets.items():
        # raw[0][0] is longitude, raw[0][3] is speed in longitude
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
    # Properly spans all 12 houses and handles the 360 -> 0 Aries crossover
    for i in range(1, 13):
        next_i = 1 if i == 12 else i + 1
        
        if cusps[i] <= planet_lon < cusps[next_i]: 
            return i
        
        if cusps[i] > cusps[next_i]:
            if planet_lon >= cusps[i] or planet_lon < cusps[next_i]:
                return i
    return 1 # Fallback safeguard

# --- THE MASTER PIPELINE ---
def execute_kp_reading(city, horary_number, positive_houses, negative_houses):
    print("\n==================================================")
    print("        KP HORARY ASTROLOGY ENGINE (V1.0)         ")
    print("==================================================\n")

    # --- [PHASE 1: THE SETUP] ---
    print("--- [PHASE 1: THE SETUP] ---")
    lat, lon = get_coordinates(city)
    if not lat: return {"error": "Location not found."}
    
    asc_data = kp_math.get_horary_chart(horary_number)
    target_asc = asc_data["ascendant_longitude"]
    horary_sub_lord = asc_data["sub_lord"]
    
    print(f"Location Locked: {city} (Lat: {round(lat,2)}, Lon: {round(lon,2)})")
    print(f"Horary #{horary_number}: Ascendant at {round(target_asc, 2)}°")
    print(f"Horary Sub-Lord (The Decider): {horary_sub_lord}\n")

    # --- [PHASE 2: THE CHART CASTING] ---
    print("--- [PHASE 2: THE CHART CASTING] ---")
    cusps = calculate_placidus_cusps(target_asc, lat, lon)
    planets, retrogrades = get_live_planets()
    planet_houses = {p: find_planet_house(lon_val, cusps) for p, lon_val in planets.items()}
    
    print("12 Placidus House Cusps Generated.")
    print("Live Transits Locked to Time of Judgment.\n")

    # --- [PHASE 3: THE VALIDATION] ---
    print("--- [PHASE 3: THE VALIDATION] ---")
    moon_lon = planets["Moon"]
    moon_star_lord = get_star_lord(moon_lon)
    print(f"Moon's Star Lord is {moon_star_lord}.")
    
    saturn_lon = planets["Saturn"]
    dist = abs(moon_lon - saturn_lon)
    if dist > 180: dist = 360 - dist
    punarphoo_active = dist <= 3.33 
    
    if punarphoo_active:
        print("!!! WARNING: PUNARPHOO DOSHA DETECTED (Saturn/Moon Conjunction) !!!")
        print("The client's mind is highly anxious. Expect severe, unpredictable delays.")
    print("System Check: If this matches the primary houses of the query, the chart is valid.\n")

    # --- [PHASE 4: THE 4-STEP SIGNIFICATORS] ---
    print("--- [PHASE 4: THE 4-STEP SIGNIFICATORS] ---")
    sl_lon = planets[horary_sub_lord]
    sl_star_lord = get_star_lord(sl_lon)
    
    true_sl_star_lord = get_true_agent(sl_star_lord, planets)
    is_retrograde = retrogrades.get(true_sl_star_lord, False)
    if is_retrograde:
        print(f"!!! WARNING: The Star Lord ({true_sl_star_lord}) is RETROGRADE (Vakri) !!!")
    
    step_1_house = planet_houses[sl_star_lord]
    step_2_houses = get_houses_owned_by_planet(sl_star_lord, cusps, planets)
    step_3_house = planet_houses[horary_sub_lord]
    step_4_houses = get_houses_owned_by_planet(horary_sub_lord, cusps, planets)

    print(f"Step 1 (Strongest): House {step_1_house} (Occupied by its Star Lord, {sl_star_lord})")
    
    if sl_star_lord in ["Rahu", "Ketu"]:
        agent = get_true_agent(sl_star_lord, planets)
        print(f"Step 2 (Strong): Houses {step_2_houses} (Stolen by {sl_star_lord} acting as agent for {agent})")
    else:
        print(f"Step 2 (Strong): Houses {step_2_houses} (Owned by {sl_star_lord})")
        
    print(f"Step 3 (Weak): House {step_3_house} (Occupied by {horary_sub_lord})")
    
    if horary_sub_lord in ["Rahu", "Ketu"]:
        agent = get_true_agent(horary_sub_lord, planets)
        print(f"Step 4 (Weakest): Houses {step_4_houses} (Stolen by {horary_sub_lord} acting as agent for {agent})\n")
    else:
        print(f"Step 4 (Weakest): Houses {step_4_houses} (Owned by {horary_sub_lord})\n")

    # --- [THE FINAL DECISION ENGINE] ---
    print("--- [THE FINAL DECISION ENGINE] ---")
    
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
        
    print(f"Houses Signified: {list(set(all_signified_houses))}")
    print(f"KP Math Score: {score}")
    print(f"SYSTEM VERDICT: {verdict}")
    print("==================================================\n")
    
    return {
        "verdict": verdict,
        "kp_score": score,
        "sub_lord": horary_sub_lord,
        "is_retrograde": is_retrograde,
        "all_houses": list(set(all_signified_houses)),
        "moon_star_lord": moon_star_lord,
        "punarphoo": punarphoo_active
    }

if __name__ == "__main__":
    try:
        test_city = input("Enter City of Judgment: > ")
        test_num = int(input("Enter Horary Number (1-249): > "))
        # Provide default positive/negative houses just for terminal testing
        execute_kp_reading(test_city, test_num, [2, 11], [8, 12])
    except Exception as e:
        print(f"An error occurred: {e}")