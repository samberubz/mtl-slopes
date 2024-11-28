import streamlit as st
import pydeck as pdk
import numpy as np
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from io import BytesIO

station_list=["Mont-Tremblant", "Mont Orford", "Mont Sutton"]
num_points_per_side = 6


def generate_coordinates(lat_min, lat_max, lon_min, lon_max, num_points):
    lats = np.linspace(lat_min, lat_max, num_points)
    lons = np.linspace(lon_min, lon_max, num_points)
    return [{"lat": lat, "lon": lon} for lat in lats for lon in lons]


coords_tremblant = generate_coordinates(46.18, 46.22, -74.60, -74.52, num_points_per_side)
coords_orford = generate_coordinates(45.33, 45.37, -72.18, -72.10, num_points_per_side)
coords_sutton = generate_coordinates(45.09, 45.13, -72.65, -72.57, num_points_per_side)


# Function to fetch forecast data
def fetch_forecast(lat, lon, forecast_hours, selected_type):
    forecast_hours = [forecast_hours]
    data_type_mapping = {
        "Snowfall": "snowfall",
        "Rainfall": "rain",
        "Total Precipitation": "precipitation",
    }
    api_param = data_type_mapping.get(selected_type)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={api_param}&timezone=auto"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        hourly = data.get("hourly", {})
        times = pd.to_datetime(hourly.get("time", []))
        values = hourly.get(api_param, [])
        # Filter data for the requested forecast hours
        df = pd.DataFrame({"time": times, selected_type: values})
        df["forecast_hour"] = (df["time"] - df["time"].min()).dt.total_seconds() // 3600
        # Compute cumulative values explicitly
        df[selected_type] = df[selected_type].cumsum()  # Make values cumulative
        # Calculate cumulative values for the requested forecast hours
        cumulative_df = (
            df[df["forecast_hour"] <= forecast_hours[0]]  # Filter for up to the requested hours
            .groupby("forecast_hour", as_index=False)  # Group by forecast hour
            .agg({selected_type: "sum"})  # Cumulative sum
        )
        # Assign coordinates and return
        cumulative_df["lat"] = lat
        cumulative_df["lon"] = lon
        return cumulative_df


def fetch_all_forecasts(coords, forecast_hours, selected_type):
    with ThreadPoolExecutor() as executor:
        results = list(
            executor.map(
                lambda coord: fetch_forecast(coord["lat"], coord["lon"], forecast_hours, selected_type),
                coords
            )
        )
    return [res for res in results if res is not None and not res.empty]


# ____________________________________________________________________________________________________
# INTRODUCTION
st.set_page_config(layout="wide")
# Display the image at the top of the page
cola, colb, colc = st.columns([2, 2, 2])
with colb:
    st.image("Capture1.png", use_container_width="True")
