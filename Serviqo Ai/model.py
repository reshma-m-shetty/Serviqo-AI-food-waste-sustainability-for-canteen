import pickle
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ================================================================
# 1. LOAD DATASET
# ================================================================
data_path = "food_demand_FINAL_3_year_balanced_relationships.csv"
print(f"Loading dataset from: {data_path} ...")
df = pd.read_csv(data_path)
df["Date"] = pd.to_datetime(df["Date"])

# ================================================================
# 2. DEFINE FEATURES & TARGET
# ================================================================
target_col = "Actual_Demand"

cat_cols = [
    "Meal_Type",
    "Menu_Item",
    "Food_Category",
    "Day_of_Week",
    "Event_Type",
    "Weather_Condition",
]

num_cols = [
    "Month",
    "Day_of_Month",
    "Week_of_Year",
    "Semester_Week",
    "Is_Weekend",
    "Is_Holiday",
    "Is_Exam_Day",
    "Is_College_Event",
    "Total_Students",
    "Expected_Attendance",
    "Attendance_Rate_Expected",
    "Total_Reservations",
    "Hostel_Preorders",
    "Expected_Event_Attendance",
    "Temperature_C",
    "Rainfall_mm",
    "Humidity_Percent",
    "Weather_Severity",
    "Previous_Day_Demand",
    "Demand_Lag_7_Days",
    "Demand_Lag_14_Days",
    "Rolling_7Day_Demand",
]

features = cat_cols + num_cols

# Convert categorical columns for LightGBM
for col in cat_cols:
    df[col] = df[col].astype("category")

# ================================================================
# 3. CHRONOLOGICAL SPLIT & TRAINING
# ================================================================
train_df = df[df["Date"] < "2025-01-01"].copy()
test_df = df[df["Date"] >= "2025-01-01"].copy()

X_train, y_train = train_df[features], train_df[target_col]
X_test, y_test = test_df[features], test_df[target_col]

print("Training LightGBM model...")
model = lgb.LGBMRegressor(
    objective="regression",
    metric="rmse",
    learning_rate=0.05,
    n_estimators=300,
    random_state=42,
    verbose=-1,
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(f"Validation R² Score : {r2_score(y_test, y_pred):.4f}")
print(f"Validation MAE      : {mean_absolute_error(y_test, y_pred):.2f} plates")
print(
    f"Validation MAPE     : {np.mean(np.abs((y_test - y_pred) / y_test)) * 100:.2f}%\n"
)

# Retrain on the full dataset for maximum accuracy in production
print("Fitting model on all available data for production...")
X_full = df[features]
y_full = df[target_col]
production_model = lgb.LGBMRegressor(
    objective="regression",
    metric="rmse",
    learning_rate=0.05,
    n_estimators=300,
    random_state=42,
    verbose=-1,
)
production_model.fit(X_full, y_full)

# ================================================================
# 4. PACKAGE AND CONVERT TO .PKL FORMAT
# ================================================================
pkl_filename = "food_demand_model.pkl"

artifact = {
    "model": production_model,
    "features": features,
    "cat_cols": cat_cols,
    "num_cols": num_cols,
    "target": target_col,
    "version": "1.0.0",
}

with open(pkl_filename, "wb") as f:
    pickle.dump(artifact, f)

print(f"✅ Model artifact successfully saved to: {pkl_filename}")
