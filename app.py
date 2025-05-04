'''
import streamlit as st
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from streamlit_echarts import st_echarts

# --- Load Dataset ---
@st.cache_data
def load_data():
    df = pd.read_csv("recipes.csv")
    df = df.dropna(subset=["Calories", "FatContent", "ProteinContent", "CarbohydrateContent"])
    df = df.astype({"Calories": float, "FatContent": float, "ProteinContent": float, "CarbohydrateContent": float})
    return df

df = load_data()

# --- BMI and BMR ---
st.title("🍽️ Personalized Diet Planner")

with st.sidebar:
    st.header("📊 Your Details")
    age = st.number_input("Age", 10, 100, 25)
    gender = st.selectbox("Gender", ["Male", "Female"])
    height = st.number_input("Height (cm)", 100, 250, 170)
    weight = st.number_input("Weight (kg)", 30, 200, 70)
    activity = st.selectbox("Activity Level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
    meal_count = st.slider("Meals per day", 1, 5, 3)

# --- BMI, BMR, Calorie Goal ---
bmi = weight / ((height / 100) ** 2)
bmr = (10 * weight + 6.25 * height - 5 * age + (5 if gender == "Male" else -161))

activity_multiplier = {
    "Sedentary": 1.2, "Lightly Active": 1.375,
    "Moderately Active": 1.55, "Very Active": 1.725
}
calorie_goal = bmr * activity_multiplier[activity]
calories_per_meal = calorie_goal / meal_count

st.subheader("📌 BMI & Calorie Goal")
st.markdown(f"**Your BMI**: {bmi:.2f} | **Daily Calorie Goal**: {calorie_goal:.0f} kcal")
st.markdown(f"**Calories per Meal**: ~{calories_per_meal:.0f} kcal")

# --- Recommend KNN recipes per meal ---
nutrient_cols = ["Calories"]
knn = NearestNeighbors(n_neighbors=5)
knn.fit(df[nutrient_cols])
distances, indices = knn.kneighbors([[calories_per_meal]])

recommended = df.iloc[indices[0]]
selected_recipes = {}

# --- Format time function ---
def format_time(time_value):
    # Check if the value is a string in ISO 8601 format or a numeric value
    if isinstance(time_value, str):
        # Handle the ISO 8601 format
        return time_value.replace("PT", "").replace("M", " minutes")
    elif isinstance(time_value, (int, float)):
        # For numeric values, just return it as minutes
        return f"{time_value} minutes"
    return "N/A"

st.subheader("🥗 Recommended Recipes")

for i, row in recommended.iterrows():
    with st.expander(f"🍴 {row['Name']}"):
        st.markdown(f"**Description**: {row['Description']}")
        
        # Format cook, prep, and total time
        cook_time = format_time(row['CookTime'])
        prep_time = format_time(row['PrepTime'])
        total_time = format_time(row['TotalTime'])
        
        st.markdown(f"**Cook Time**: {cook_time}, **Prep Time**: {prep_time}, **Total Time**: {total_time}")

        # Ingredients - Displaying as a bullet list
        st.markdown("#### Ingredients")
        ingredients = row["RecipeIngredientParts"]
        ingredients_list = ingredients.strip("c()").replace('"', '').split(", ")
        for ingredient in ingredients_list:
            st.markdown(f"- {ingredient}")
        
        st.markdown("#### Nutrition Info (per serving)")
        # Nutrition Info Table - Fixing format and displaying properly
        nutrition_data = {
            "Calories": [row["Calories"]],
            "Fat (g)": [row["FatContent"]],
            "Protein (g)": [row["ProteinContent"]],
            "Carbs (g)": [row["CarbohydrateContent"]],
        }
        st.dataframe(pd.DataFrame(nutrition_data), use_container_width=True)

        choice = st.selectbox(f"Add to Today’s Meal Plan?", ["No", "Yes"], key=f"select_{i}")
        if choice == "Yes":
            selected_recipes[row["Name"]] = row

# --- User Summary ---
if selected_recipes:
    st.subheader("📋 Selected Recipes Summary")

    total_cals = sum([r["Calories"] for r in selected_recipes.values()])
    total_fat = sum([r["FatContent"] for r in selected_recipes.values()])
    total_protein = sum([r["ProteinContent"] for r in selected_recipes.values()])
    total_carbs = sum([r["CarbohydrateContent"] for r in selected_recipes.values()])

    st.markdown(f"**Total Calories Chosen**: {total_cals:.0f} kcal vs Goal: {calorie_goal:.0f} kcal")

    # --- Bar Chart ---
    st_echarts({
        "title": {"text": "Calories vs Goal"},
        "tooltip": {},
        "xAxis": {"type": "category", "data": ["Selected", "Goal"]},
        "yAxis": {"type": "value"},
        "series": [{
            "data": [round(total_cals, 1), round(calorie_goal, 1)],
            "type": "bar",
            "color": "#91cc75"
        }]
    }, height="300px")

    # --- Pie Chart ---
    st_echarts({
        "title": {"text": "Nutrition Breakdown", "left": "center"},
        "tooltip": {"trigger": "item"},
        "series": [{
            "type": "pie",
            "radius": "60%",
            "data": [
                {"value": round(total_fat, 1), "name": "Fat"},
                {"value": round(total_protein, 1), "name": "Protein"},
                {"value": round(total_carbs, 1), "name": "Carbohydrates"}
            ]
        }]
    }, height="400px")
else:
    st.info("No meals selected yet.")

'''


import streamlit as st
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from streamlit_echarts import st_echarts

