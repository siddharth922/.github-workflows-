import os
import requests
import datetime
import pandas as pd

# District Coordinates Mapping for Weather Ingestion
DISTRICT_COORDS = {
    # Madhya Pradesh
    "Rajgarh": {"lat": 24.01, "lon": 76.73},
    "Gwalior": {"lat": 26.22, "lon": 78.18},
    "Morena": {"lat": 26.50, "lon": 78.00},
    "Chhindwara": {"lat": 22.06, "lon": 78.93},
    # Maharashtra
    "Sambhaji Nagar": {"lat": 19.87, "lon": 75.34},
    "Jalna": {"lat": 19.84, "lon": 75.88},
    # Uttar Pradesh
    "Agra": {"lat": 27.17, "lon": 78.00},
    "Farrukhabad": {"lat": 27.38, "lon": 79.58},
    # Punjab & HP
    "Amritsar": {"lat": 31.63, "lon": 74.87},
    "Una (HP)": {"lat": 31.46, "lon": 76.27},
    # Bihar
    "Arariya": {"lat": 26.15, "lon": 87.51},
    "Purnea": {"lat": 25.77, "lon": 87.47},
    # West Bengal
    "Raiganj": {"lat": 25.62, "lon": 88.12}
}

def fetch_daily_weather(lat, lon):
    """Fetch 7-day trailing weather and soil temp from Open-Meteo."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=rain_sum,soil_temperature_0_to_10cm_mean&timezone=Asia/Kolkata"
    res = requests.get(url).json()
    
    if "daily" in res:
        df = pd.DataFrame(res["daily"])
        recent_rain = df["rain_sum"].tail(7).sum()
        avg_soil_temp = df["soil_temperature_0_to_10cm_mean"].tail(3).mean()
        return recent_rain, avg_soil_temp
    return 0, 20.0

def calculate_sowing_score(recent_rain, soil_temp, crop_category):
    """
    Core Logic: Calculates Sowing Readiness Score (0-100%) based on weather conditions.
    """
    score = 50 # Baseline score
    
    # Rainfall evaluation
    if recent_rain > 20 and recent_rain < 100:
        score += 30  # Optimal moisture window
    elif recent_rain >= 100:
        score -= 20  # Waterlogged field risk
    else:
        score -= 15  # Dry soil delay
        
    # Soil Temperature evaluation
    if crop_category in ["Cereals", "Oilseeds"] and 18 <= soil_temp <= 30:
        score += 20
    elif crop_category in ["Vegetables"] and 15 <= soil_temp <= 28:
        score += 20
        
    final_score = max(0, min(100, score))
    
    # Status determination
    if final_score >= 75:
        status = "Optimal Sowing Window Open"
    elif final_score >= 45:
        status = "Moderate Sowing Activity"
    else:
        status = "Suboptimal Conditions / Preparation Phase"
        
    return final_score, status

if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    print(f"Running automated daily ETL for {today}...")
    
    for district, coords in DISTRICT_COORDS.items():
        rain, soil_temp = fetch_daily_weather(coords["lat"], coords["lon"])
        score, status = calculate_sowing_score(rain, soil_temp, "Cereals")
        print(f"[{district}] 7-Day Rain: {rain}mm | Soil Temp: {soil_temp}°C | Sowing Score: {score}% ({status})")