st.markdown(
    """
    <style>
    /* Load Montserrat font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

    /* Change background color */
    .stApp {
        background-color: #fcfdfd; /* Choose your color here */
    }

    /* Apply Montserrat font and center content */
    h1, p {
        font-family: 'Montserrat', sans-serif; /* Apply Montserrat font */
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("     **Welcome !**")
st.write("Hey Skiers, this app was designed for you! :skier::snow_capped_mountain:")
st.write("It gathers snow forecasts for three well-known ski stations, making it your perfect destination before hitting the slopes! :car:")

st.write("")
# ____________________________________________________________________________________________________
# PARAMETERS
# 1. Slider
st.markdown(
    """
    <h5 style="text-align: center; padding-bottom: 0px; margin-bottom: -5px;">Select Forecast Time</h5>
    """,
    unsafe_allow_html=True)
st.markdown(
    """
    <h5 style="text-align: center; padding-bottom: -50px; margin-bottom: -100px;">[6 to 48 hours]</h5>
    """,
    unsafe_allow_html=True)
st.markdown("""
    <style>
    .stSlider [data-baseweb=slider]{
        width: 80%;
        margin: auto; /* Center slider horizontally */
        margin-top: -30px;
        padding-top: -50px;
        padding-bottom: 15px;
    }
        .stSlider [role="slider"] {
        background: linear-gradient(90deg, #FFA500, #FF0000); /* Orange to red gradient */
        border-radius: 50%; /* Round handle */
        height: 20px; /* Increase handle size */
        width: 20px;
    }
    .stSlider [role="slider"]:hover {
        transform: scale(1.2); /* Enlarge on hover */
        box-shadow: 0 0 30px rgba(33, 150, 243, 0.8); /* Add glow on hover */
    }
    .stSlider [data-testid="stSliderTrack"] > div {
        background-color: #4b0082; /* Dark purple line */
        height: 8px; /* Make track thicker */
        border-radius: 5px; /* Round track ends */
    }
    .stSlider div[data-testid="stMarkdownContainer"] {
        color: #4b0082; /* Dark purple text */
        font-weight: bold; /* Make it bold for better visibility */
    }
    </style>
    """,
            unsafe_allow_html=True)
forecast_hours = st.slider(
    "",
    min_value=6,
    max_value=48,
    step=6,
    help=""
)
# 2. Toggle Buttons
st.markdown(
    """
    <style>
    /* Center the radio button container horizontally and vertically */
    .stRadio {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 6vh;  /* Make it take the full height of the viewport */
    }

    .stRadio > div {
        display: flex;
        justify-content: center; /* Center the buttons side by side */
        gap: 5px; /* Space between the buttons */
    }
    .stRadio label {
        font-family: 'Montserrat', sans-serif; /* Match your app's font */
        font-size: 16px;
        margin: 0; /* Remove unnecessary margins */
        padding: 4px 20px; /* Add padding for a button-like appearance */
        border-radius: 20px; /* Make it look like pills */
        background-color: #f0f2f5; /* Light gray background */
        color: #000; /* Black text */
        cursor: pointer; /* Pointer cursor */
        transition: all 0.3s ease-in-out; /* Smooth hover effect */
        text-align: center; /* Center the text inside the button */
    }
    .stRadio label:hover {
        background-color: #e0e4ea; /* Slightly darker background on hover */
    }
    .stRadio label[data-selected="true"] {
        background-color: #4CAF50; /* Green for selected option */
        color: white; /* White text for better contrast */
    }
    </style>
    """,
    unsafe_allow_html=True)
selected_type = st.radio(
    "Type",  # Label for accessibility (invisible)
    options=["Snowfall", "Rainfall", "Total Precipitation"],
    index=0,
    label_visibility="collapsed"  # Hide the label
)
st.markdown('</div>', unsafe_allow_html=True)  # Close container

# ____________________________________________________________________________________________________
# DATA
# Fetch forecasts for all coordinates
for station in station_list:
    forecast_data = []
    if station == "Mont-Tremblant":
        forecast_data = fetch_all_forecasts(coords_tremblant, forecast_hours, selected_type)
        if forecast_data:
            data_tremblant = pd.concat(forecast_data, ignore_index=True)
            # Use only the row corresponding to the selected cumulative hour
            data_tremblant = data_tremblant[data_tremblant["forecast_hour"] <= forecast_hours]
        else:
            data_tremblant = pd.DataFrame()
        data_tremblant["weight"] = data_tremblant[selected_type]
        data_tremblant["weight"] = data_tremblant["weight"] / data_tremblant["weight"].max()
        data_tremblant["position"] = data_tremblant[["lon", "lat"]].values.tolist()
        data_tremblant["position"] = data_tremblant.apply(
            lambda row: [row["lon"], row["lat"]], axis=1
        )
    elif station == "Mont Orford":
        forecast_data = fetch_all_forecasts(coords_orford, forecast_hours, selected_type)
        if forecast_data:
            data_orford = pd.concat(forecast_data, ignore_index=True)
            # Use only the row corresponding to the selected cumulative hour
            data_orford = data_orford[data_orford["forecast_hour"] <= forecast_hours]
        else:
            data_orford = pd.DataFrame()
        data_orford["weight"] = data_orford[selected_type]
        data_orford["weight"] = data_orford["weight"] / data_orford["weight"].max()
        data_orford["position"] = data_orford[["lon", "lat"]].values.tolist()
        data_orford["position"] = data_orford.apply(
            lambda row: [row["lon"], row["lat"]], axis=1
        )
    elif station == "Mont Sutton":
        forecast_data = fetch_all_forecasts(coords_sutton, forecast_hours, selected_type)
        if forecast_data:
            data_sutton = pd.concat(forecast_data, ignore_index=True)
            # Use only the row corresponding to the selected cumulative hour
            data_sutton = data_sutton[data_sutton["forecast_hour"] <= forecast_hours]
        else:
            data_sutton = pd.DataFrame()
        data_sutton["weight"] = data_sutton[selected_type]
        data_sutton["weight"] = data_sutton["weight"] / data_sutton["weight"].max()
        data_sutton["position"] = data_sutton[["lon", "lat"]].values.tolist()
        data_sutton["position"] = data_sutton.apply(
            lambda row: [row["lon"], row["lat"]], axis=1
        )

# ____________________________________________________________________________________________________
# MONT-TREMBLANT
st.markdown("<p>___________________</p>", unsafe_allow_html=True)
st.markdown("<h1>Mont-Tremblant</h1>", unsafe_allow_html=True)
# 1. Table
# st.write("[Website](https://promo.tremblant.ca/hiver/2425/launch/nordik?gad_source=1&gbraid=0AAAAA9foEmpCCkdWThwd9Mx4Z7_dQ_W7E&gclid=Cj0KCQiArby5BhCDARIsAIJvjIT5-wirWVKACD35C4QdO6DeqIbxlShnV4MnYgxYa14A4PO0uLGAphEaAtDJEALw_wcB)")
st.markdown(
    """
    <style>
    .tremblant-table {
        border-collapse: separate;
        border-spacing: 0;
        width: 35%;
        margin: auto;
        font-family: 'Montserrat', sans-serif;
    }
    .tremblant-table th, .tremblant-table td {
        border: 0px; /* Gray borders */
        border-radius: 0px; /* Rounded corners */
        padding: 10px;
        text-align: center;
    }
    .tremblant-table th:first-child, .tremblant-table td:first-child {
        border-top-left-radius: 2px;
        border-bottom-left-radius: 2px;
    }
    .tremblant-table th:last-child, .tremblant-table td:last-child {
        border-top-right-radius: 2px;
        border-bottom-right-radius: 2px;
    }
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Altitude</th>
            <th>Trails</th>
            <th>Slopes</th>
            <th>Lifts</th>
        </tr>
        <tr>
            <td>875 m</td>
            <td>102</td>
            <td>4</td>
            <td>14</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True
)
# 2. Display
layer_tremblant = pdk.Layer(
    "HeatmapLayer",
    data=data_tremblant,
    get_position="position",
    get_weight="weight",  # Use the precipitation amount to influence intensity
    radius_pixels=300,  # Adjust the radius of influence of each data point
    intensity=0.4,
    threshold=0.001,
    color_range=[
        [198, 229, 255, 160],  # Light blue for low precipitation
        [135, 206, 250, 220],  # Sky blue for slightly higher
        [0, 43, 226, 300],  # Blue-violet for intense precipitation
        [0, 0, 130, 300]  # Dark purple for maximum precipitation
    ]
)
map_tremblant = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v10",
    initial_view_state=pdk.ViewState(
        latitude=46.23,
        longitude=-74.559444,
        zoom=11.7,  # Set fixed zoom level
        pitch=50,
        bearing=0,
        max_zoom=11.7,
        min_zoom=11.7
    ),
    layers=[layer_tremblant]
)
col1, col2, col3 = st.columns([2, 2, 2])  # Adjust the proportions as needed
with col2:  # Middle column
    st.pydeck_chart(map_tremblant, use_container_width=True)

