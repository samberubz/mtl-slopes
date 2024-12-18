import streamlit as st
import pydeck as pdk
import numpy as np
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor


station_list=["Mont-Tremblant", "Mont Orford", "Mont Sutton"]
num_points_per_side = 10


def generate_coordinates(lat_min, lat_max, lon_min, lon_max, num_points):
    lats = np.linspace(lat_min, lat_max, num_points)
    lons = np.linspace(lon_min, lon_max, num_points)
    return [{"lat": lat, "lon": lon} for lat in lats for lon in lons]


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


coords_tremblant = generate_coordinates(46.18, 46.22, -74.7, -74.5, num_points_per_side)
coords_orford = generate_coordinates(45.33, 45.37, -72.3, -72.05, num_points_per_side)
coords_sutton = generate_coordinates(45.09, 45.13, -72.6, -72.5, num_points_per_side)

# ____________________________________________________________________________________________________
# INTRODUCTION
# Display the image at the top of the page
st.set_page_config(layout="wide")
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
snow_depths_tremblant = [120, 95]  # Replace with your dynamic values
snow_depths_orford = [120, 95]  # Replace with your dynamic values
snow_depths_sutton = [120, 95]  # Replace with your dynamic values
# ____________________________________________________________________________________________________
# MONT-TREMBLANT
st.markdown("<p>_______________________________</p>", unsafe_allow_html=True)
st.markdown("<h1>Tremblant</h1>", unsafe_allow_html=True)
# 1. Table
# st.write("[Website](https://promo.tremblant.ca/hiver/2425/launch/nordik?gad_source=1&gbraid=0AAAAA9foEmpCCkdWThwd9Mx4Z7_dQ_W7E&gclid=Cj0KCQiArby5BhCDARIsAIJvjIT5-wirWVKACD35C4QdO6DeqIbxlShnV4MnYgxYa14A4PO0uLGAphEaAtDJEALw_wcB)")
st.markdown(
    f"""
    <style>
    .tremblant-table {{
        border-collapse: collapse;
        width: 30%; /* Increase the table width */
        min-width: 30px; /* Ensure the table has a minimum width */
        margin: 20px auto; /* Center the table */
        font-family: 'Montserrat', sans-serif;
    }}
    .tremblant-table th, .tremblant-table td {{
        border: 0px solid #ddd; /* Light gray borders */
        padding: 0px; /* Increase padding for more spacious cells */
        text-align: center; /* Center align text */
        min-width: 1px; /* Ensure columns are wide enough */
    }}
    .tremblant-table th {{
        background-color: #f2f2f2; /* Light gray header background */
        color: black;
        font-size: 12px; /* Increase header font size for better readability */
    }}
    .tremblant-table td {{
        font-size: 12px; /* Increase cell font size */
    }}
    .tremblant-table tr:nth-child(even) {{
        background-color: #f9f9f9; /* Light gray for even rows */
    }}
    .tremblant-table tr:hover {{
        background-color: #ddd; /* Highlight on hover */
    }}
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Trails</th>
            <th>Lifts</th>
            <th>Altitude</th>
        </tr>
        <tr>
            <td>102</td>
            <td>14</td>
            <td>875 m</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True
)
st.markdown(
    f"""
    <style>
    .tremblant-table {{
        border-collapse: collapse;
        width: 80%; /* Increase the table width */
        min-width: 100; /* Ensure the table has a minimum width */
        margin: 20px auto; /* Center the table */
        font-family: 'Montserrat', sans-serif;
    }}
    .tremblant-table th, .tremblant-table td {{
        border: 0px solid #ddd; /* Light gray borders */
        padding: 20px; /* Increase padding for more spacious cells */
        text-align: center; /* Center align text */
        min-width: 50px; /* Ensure columns are wide enough */
    }}
    .tremblant-table th {{
        background-color: #f2f2f2; /* Light gray header background */
        color: black;
        font-size: 12px; /* Increase header font size for better readability */
    }}
    .tremblant-table td {{
        font-size: 12px; /* Increase cell font size */
    }}
    .tremblant-table tr:nth-child(even) {{
        background-color: #f9f9f9; /* Light gray for even rows */
    }}
    .tremblant-table tr:hover {{
        background-color: #ddd; /* Highlight on hover */
    }}
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Snow Forecast 24h (cm)</th>
            <th>Snow Forecast 48h (cm)</th>
        </tr>
        <tr>
            <td>{snow_depths_tremblant[0]}</td>
            <td>{snow_depths_tremblant[1]}</td>
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
    radius_pixels=600,  # Adjust the radius of influence of each data point
    intensity=0.37,
    threshold=0.001,
    color_range=[
        [130, 100, 255, 40],
        [110, 80, 255, 110],
        [90, 60, 255, 120],
        [70, 40, 255, 130],
        [60, 20, 230, 140],  # Soft medium purple with more transparency
        [50, 0, 200, 150],  # Medium purple
        [40, 0, 170, 160],
        [30, 0, 140, 170],
        [20, 0, 110, 180],
        [10, 0, 80, 190],  # Dark purple for maximum precipitation with high transparency
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
        min_zoom=11.7,
        interactive=False
    ),
    layers=[layer_tremblant]
)
col1, col2, col3 = st.columns([2, 2, 2])  # Adjust the proportions as needed
with col2:  # Middle column
    st.pydeck_chart(map_tremblant, use_container_width=True)

