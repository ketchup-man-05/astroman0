import swisseph as swe

# Vimshottari dasha definitions
dasha_sequence = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
]
total_dasha_years = 120
nakshatra_length = 13.333333333333334
zodiac_signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_kp_dignities(longitude):
    """Takes any 360-degree longitude and returns Sign, Star, and Sub-Lord."""
    sign_index = int(longitude // 30)
    sign_name = zodiac_signs[sign_index]

    nakshatra_index = int(longitude // nakshatra_length)
    star_lord = dasha_sequence[nakshatra_index % 9][0]

    degree_in_nakshatra = longitude - (nakshatra_index * nakshatra_length)
    current_sub_lord = ""
    accumulated_span = 0.0
    start_idx = nakshatra_index % 9

    for i in range(9):
        idx = (start_idx + i) % 9
        planet_name, dasha_years = dasha_sequence[idx]
        span = (dasha_years / total_dasha_years) * nakshatra_length
        accumulated_span += span
        if degree_in_nakshatra <= accumulated_span:
            current_sub_lord = planet_name
            break

    return {
        "longitude": round(longitude, 4),
        "sign": sign_name,
        "star_lord": star_lord,
        "sub_lord": current_sub_lord
    }

def generate_kp_249_table():
    """Generates the official 249 KP Horary sub-lord boundaries."""
    table = []
    current_longitude = 0.0
    
    for nak_idx in range(27):
        star_lord = dasha_sequence[nak_idx % 9][0]
        start_sub_idx = nak_idx % 9
        
        for i in range(9):
            sub_idx = (start_sub_idx + i) % 9
            sub_lord, years = dasha_sequence[sub_idx]
            span = (years / total_dasha_years) * nakshatra_length
            end_longitude = current_longitude + span
            
            # Rounding to prevent floating-point drift
            c_lon = round(current_longitude, 6)
            e_lon = round(end_longitude, 6)
            
            current_sign_idx = int(c_lon // 30)
            end_sign_idx = int((e_lon - 0.000001) // 30)
            
            if current_sign_idx != end_sign_idx and end_sign_idx < 12:
                split_point = end_sign_idx * 30.0
                table.append({
                    "start_deg": current_longitude,
                    "sign": zodiac_signs[current_sign_idx],
                    "star_lord": star_lord,
                    "sub_lord": sub_lord
                })
                table.append({
                    "start_deg": split_point,
                    "sign": zodiac_signs[end_sign_idx],
                    "star_lord": star_lord,
                    "sub_lord": sub_lord
                })
            else:
                table.append({
                    "start_deg": current_longitude,
                    "sign": zodiac_signs[current_sign_idx],
                    "star_lord": star_lord,
                    "sub_lord": sub_lord
                })
            current_longitude = end_longitude
            
    return table

kp_table = generate_kp_249_table()

def get_horary_chart(number):
    """Takes a Horary Number (1-249) and returns its exact Ascendant details."""
    if not (1 <= number <= 249):
        return {"error": "Horary number must be between 1 and 249"}
    
    entry = kp_table[number - 1]
    return {
        "horary_number": number,
        "ascendant_longitude": round(entry["start_deg"], 4),
        "sign": entry["sign"],
        "star_lord": entry["star_lord"],
        "sub_lord": entry["sub_lord"]
    }

# --- TEST 1-249 ---
print(f"Total KP subdivisions generated: {len(kp_table)}")
test_num = 45
chart = get_horary_chart(test_num)
print(f"Horary #{test_num}: {chart['sign']} at {chart['ascendant_longitude']}° | Star: {chart['star_lord']} | Sub: {chart['sub_lord']}")