# ____________________________________________________________________________________________________
# MONT ORFORD
st.markdown("<p>___________________</p>", unsafe_allow_html=True)
st.markdown("<h1>Mont Orford</h1>", unsafe_allow_html=True)
# st.write("[Website](https://promo.tremblant.ca/hiver/2425/launch/nordik?gad_source=1&gbraid=0AAAAA9foEmpCCkdWThwd9Mx4Z7_dQ_W7E&gclid=Cj0KCQiArby5BhCDARIsAIJvjIT5-wirWVKACD35C4QdO6DeqIbxlShnV4MnYgxYa14A4PO0uLGAphEaAtDJEALw_wcB)")
st.markdown(
    """
    <style>
    .tremblant-table {
        border-collapse: separate;
        border-spacing: 0;
        width: 30%;
        margin: 0 auto;
        font-family: 'Montserrat', sans-serif;
    }
    .tremblant-table th, .tremblant-table td {
        border: 0px; /* Gray borders */
        border-radius: 0px; /* Rounded corners */
        padding: 0px;
        text-align: center;
    }
    .tremblant-table th:first-child, .tremblant-table td:first-child {
        border-top-left-radius: 2px;
        border-bottom-left-radius: 2px;
    }
    .tremblant-table th:last-child, .tremblant-table td:last-child {
        border-top-right-radius: 2px;
        border-bottom-right-radius: 2px;
    }
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Altitude</th>
            <th>Trails</th>
            <th>Slopes</th>
            <th>Lifts</th>
        </tr>
        <tr>
            <td>853 m</td>
            <td>44</td>
            <td>4</td>
            <td>5</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True)
# 2. Display
layer_orford = pdk.Layer(
    "HeatmapLayer",
    data=data_orford,
    get_position="position",
    get_weight="weight",  # Use the precipitation amount to influence intensity
    radius_pixels=300,  # Adjust the radius of influence of each data point
    intensity=0.4,
    threshold=0.001,
    color_range=[
        [198, 229, 255, 160],  # Light blue for low precipitation
        [135, 206, 250, 220],  # Sky blue for slightly higher
        [0, 43, 226, 300],  # Blue-violet for intense precipitation
        [0, 0, 130, 300]  # Dark purple for maximum precipitation
    ]
)
map_orford = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v10",
    initial_view_state=pdk.ViewState(
        latitude=45.35,
        longitude=-72.14,
        zoom=11.7,  # Set fixed zoom level
        pitch=50,
        bearing=0,
        max_zoom=11.7,
        min_zoom=11.7
    ),
    layers=[layer_orford]
)
col1, col2, col3 = st.columns([2, 2, 2])  # Adjust the proportions as needed
with col2:  # Middle column
    st.pydeck_chart(map_orford, use_container_width=True)

# ____________________________________________________________________________________________________
# MONT SUTTON
st.markdown("<p>___________________</p>", unsafe_allow_html=True)
st.markdown("<h1>Mont Sutton</h1>", unsafe_allow_html=True)
# st.write("[Website](https://promo.tremblant.ca/hiver/2425/launch/nordik?gad_source=1&gbraid=0AAAAA9foEmpCCkdWThwd9Mx4Z7_dQ_W7E&gclid=Cj0KCQiArby5BhCDARIsAIJvjIT5-wirWVKACD35C4QdO6DeqIbxlShnV4MnYgxYa14A4PO0uLGAphEaAtDJEALw_wcB)")
st.markdown(
    """
    <style>
    .tremblant-table {
        border-collapse: separate;
        border-spacing: 0;
        width: 30%;
        margin: 0 auto;
        font-family: 'Montserrat', sans-serif;
    }
    .tremblant-table th, .tremblant-table td {
        border: 0px; /* Gray borders */
        border-radius: 0px; /* Rounded corners */
        padding: 0px;
        text-align: center;
    }
    .tremblant-table th:first-child, .tremblant-table td:first-child {
        border-top-left-radius: 2px;
        border-bottom-left-radius: 2px;
    }
    .tremblant-table th:last-child, .tremblant-table td:last-child {
        border-top-right-radius: 2px;
        border-bottom-right-radius: 2px;
    }
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Altitude</th>
            <th>Trails</th>
            <th>Slope</th>
            <th>Lifts</th>
        </tr>
        <tr>
            <td>962 m</td>
            <td>60</td>
            <td>1</td>
            <td>9</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True)