# ____________________________________________________________________________________________________
# MONT ORFORD
st.markdown("<p>_______________________________</p>", unsafe_allow_html=True)
st.markdown("<h1>Orford</h1>", unsafe_allow_html=True)
# st.write("[Website](https://promo.tremblant.ca/hiver/2425/launch/nordik?gad_source=1&gbraid=0AAAAA9foEmpCCkdWThwd9Mx4Z7_dQ_W7E&gclid=Cj0KCQiArby5BhCDARIsAIJvjIT5-wirWVKACD35C4QdO6DeqIbxlShnV4MnYgxYa14A4PO0uLGAphEaAtDJEALw_wcB)")
st.markdown(
    f"""
    <style>
    .tremblant-table {{
        border-collapse: collapse;
        width: 30%; /* Increase the table width */
        min-width: 30px; /* Ensure the table has a minimum width */
        margin: 20px auto; /* Center the table */
        font-family: 'Montserrat', sans-serif;
    }}
    .tremblant-table th, .tremblant-table td {{
        border: 0px solid #ddd; /* Light gray borders */
        padding: 0px; /* Increase padding for more spacious cells */
        text-align: center; /* Center align text */
        min-width: 1px; /* Ensure columns are wide enough */
    }}
    .tremblant-table th {{
        background-color: #f2f2f2; /* Light gray header background */
        color: black;
        font-size: 12px; /* Increase header font size for better readability */
    }}
    .tremblant-table td {{
        font-size: 12px; /* Increase cell font size */
    }}
    .tremblant-table tr:nth-child(even) {{
        background-color: #f9f9f9; /* Light gray for even rows */
    }}
    .tremblant-table tr:hover {{
        background-color: #ddd; /* Highlight on hover */
    }}
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Trails</th>
            <th>Lifts</th>
            <th>Altitude</th>
        </tr>
        <tr>
            <td>44</td>
            <td>5</td>
            <td>853 m</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True
)
st.markdown(
    f"""
    <style>
    .tremblant-table {{
        border-collapse: collapse;
        width: 80%; /* Increase the table width */
        min-width: 100; /* Ensure the table has a minimum width */
        margin: 20px auto; /* Center the table */
        font-family: 'Montserrat', sans-serif;
    }}
    .tremblant-table th, .tremblant-table td {{
        border: 0px solid #ddd; /* Light gray borders */
        padding: 20px; /* Increase padding for more spacious cells */
        text-align: center; /* Center align text */
        min-width: 50px; /* Ensure columns are wide enough */
    }}
    .tremblant-table th {{
        background-color: #f2f2f2; /* Light gray header background */
        color: black;
        font-size: 12px; /* Increase header font size for better readability */
    }}
    .tremblant-table td {{
        font-size: 12px; /* Increase cell font size */
    }}
    .tremblant-table tr:nth-child(even) {{
        background-color: #f9f9f9; /* Light gray for even rows */
    }}
    .tremblant-table tr:hover {{
        background-color: #ddd; /* Highlight on hover */
    }}
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Snow Forecast 24h (cm)</th>
            <th>Snow Forecast 48h (cm)</th>
        </tr>
        <tr>
            <td>{snow_depths_orford[0]}</td>
            <td>{snow_depths_orford[1]}</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True
)
# 2. Display
layer_orford = pdk.Layer(
    "HeatmapLayer",
    data=data_orford,
    get_position="position",
    get_weight="weight",  # Use the precipitation amount to influence intensity
    radius_pixels=600,  # Adjust the radius of influence of each data point
    intensity=0.37,
    threshold=0.001,
    color_range=[
        [130, 100, 255, 40],
        [110, 80, 255, 110],
        [90, 60, 255, 120],
        [70, 40, 255, 130],
        [60, 20, 230, 140],  # Soft medium purple with more transparency
        [50, 0, 200, 150],  # Medium purple
        [40, 0, 170, 160],
        [30, 0, 140, 170],
        [20, 0, 110, 180],
        [10, 0, 80, 190],  # Dark purple for maximum precipitation with high transparency
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
st.markdown("<p>_______________________________</p>", unsafe_allow_html=True)
st.markdown("<h1>Sutton</h1>", unsafe_allow_html=True)
# st.write("[Website](https://promo.tremblant.ca/hiver/2425/launch/nordik?gad_source=1&gbraid=0AAAAA9foEmpCCkdWThwd9Mx4Z7_dQ_W7E&gclid=Cj0KCQiArby5BhCDARIsAIJvjIT5-wirWVKACD35C4QdO6DeqIbxlShnV4MnYgxYa14A4PO0uLGAphEaAtDJEALw_wcB)")
st.markdown(
    f"""
    <style>
    .tremblant-table {{
        border-collapse: collapse;
        width: 30%; /* Increase the table width */
        min-width: 30px; /* Ensure the table has a minimum width */
        margin: 20px auto; /* Center the table */
        font-family: 'Montserrat', sans-serif;
    }}
    .tremblant-table th, .tremblant-table td {{
        border: 0px solid #ddd; /* Light gray borders */
        padding: 0px; /* Increase padding for more spacious cells */
        text-align: center; /* Center align text */
        min-width: 1px; /* Ensure columns are wide enough */
    }}
    .tremblant-table th {{
        background-color: #f2f2f2; /* Light gray header background */
        color: black;
        font-size: 12px; /* Increase header font size for better readability */
    }}
    .tremblant-table td {{
        font-size: 12px; /* Increase cell font size */
    }}
    .tremblant-table tr:nth-child(even) {{
        background-color: #f9f9f9; /* Light gray for even rows */
    }}
    .tremblant-table tr:hover {{
        background-color: #ddd; /* Highlight on hover */
    }}
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Trails</th>
            <th>Lifts</th>
            <th>Altitude</th>
        </tr>
        <tr>
            <td>60</td>
            <td>9</td>
            <td>962 m</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True
)
st.markdown(
    f"""
    <style>
    .tremblant-table {{
        border-collapse: collapse;
        width: 80%; /* Increase the table width */
        min-width: 100; /* Ensure the table has a minimum width */
        margin: 20px auto; /* Center the table */
        font-family: 'Montserrat', sans-serif;
    }}
    .tremblant-table th, .tremblant-table td {{
        border: 0px solid #ddd; /* Light gray borders */
        padding: 20px; /* Increase padding for more spacious cells */
        text-align: center; /* Center align text */
        min-width: 50px; /* Ensure columns are wide enough */
    }}
    .tremblant-table th {{
        background-color: #f2f2f2; /* Light gray header background */
        color: black;
        font-size: 12px; /* Increase header font size for better readability */
    }}
    .tremblant-table td {{
        font-size: 12px; /* Increase cell font size */
    }}
    .tremblant-table tr:nth-child(even) {{
        background-color: #f9f9f9; /* Light gray for even rows */
    }}
    .tremblant-table tr:hover {{
        background-color: #ddd; /* Highlight on hover */
    }}
    </style>

    <table class="tremblant-table">
        <tr>
            <th>Snow Forecast 24h (cm)</th>
            <th>Snow Forecast 48h (cm)</th>
        </tr>
        <tr>
            <td>{snow_depths_sutton[0]}</td>
            <td>{snow_depths_sutton[1]}</td>
        </tr>
    </table>
    """,
    unsafe_allow_html=True
)
# 2. Display
layer_sutton = pdk.Layer(
    "HeatmapLayer",
    data=data_sutton,
    get_position="position",
    get_weight="weight",  # Use the precipitation amount to influence intensity
    radius_pixels=600,  # Adjust the radius of influence of each data point
    intensity=0.37,
    threshold=0.001,
    color_range=[
        [130, 100, 255, 40],
        [110, 80, 255, 110],
        [90, 60, 255, 120],
        [70, 40, 255, 130],
        [60, 20, 230, 140],  # Soft medium purple with more transparency
        [50, 0, 200, 150],  # Medium purple
        [40, 0, 170, 160],
        [30, 0, 140, 170],
        [20, 0, 110, 180],
        [10, 0, 80, 190],  # Dark purple for maximum precipitation with high transparency
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
