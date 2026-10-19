import os
import pickle
import datetime
from typing import Dict, Any, List
import pandas as pd

MODEL_PKL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "food_demand_model.pkl")
FALLBACK_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")

# Cached ML model instance
_model_artifact = None
_model_loaded_time = None


def load_ml_model():
    global _model_artifact, _model_loaded_time
    target_path = MODEL_PKL_PATH if os.path.exists(MODEL_PKL_PATH) else FALLBACK_MODEL_PATH
    if os.path.exists(target_path):
        try:
            with open(target_path, "rb") as f:
                loaded = pickle.load(f)
            # If the artifact is a dict containing 'model', 'features', etc.
            if isinstance(loaded, dict) and "model" in loaded:
                _model_artifact = loaded
            else:
                _model_artifact = {"model": loaded, "features": None, "cat_cols": []}
            _model_loaded_time = os.path.getmtime(target_path)
            print(f"[ML Engine] Successfully loaded ML model from {target_path}")
            return _model_artifact
        except Exception as e:
            print(f"[ML Engine] Warning: Failed to unpickle {target_path}: {e}")
            _model_artifact = None
    else:
        _model_artifact = None
    return _model_artifact


def get_model_status() -> Dict[str, Any]:
    """Check whether food_demand_model.pkl is currently loaded or in fallback mode."""
    target_path = MODEL_PKL_PATH if os.path.exists(MODEL_PKL_PATH) else FALLBACK_MODEL_PATH
    is_available = os.path.exists(target_path) and _model_artifact is not None
    return {
        "model_file_exists": is_available,
        "model_path": target_path,
        "model_status": "active_lightgbm_model" if is_available else "heuristic_fallback_ready",
        "description": "LightGBM trained production model active." if is_available else "Using heuristic fallback engine."
    }


# Standard menu item coefficients for realistic meal item breakdown
MENU_BLUEPRINTS = {
    "breakfast": [
        {"name": "Idli", "unit": "plates", "base_ratio": 0.88, "waste_risk": "medium"},
        {"name": "Sambar", "unit": "liters", "base_ratio": 0.24, "waste_risk": "low"},
        {"name": "Coconut Chutney", "unit": "liters", "base_ratio": 0.095, "waste_risk": "high"},
        {"name": "Vada", "unit": "pieces", "base_ratio": 0.62, "waste_risk": "medium"},
        {"name": "Filter Coffee / Tea", "unit": "cups", "base_ratio": 0.78, "waste_risk": "low"}
    ],
    "lunch": [
        {"name": "Steamed Rice", "unit": "plates", "base_ratio": 0.94, "waste_risk": "high"},
        {"name": "Dal / Sambar", "unit": "liters", "base_ratio": 0.23, "waste_risk": "medium"},
        {"name": "Vegetable Curry (Sabzi)", "unit": "liters", "base_ratio": 0.19, "waste_risk": "medium"},
        {"name": "Rasam / Soup", "unit": "liters", "base_ratio": 0.16, "waste_risk": "low"},
        {"name": "Curd / Yogurt", "unit": "cups", "base_ratio": 0.88, "waste_risk": "low"}
    ],
    "snacks": [
        {"name": "Masala Vada / Samosa", "unit": "pieces", "base_ratio": 0.58, "waste_risk": "high"},
        {"name": "Hot Tea", "unit": "cups", "base_ratio": 0.78, "waste_risk": "low"},
        {"name": "Coffee", "unit": "cups", "base_ratio": 0.55, "waste_risk": "low"},
        {"name": "Pakora / Bajji", "unit": "plates", "base_ratio": 0.48, "waste_risk": "medium"},
        {"name": "Biscuits / Cookies", "unit": "packets", "base_ratio": 0.42, "waste_risk": "low"}
    ],
    "dinner": [
        {"name": "Steamed Rice", "unit": "plates", "base_ratio": 0.88, "waste_risk": "high"},
        {"name": "Chapati / Roti", "unit": "pieces", "base_ratio": 1.45, "waste_risk": "medium"},
        {"name": "Dal Tadka", "unit": "liters", "base_ratio": 0.20, "waste_risk": "medium"},
        {"name": "Mixed Veg Curry", "unit": "liters", "base_ratio": 0.18, "waste_risk": "medium"},
        {"name": "Curd", "unit": "cups", "base_ratio": 0.72, "waste_risk": "low"}
    ]
}