# 2. Display
layer_sutton = pdk.Layer(
    "HeatmapLayer",
    data=data_sutton,
    get_position="position",
    get_weight="weight",  # Use the precipitation amount to influence intensity
    radius_pixels=300,  # Adjust the radius of influence of each data point
    intensity=0.4,
    threshold=0.001,
    color_range=[
        [198, 229, 255, 160],  # Light blue for low precipitation
        [135, 206, 250, 220],  # Sky blue for slightly higher
        [0, 43, 226, 300],  # Blue-violet for intense precipitation
        [0, 0, 130, 300]  # Dark purple for maximum precipitation
    ]
)
map_sutton = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v10",
    initial_view_state=pdk.ViewState(
        latitude=45.11,
        longitude=-72.61,
        zoom=11.7,  # Set fixed zoom level
        pitch=50,
        bearing=0,
        max_zoom=11.7,
        min_zoom=11.7
    ),
    layers=[layer_sutton]
)
col1, col2, col3 = st.columns([2, 2, 2])  # Adjust the proportions as needed
with col2:  # Middle column
    st.pydeck_chart(map_sutton, use_container_width=True)


st.markdown("   ", unsafe_allow_html=True)
st.markdown("   ", unsafe_allow_html=True)
colx, coly, colz = st.columns([2, 2, 2])
with coly:
    st.image("Capture1.png", use_container_width="True")
st.markdown("<p>©2024, Samuel Bérubé, P.Eng., M.A.Sc.</p>", unsafe_allow_html=True)