# --- Load Dataset ---
@st.cache_data
def load_data():
    df = pd.read_csv("recipes.csv")
    df = df.dropna(subset=["Calories", "FatContent", "ProteinContent", "CarbohydrateContent"])
    df = df.astype({
        "Calories": float,
        "FatContent": float,
        "ProteinContent": float,
        "CarbohydrateContent": float
    })
    return df

df = load_data()

# --- Title ---
st.title("🍽️ Personalized Diet Planner")

# --- Session State ---
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "selected_recipes" not in st.session_state:
    st.session_state.selected_recipes = {}

# --- Sidebar: User Inputs ---
with st.sidebar:
    st.header("📊 Your Details")
    age = st.number_input("Age", 10, 100, 25)
    gender = st.selectbox("Gender", ["Male", "Female"])
    height = st.number_input("Height (cm)", 100, 250, 170)
    weight = st.number_input("Weight (kg)", 30, 200, 70)
    activity = st.selectbox("Activity Level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
    meal_count = st.slider("Meals per day", 1, 5, 3)

    if st.button("Submit"):
        st.session_state.submitted = True
        st.session_state.selected_recipes = {}  # Clear old selections on new submission

# --- Proceed only if submitted ---
if st.session_state.submitted:
    bmi = weight / ((height / 100) ** 2)
    bmr = (10 * weight + 6.25 * height - 5 * age + (5 if gender == "Male" else -161))

    activity_multiplier = {
        "Sedentary": 1.2, "Lightly Active": 1.375,
        "Moderately Active": 1.55, "Very Active": 1.725
    }
    calorie_goal = bmr * activity_multiplier[activity]
    calories_per_meal = calorie_goal / meal_count

    # --- BMI Category ---
    if bmi < 18.5:
        bmi_status = "Underweight"
    elif 18.5 <= bmi < 24.9:
        bmi_status = "Normal weight"
    elif 25 <= bmi < 29.9:
        bmi_status = "Overweight"
    else:
        bmi_status = "Obese"

    # --- BMI Display ---
    st.subheader("📌 BMI & Calorie Goal")
    st.markdown(f"**Your BMI**: {bmi:.2f} ({bmi_status}) | **Daily Calorie Goal**: {calorie_goal:.0f} kcal")
    st.markdown(f"**Calories per Meal**: ~{calories_per_meal:.0f} kcal")

    # --- KNN Recipe Recommendation ---
    nutrient_cols = ["Calories"]
    knn = NearestNeighbors(n_neighbors=5)
    knn.fit(df[nutrient_cols])
    distances, indices = knn.kneighbors([[calories_per_meal]])

    recommended = df.iloc[indices[0]]

    st.subheader("🥗 Recommended Recipes")

    # --- Format time function ---
    def format_time(time_value):
        if isinstance(time_value, str):
            return time_value.replace("PT", "").replace("M", " minutes")
        elif isinstance(time_value, (int, float)):
            return f"{time_value} minutes"
        return "N/A"

    for i, row in recommended.iterrows():
        with st.expander(f"🍴 {row['Name']}"):
            st.markdown(f"**Description**: {row['Description']}")
            st.markdown(f"**Cook Time**: {format_time(row['CookTime'])}, **Prep Time**: {format_time(row['PrepTime'])}, **Total Time**: {format_time(row['TotalTime'])}")

            st.markdown("#### Ingredients")
            ingredients = row["RecipeIngredientParts"]
            ingredients_list = ingredients.strip("c()").replace('"', '').split(", ")
            for ingredient in ingredients_list:
                st.markdown(f"- {ingredient}")

            st.markdown("#### Nutrition Info (per serving)")
            nutrition_data = {
                "Calories": [row["Calories"]],
                "Fat (g)": [row["FatContent"]],
                "Protein (g)": [row["ProteinContent"]],
                "Carbs (g)": [row["CarbohydrateContent"]],
            }
            st.dataframe(pd.DataFrame(nutrition_data), use_container_width=True)

            choice = st.selectbox(f"Add to Today’s Meal Plan?", ["No", "Yes"], key=f"select_{i}")
            if choice == "Yes":
                st.session_state.selected_recipes[row["Name"]] = row

    # --- Summary ---
    if st.session_state.selected_recipes:
        st.subheader("📋 Selected Recipes Summary")

        total_cals = sum([r["Calories"] for r in st.session_state.selected_recipes.values()])
        total_fat = sum([r["FatContent"] for r in st.session_state.selected_recipes.values()])
        total_protein = sum([r["ProteinContent"] for r in st.session_state.selected_recipes.values()])
        total_carbs = sum([r["CarbohydrateContent"] for r in st.session_state.selected_recipes.values()])

        st.markdown(f"**Total Calories Chosen**: {total_cals:.0f} kcal vs Goal: {calorie_goal:.0f} kcal")

        # --- Bar Chart ---
        st_echarts({
            "title": {"text": "Calories vs Goal"},
            "tooltip": {},
            "xAxis": {"type": "category", "data": ["Selected", "Goal"]},
            "yAxis": {"type": "value"},
            "series": [{
                "data": [round(total_cals, 1), round(calorie_goal, 1)],
                "type": "bar",
                "color": "#91cc75"
            }]
        }, height="300px")

        # --- Pie Chart ---
        st_echarts({
            "title": {"text": "Nutrition Breakdown", "left": "center"},
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "pie",
                "radius": "60%",
                "data": [
                    {"value": round(total_fat, 1), "name": "Fat"},
                    {"value": round(total_protein, 1), "name": "Protein"},
                    {"value": round(total_carbs, 1), "name": "Carbohydrates"}
                ]
            }]
        }, height="400px")
    else:
        st.info("No meals selected yet.")
else:
    st.warning("⚠️ Please enter your details and click 'Submit' to get personalized results.")