def predict_kitchen_demand(
    meal_type: str = "breakfast",
    attendance: int = 150,
    hostel_attendance: int = None,
    dayscholar_attendance: int = None,
    temperature_c: float = 27.0,
    rainfall_mm: float = 0.0,
    humidity_pct: float = 60.0,
    day_type: str = "weekday",
    is_exam_day: bool = False,
    is_college_event: bool = False,
    previous_demand: int = None,
    avg_7day_demand: int = None,
    popularity_level: int = 2
) -> Dict[str, Any]:
    """
    Predict overall meal counts and itemized requirements using the trained LightGBM ML model.
    """
    artifact = load_ml_model()

    meal_key = meal_type.lower()
    if meal_key not in MENU_BLUEPRINTS:
        meal_key = "breakfast"

    predicted_meals = None
    model_source = "heuristic_fallback"

    # Default attendance calculations
    expected_att = max(10, attendance)
    hostel_att = hostel_attendance if hostel_attendance is not None else int(expected_att * 0.65)
    dayscholar_att = dayscholar_attendance if dayscholar_attendance is not None else int(expected_att * 0.35)
    prev_demand = previous_demand if previous_demand is not None else int(expected_att * 0.95)
    rolling_7d = avg_7day_demand if avg_7day_demand is not None else int(expected_att * 0.96)
    temp_c = float(temperature_c) if temperature_c is not None else 27.0
    rain_mm = float(rainfall_mm) if rainfall_mm is not None else 0.0
    hum_pct = float(humidity_pct) if humidity_pct is not None else 65.0

    is_weekend = (day_type == "weekend")
    is_holiday = (day_type == "holiday")

    now = datetime.datetime.now()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = days_of_week[now.weekday()]
    if is_weekend:
        day_name = "Saturday" if now.weekday() < 5 else day_name

    weather_condition = "Rainy" if rain_mm > 15 else ("Cloudy" if rain_mm > 5 else "Sunny")
    weather_severity = 3.0 if rain_mm > 25 else (2.0 if rain_mm > 8 else 1.0)
    event_type = "College Event" if is_college_event else "None"
    primary_menu_item = MENU_BLUEPRINTS[meal_key][0]["name"]
    total_students = max(expected_att + 200, 1000)
    attendance_rate = min(1.0, round(expected_att / total_students, 2))
    total_reservations = hostel_att + int(dayscholar_att * 0.5)

    if artifact is not None and "model" in artifact and artifact.get("features"):
        try:
            model = artifact["model"]
            features = artifact["features"]
            cat_cols = artifact.get("cat_cols", [])

            feature_dict = {
                "Meal_Type": [meal_key.title()],
                "Menu_Item": [primary_menu_item],
                "Food_Category": [meal_key.title()],
                "Day_of_Week": [day_name],
                "Event_Type": [event_type],
                "Weather_Condition": [weather_condition],
                "Month": [now.month],
                "Day_of_Month": [now.day],
                "Week_of_Year": [now.isocalendar()[1]],
                "Semester_Week": [8],
                "Is_Weekend": [1 if is_weekend else 0],
                "Is_Holiday": [1 if is_holiday else 0],
                "Is_Exam_Day": [1 if is_exam_day else 0],
                "Is_College_Event": [1 if is_college_event else 0],
                "Total_Students": [total_students],
                "Expected_Attendance": [expected_att],
                "Attendance_Rate_Expected": [attendance_rate],
                "Total_Reservations": [total_reservations],
                "Hostel_Preorders": [hostel_att],
                "Expected_Event_Attendance": [expected_att if is_college_event else 0],
                "Temperature_C": [temp_c],
                "Rainfall_mm": [rain_mm],
                "Humidity_Percent": [hum_pct],
                "Weather_Severity": [weather_severity],
                "Previous_Day_Demand": [prev_demand],
                "Demand_Lag_7_Days": [rolling_7d],
                "Demand_Lag_14_Days": [rolling_7d],
                "Rolling_7Day_Demand": [float(rolling_7d)]
            }

            df = pd.DataFrame(feature_dict)
            for c in cat_cols:
                if c in df.columns:
                    df[c] = df[c].astype("category")

            pred = model.predict(df[features])
            raw_prediction = float(pred[0])

            # Apply popularity multiplier
            if popularity_level == 3:
                raw_prediction *= 1.05
            elif popularity_level == 1:
                raw_prediction *= 0.95

            predicted_meals = max(10.0, round(raw_prediction, 1))
            model_source = "LightGBM Trained Model (food_demand_model.pkl)"
        except Exception as e:
            print(f"[ML Engine] LightGBM prediction error ({e}), utilizing heuristic formula.")
            predicted_meals = None

    if predicted_meals is None:
        # Heuristic fallback if model execution hits an unexpected issue
        base_demand = (expected_att * 0.72) + (prev_demand * 0.28)
        if popularity_level == 3:
            base_demand += 10
        elif popularity_level == 1:
            base_demand -= 10
        if rain_mm > 20:
            base_demand -= 8
        if is_weekend:
            base_demand -= 15
        if is_holiday:
            base_demand -= 25
        if is_exam_day:
            base_demand += 12
        if is_college_event:
            base_demand += 25
        predicted_meals = max(10.0, round(base_demand, 1))
        model_source = "Heuristic Regression Fallback"

    # Safety buffer calculation (6% safety buffer to eliminate food shortfalls while controlling waste)
    safety_buffer_pct = 6.0
    safety_buffer = round(predicted_meals * (safety_buffer_pct / 100.0), 1)
    recommended_prep = int(round(predicted_meals + safety_buffer))

    # Itemized portion breakdown
    items_blueprint = MENU_BLUEPRINTS[meal_key]
    top_items = []
    for item in items_blueprint:
        qty = max(1, round(predicted_meals * item["base_ratio"]))
        top_items.append({
            "name": item["name"],
            "unit": item["unit"],
            "quantity": qty,
            "waste_risk": item["waste_risk"]
        })

    top_item_name = top_items[0]["name"] if top_items else "Primary Item"
    recommendation_text = (
        f"For {meal_key.title()}, {top_item_name} is projected as highest demand. "
        f"Base ML Demand: {int(predicted_meals)} servings + {safety_buffer_pct}% safety buffer ({int(safety_buffer)} servings) "
        f"= Recommended Preparation: {recommended_prep} units."
    )

    return {
        "meal_type": meal_key,
        "attendance": expected_att,
        "predicted_demand": int(round(predicted_meals)),
        "safety_buffer": int(round(safety_buffer)),
        "safety_buffer_percent": safety_buffer_pct,
        "recommended_prep": recommended_prep,
        "model_source": model_source,
        "top_items": top_items,
        "recommendation": recommendation_text,
        "weather": weather_condition,
        "demand_status": "High Demand" if predicted_meals >= expected_att * 0.9 else "Optimal",
        "temperature_c": temp_c,
        "rainfall_mm": rain_mm,
        "humidity_pct": hum_pct
    }


# Initial model load attempt on start
load_ml_model()
