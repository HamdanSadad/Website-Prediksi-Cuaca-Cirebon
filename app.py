import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Paths for models
MODEL_T6_PATH = os.path.join("models", "xgbfullt6.pkl")
MODEL_T24_PATH = os.path.join("models", "xgbfullt24.pkl")

# Global variables for models
model_t6 = None
model_t24 = None

# Attempt to load models at startup
try:
    if os.path.exists(MODEL_T6_PATH):
        model_t6 = joblib.load(MODEL_T6_PATH)
        print(f"Loaded model t+6 from {MODEL_T6_PATH}")
    else:
        print(f"Warning: Model t+6 not found at {MODEL_T6_PATH}. Using mock predictions.")

    if os.path.exists(MODEL_T24_PATH):
        model_t24 = joblib.load(MODEL_T24_PATH)
        print(f"Loaded model t+24 from {MODEL_T24_PATH}")
    else:
        print(f"Warning: Model t+24 not found at {MODEL_T24_PATH}. Using mock predictions.")
except Exception as e:
    print(f"Error loading models: {e}. Will use mock predictions.")

def get_air_quality_category(pm25_value):
    """
    Sederhana: mapping PM2.5 ke kategori kualitas udara.
    0 - 15.5   : Baik
    15.6 - 55.4: Sedang
    55.5 - 150.4: Tidak Sehat
    150.5 - 250.4: Sangat Tidak Sehat
    > 250.5    : Berbahaya
    """
    if pm25_value <= 15.5:
        return "Baik", "good"
    elif pm25_value <= 55.4:
        return "Sedang", "moderate"
    elif pm25_value <= 150.4:
        return "Tidak Sehat", "unhealthy"
    elif pm25_value <= 250.4:
        return "Sangat Tidak Sehat", "very-unhealthy"
    else:
        return "Berbahaya", "hazardous"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health_check():
    return jsonify({"status": "ok"})

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json
        
        # Parse inputs
        obs_datetime_str = data.get("datetime")
        pm25_current = float(data.get("pm25", 0))
        suhuC = float(data.get("suhuC", 0))
        kelembapan = float(data.get("kelembapan", 0))
        curahhujan = float(data.get("curahhujan", 0))
        angin = float(data.get("angin", 0))
        
        obs_dt = datetime.fromisoformat(obs_datetime_str)
        
        # 1. Feature Engineering
        hour = obs_dt.hour
        dayofweek = obs_dt.weekday() # 0 = Monday, 6 = Sunday
        month = obs_dt.month
        weekend = 1 if dayofweek >= 5 else 0
        quarter = (month - 1) // 3 + 1
        dayofyear = obs_dt.timetuple().tm_yday
        
        # Cyclic features
        sinhour = np.sin(2 * np.pi * hour / 23.0) if hour <= 23 else 0
        coshour = np.cos(2 * np.pi * hour / 23.0) if hour <= 23 else 1
        sindayofweek = np.sin(2 * np.pi * dayofweek / 6.0)
        cosdayofweek = np.cos(2 * np.pi * dayofweek / 6.0)
        
        # Prepare feature vector strictly matching the 46 features in order
        feature_dict = {
            'suhu_C': suhuC,
            'kelembapan_%': kelembapan,
            'curah_hujan_mm': curahhujan,
            'angin_kmh': angin,
            'pm2_5': pm25_current,
            'pm25_lag_1': pm25_current,
            'suhu_lag_1': suhuC,
            'curah_hujan_lag_1': curahhujan,
            'pm25_lag_3': pm25_current,
            'suhu_lag_3': suhuC,
            'curah_hujan_lag_3': curahhujan,
            'pm25_lag_6': pm25_current,
            'suhu_lag_6': suhuC,
            'curah_hujan_lag_6': curahhujan,
            'pm25_lag_12': pm25_current,
            'pm25_lag_24': pm25_current,
            'suhu_lag_24': suhuC,
            'curah_hujan_lag_24': curahhujan,
            'pm25_lag_48': pm25_current,
            'pm25_lag_72': pm25_current,
            'pm25_lag_168': pm25_current,
            'rolling_mean_6': pm25_current,
            'rolling_mean_12': pm25_current,
            'rolling_mean_24': pm25_current,
            'rolling_std_24': 0,
            'rolling_max_24': pm25_current,
            'rolling_min_24': pm25_current,
            'rolling_median_24': pm25_current,
            'expanding_mean': pm25_current,
            'expanding_std': 0,
            'sin_hour': sinhour,
            'cos_hour': coshour,
            'sin_dayofweek': sindayofweek,
            'cos_dayofweek': cosdayofweek,
            'diff_1': 0,
            'diff_24': 0,
            'hum_temp_interact': kelembapan * suhuC,
            'wind_pm25_interact': angin * pm25_current,
            'high_pollution_flag': 1 if pm25_current > 55.4 else 0,
            'sudden_change_flag': 0,
            'hour': hour,
            'dayofweek': dayofweek,
            'month': month,
            'weekend': weekend,
            'quarter': quarter,
            'dayofyear': dayofyear
        }
        
        features_df = pd.DataFrame([feature_dict])
        
        # 2. Predict t+6
        if model_t6:
            pred_t6_log = model_t6.predict(features_df)[0]
            pred_t6 = np.expm1(pred_t6_log)
        else:
            # Mock prediction if model not loaded
            pred_t6 = max(0, pm25_current + np.random.uniform(-5, 15))
            
        # 3. Predict t+24
        if model_t24:
            pred_t24_log = model_t24.predict(features_df)[0]
            pred_t24 = np.expm1(pred_t24_log)
        else:
            # Mock prediction if model not loaded
            pred_t24 = max(0, pm25_current + np.random.uniform(-10, 20))
            
        # 4. Get categories
        cat_t6, cat_class_t6 = get_air_quality_category(pred_t6)
        cat_t24, cat_class_t24 = get_air_quality_category(pred_t24)
        cat_current, cat_class_current = get_air_quality_category(pm25_current)
        
        return jsonify({
            "status": "success",
            "pm25_current": round(float(pm25_current), 1),
            "category_current": cat_current,
            "category_class_current": cat_class_current,
            
            "pm25_t6": round(float(pred_t6), 1),
            "category_t6": cat_t6,
            "category_class_t6": cat_class_t6,
            
            "pm25_t24": round(float(pred_t24), 1),
            "category_t24": cat_t24,
            "category_class_t24": cat_class_t24,
            
            "timestamp": obs_dt.strftime("%Y-%m-%d %H:%M")
        })

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/weather-auto", methods=["GET"])
def weather_auto():
    try:
        dt_str = request.args.get("datetime")
        lat = request.args.get("lat", "-6.7063") # Default Cirebon lat
        lon = request.args.get("lon", "108.557") # Default Cirebon lon
        
        if not dt_str:
            return jsonify({"status": "error", "message": "Parameter datetime diperlukan"}), 400
            
        target_dt = datetime.fromisoformat(dt_str)
        target_date_str = target_dt.strftime("%Y-%m-%d")
        
        # 1. Fetch Weather Data
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": "Asia/Jakarta",
            "start_date": target_date_str,
            "end_date": target_date_str
        }
        weather_res = requests.get(weather_url, params=weather_params, timeout=10)
        weather_res.raise_for_status()
        weather_data = weather_res.json()
        
        # 2. Fetch Air Quality Data
        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aq_params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "pm2_5",
            "timezone": "Asia/Jakarta",
            "start_date": target_date_str,
            "end_date": target_date_str
        }
        aq_res = requests.get(aq_url, params=aq_params, timeout=10)
        aq_res.raise_for_status()
        aq_data = aq_res.json()
        
        # Find closest hour
        target_hour_str = target_dt.strftime("%Y-%m-%dT%H:00")
        times = weather_data.get("hourly", {}).get("time", [])
        
        if not times:
            return jsonify({"status": "error", "message": "Data per jam tidak tersedia di Open-Meteo"}), 404
            
        try:
            idx = times.index(target_hour_str)
        except ValueError:
            idx = target_dt.hour
            if idx >= len(times):
                idx = -1
        
        temp = weather_data["hourly"]["temperature_2m"][idx]
        humidity = weather_data["hourly"]["relative_humidity_2m"][idx]
        precip = weather_data["hourly"]["precipitation"][idx]
        wind_speed = weather_data["hourly"]["wind_speed_10m"][idx]
        
        pm25 = None
        aq_times = aq_data.get("hourly", {}).get("time", [])
        if aq_times:
            try:
                aq_idx = aq_times.index(target_hour_str)
            except ValueError:
                aq_idx = target_dt.hour
                if aq_idx >= len(aq_times): aq_idx = -1
            pm25 = aq_data["hourly"].get("pm2_5", [])[aq_idx]
            
        return jsonify({
            "status": "success",
            "pm25": float(pm25) if pm25 is not None else None,
            "suhuC": float(temp),
            "kelembapan": float(humidity),
            "curahhujanmm": float(precip),
            "anginkmh": float(wind_speed),
            "source_time": times[idx]
        })
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Open-Meteo: {e}")
        return jsonify({"status": "error", "message": "Gagal mengambil data dari API Open-Meteo"}), 502
    except Exception as e:
        print(f"Error in weather-auto: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    app.run(debug=True, port=5000)
