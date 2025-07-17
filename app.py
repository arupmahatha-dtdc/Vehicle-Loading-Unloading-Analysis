import streamlit as st
import math
from unit_converter import UnitConverter
import pandas as pd
import plotly.graph_objects as go

# Vehicle data from sample
VEHICLES = [
    {"type": "40 ft ODC Trailer / Container", "L": 40, "B": 8, "H": 9, "Payload": 32000},
    {"type": "32 ft Container SXL", "L": 32, "B": 8, "H": 9, "Payload": "7000 to 9000"},
    {"type": "32 ft Container MXL", "L": 32, "B": 8, "H": 9, "Payload": "14000 to 18000"},
    {"type": "24 ft Box/Container Truck", "L": 24, "B": 8, "H": 9, "Payload": "7500 to 16000"},
    {"type": "Tata 22 ft Container", "L": 22, "B": 8, "H": 8, "Payload": 10000},
    {"type": "Eicher 19 ft", "L": 19, "B": 7, "H": 8, "Payload": "10491 to 10631"},
    {"type": "Eicher 17 ft", "L": 17, "B": 6, "H": 8, "Payload": "4300 to 13300"},
    {"type": "Eicher 14 ft (LCV)", "L": 14, "B": 6, "H": 8, "Payload": "4015 to 4120"},
    {"type": "Tata Super Ace", "L": 14, "B": 5, "H": 6, "Payload": 1000},
    {"type": "Tata Ace / Dost", "L": 12, "B": 5, "H": 6, "Payload": "600 to 1100"},
    {"type": "Tata 407 / Dost Bada", "L": 9, "B": 6, "H": 6, "Payload": "2250 to 2500"},
    {"type": "Mahindra Bolero Pickup", "L": 8, "B": 5, "H": 6, "Payload": 1010},
]

# Default parcel dimensions (ft)
DEFAULT_PARCEL_L = 1.25
DEFAULT_PARCEL_B = 1.0
DEFAULT_PARCEL_H = 1.0

# Worker/operation parameters (defaults)
DEFAULT_SPEED_WITHOUT_LOAD = 0.9  # m/s
DEFAULT_SPEED_WITH_LOAD = 0.67    # m/s
DEFAULT_UNLOADING_DELAY = 10.21   # s
DEFAULT_LOADING_DELAY = 13.8      # s
DEFAULT_FATIGUE_RATIO = 0.8833333333
DEFAULT_TIME_MULTIPLIER = 1.13

def format_hours(h):
    hours = int(h)
    minutes = int(round((h - hours) * 60))
    return f"{hours}h {minutes}m"

st.title("Vehicle Loading/Unloading Analysis")

if 'vehicle_configs' not in st.session_state:
    st.session_state['vehicle_configs'] = [
        {
            'id': 0,
            'type': VEHICLES[0]['type'],
            'L': VEHICLES[0]['L'],
            'B': VEHICLES[0]['B'],
            'H': VEHICLES[0]['H'],
            'Payload': VEHICLES[0]['Payload'],
            'PARCEL_L': DEFAULT_PARCEL_L,
            'PARCEL_B': DEFAULT_PARCEL_B,
            'PARCEL_H': DEFAULT_PARCEL_H,
            'SPEED_WITHOUT_LOAD': DEFAULT_SPEED_WITHOUT_LOAD,
            'SPEED_WITH_LOAD': DEFAULT_SPEED_WITH_LOAD,
            'UNLOADING_DELAY': DEFAULT_UNLOADING_DELAY,
            'LOADING_DELAY': DEFAULT_LOADING_DELAY,
            'FATIGUE_RATIO': DEFAULT_FATIGUE_RATIO,
            'TIME_MULTIPLIER': DEFAULT_TIME_MULTIPLIER,
        }
    ]
    st.session_state['next_id'] = 1

# Add Vehicle button
if st.button("Add Vehicle"):
    st.session_state['vehicle_configs'].append({
        'id': st.session_state['next_id'],
        'type': VEHICLES[0]['type'],
        'L': VEHICLES[0]['L'],
        'B': VEHICLES[0]['B'],
        'H': VEHICLES[0]['H'],
        'Payload': VEHICLES[0]['Payload'],
        'PARCEL_L': DEFAULT_PARCEL_L,
        'PARCEL_B': DEFAULT_PARCEL_B,
        'PARCEL_H': DEFAULT_PARCEL_H,
        'SPEED_WITHOUT_LOAD': DEFAULT_SPEED_WITHOUT_LOAD,
        'SPEED_WITH_LOAD': DEFAULT_SPEED_WITH_LOAD,
        'UNLOADING_DELAY': DEFAULT_UNLOADING_DELAY,
        'LOADING_DELAY': DEFAULT_LOADING_DELAY,
        'FATIGUE_RATIO': DEFAULT_FATIGUE_RATIO,
        'TIME_MULTIPLIER': DEFAULT_TIME_MULTIPLIER,
    })
    st.session_state['next_id'] += 1

# Remove vehicle logic
remove_ids = []

vehicle_configs = st.session_state['vehicle_configs']
num_vehicles = len(vehicle_configs)
cols = st.columns(num_vehicles)
results = []

for idx, config in enumerate(vehicle_configs):
    with cols[idx]:
        st.markdown(f"### Vehicle {idx+1}")
        # Remove button (don't show if only one config)
        if num_vehicles > 1:
            if st.button(f"Remove", key=f"remove_{config['id']}"):
                remove_ids.append(config['id'])
        # Vehicle selection
        types = [v["type"] for v in VEHICLES]
        prev_type = config.get('prev_type', config['type'])
        selected_type = st.selectbox("Select Vehicle Type", types, index=types.index(config['type']), key=f"type_{config['id']}")
        config['type'] = selected_type
        defaults = next(v for v in VEHICLES if v["type"] == config['type'])
        # If vehicle type changed, update ALL fields to defaults
        if config['type'] != prev_type:
            config['L'] = defaults['L']
            config['B'] = defaults['B']
            config['H'] = defaults['H']
            config['Payload'] = defaults['Payload']
            config['PARCEL_L'] = DEFAULT_PARCEL_L
            config['PARCEL_B'] = DEFAULT_PARCEL_B
            config['PARCEL_H'] = DEFAULT_PARCEL_H
            config['SPEED_WITHOUT_LOAD'] = DEFAULT_SPEED_WITHOUT_LOAD
            config['SPEED_WITH_LOAD'] = DEFAULT_SPEED_WITH_LOAD
            config['UNLOADING_DELAY'] = DEFAULT_UNLOADING_DELAY
            config['LOADING_DELAY'] = DEFAULT_LOADING_DELAY
            config['FATIGUE_RATIO'] = DEFAULT_FATIGUE_RATIO
            config['TIME_MULTIPLIER'] = DEFAULT_TIME_MULTIPLIER
        config['prev_type'] = config['type']
        config['L'] = st.number_input("L (ft)", value=float(config['L']), key=f"L_{config['id']}")
        config['B'] = st.number_input("B (ft)", value=float(config['B']), key=f"B_{config['id']}")
        config['H'] = st.number_input("H (ft)", value=float(config['H']), key=f"H_{config['id']}")
        if isinstance(defaults["Payload"], str) and "to" in str(defaults["Payload"]):
            parts = str(defaults["Payload"]).replace(" ", "").split("to")
            payload_min = float(parts[0])
            payload_max = float(parts[1])
            # If type changed, set to min of new range
            if config['type'] != prev_type:
                config['Payload'] = payload_min
            config['Payload'] = st.slider("Payload (kg)", min_value=payload_min, max_value=payload_max, value=float(config['Payload']) if isinstance(config['Payload'], (int, float)) else payload_min, step=10.0, key=f"Payload_{config['id']}")
        else:
            config['Payload'] = st.number_input("Payload (kg)", value=float(config['Payload']), key=f"Payload_{config['id']}")
        st.markdown("---")
        st.subheader("Parcel Assumptions")
        config['PARCEL_L'] = st.number_input("Parcel Length (ft)", value=float(config['PARCEL_L']), key=f"PARCEL_L_{config['id']}")
        config['PARCEL_B'] = st.number_input("Parcel Breadth (ft)", value=float(config['PARCEL_B']), key=f"PARCEL_B_{config['id']}")
        config['PARCEL_H'] = st.number_input("Parcel Height (ft)", value=float(config['PARCEL_H']), key=f"PARCEL_H_{config['id']}")
        st.markdown("---")
        st.subheader("Worker & Operation Parameters")
        config['SPEED_WITHOUT_LOAD'] = st.number_input("Worker's Average Speed without Load (m/s)", value=float(config['SPEED_WITHOUT_LOAD']), key=f"SPEED_WITHOUT_LOAD_{config['id']}")
        config['SPEED_WITH_LOAD'] = st.number_input("Worker's Average Speed with Load (m/s)", value=float(config['SPEED_WITH_LOAD']), key=f"SPEED_WITH_LOAD_{config['id']}")
        config['UNLOADING_DELAY'] = st.number_input("Unloading Delay per Parcel (s)", value=float(config['UNLOADING_DELAY']), key=f"UNLOADING_DELAY_{config['id']}")
        config['LOADING_DELAY'] = st.number_input("Loading Delay per Parcel (s)", value=float(config['LOADING_DELAY']), key=f"LOADING_DELAY_{config['id']}")
        config['FATIGUE_RATIO'] = st.number_input("Worker Fatigue Ratio", value=float(config['FATIGUE_RATIO']), key=f"FATIGUE_RATIO_{config['id']}")
        config['TIME_MULTIPLIER'] = st.number_input("Time Multiplier", value=float(config['TIME_MULTIPLIER']), key=f"TIME_MULTIPLIER_{config['id']}")
        # --- Calculations ---
        L = config['L']
        B = config['B']
        H = config['H']
        PARCEL_L = config['PARCEL_L']
        PARCEL_B = config['PARCEL_B']
        PARCEL_H = config['PARCEL_H']
        SPEED_WITHOUT_LOAD = config['SPEED_WITHOUT_LOAD']
        SPEED_WITH_LOAD = config['SPEED_WITH_LOAD']
        UNLOADING_DELAY = config['UNLOADING_DELAY']
        LOADING_DELAY = config['LOADING_DELAY']
        FATIGUE_RATIO = config['FATIGUE_RATIO']
        TIME_MULTIPLIER = config['TIME_MULTIPLIER']
        Volume_of_Vechile = L * B * H
        Volume_of_Parcel = PARCEL_L * PARCEL_B * PARCEL_H
        No_Parcels_L = int(L // PARCEL_L)
        No_Parcels_B = int(B // PARCEL_B)
        No_Parcels_H = int(H // PARCEL_H)
        Parcels_in_Layer = No_Parcels_B * No_Parcels_H
        Total_Parcels = No_Parcels_L * No_Parcels_B * No_Parcels_H
        Length_Steps_per_Way_ft = 0.75 * (No_Parcels_L - 1) * No_Parcels_L
        Total_Length_Steps_ft = Length_Steps_per_Way_ft * Parcels_in_Layer
        converter = UnitConverter()
        Total_Length_Steps_m = converter.feet_to_meters(Total_Length_Steps_ft)
        Going_hr = (Total_Length_Steps_m / SPEED_WITHOUT_LOAD) / 3600
        Coming_hr = (Total_Length_Steps_m / SPEED_WITH_LOAD) / 3600
        Total_Walking_hr = Going_hr + Coming_hr
        Unloading_Time_h = (Total_Parcels * (UNLOADING_DELAY / 3600))
        Loading_Time_h = (Total_Parcels * (LOADING_DELAY / 3600))
        Total_Loading_Delay_h = Total_Walking_hr + Loading_Time_h
        Total_Unloading_Delay_h = Total_Walking_hr + Unloading_Time_h
        # --- Apply time multiplier to all relevant times ---
        Total_Walking_hr *= TIME_MULTIPLIER
        Loading_Time_h *= TIME_MULTIPLIER
        Total_Loading_Delay_h *= TIME_MULTIPLIER
        Unloading_Time_h *= TIME_MULTIPLIER
        Total_Unloading_Delay_h *= TIME_MULTIPLIER
        # --- Results for this config ---
        st.markdown("#### 🚚 Vehicle Details")
        st.metric("Volume of Vehicle (ft³)", f"{Volume_of_Vechile:,.2f}")
        st.markdown("---")
        st.markdown("#### 📦 Parcel Details")
        st.metric("Volume of Parcel (ft³)", f"{Volume_of_Parcel:,.2f}")
        st.metric("No. of Parcels Length Wise", No_Parcels_L)
        st.metric("No. of Parcels Breadth Wise", No_Parcels_B)
        st.metric("No. of Parcels Height Wise", No_Parcels_H)
        st.metric("No. of Parcels in a Layer", Parcels_in_Layer)
        st.metric("Total No. Of Parcels", Total_Parcels)
        st.markdown("---")
        st.markdown("#### 🚶 Walking Times")
        st.metric("Going Time in Trip (h)", format_hours(Going_hr * TIME_MULTIPLIER))
        st.metric("Coming Time in Trip (h)", format_hours(Coming_hr * TIME_MULTIPLIER))
        st.metric("Total Walking Time (h)", format_hours(Total_Walking_hr))
        st.markdown("---")
        st.markdown("#### ⏳ Loading Times")
        st.metric("Loading Time (h)", format_hours(Loading_Time_h))
        st.metric("Total Loading Delay (h)", format_hours(Total_Loading_Delay_h))
        st.markdown("---")
        st.markdown("#### ⏳ Unloading Times")
        st.metric("Unloading Time (h)", format_hours(Unloading_Time_h))
        st.metric("Total Unloading Delay (h)", format_hours(Total_Unloading_Delay_h))
        # Store results for comparison
        results.append({
            'Vehicle Type': config['type'],
            'Total No. Of Parcels': Total_Parcels,
            'Total Walking Time (h)': Total_Walking_hr,
            'Loading Time (h)': Loading_Time_h,
            'Total Loading Delay (h)': Total_Loading_Delay_h,
            'Unloading Time (h)': Unloading_Time_h,
            'Total Unloading Delay (h)': Total_Unloading_Delay_h,
        })

# Remove marked vehicles
if remove_ids:
    st.session_state['vehicle_configs'] = [c for c in st.session_state['vehicle_configs'] if c['id'] not in remove_ids]

# Comparative Graphs
if results and len(results) > 1:
    st.markdown("---")
    st.markdown("#### 📊 Comparative Graphs")
    df = pd.DataFrame(results)
    vehicle_types = df['Vehicle Type']

    # 1. Walking Time
    st.markdown("##### 🚶 Total Walking Time")
    fig_walking = go.Figure()
    fig_walking.add_trace(go.Bar(
        x=vehicle_types,
        y=df['Total Walking Time (h)'],
        name='Total Walking Time (h)',
        marker_color='blue'
    ))
    fig_walking.update_layout(barmode='group', yaxis_title='Hours')
    st.plotly_chart(fig_walking, use_container_width=True)

    # 2. Loading Times (Grouped: Machine & Human)
    st.markdown("##### ⏳ Loading Times")
    fig_loading = go.Figure()
    fig_loading.add_trace(go.Bar(
        x=vehicle_types,
        y=df['Loading Time (h)'],
        name='Machine Loading Time (h)',
        marker_color='green'
    ))
    fig_loading.add_trace(go.Bar(
        x=vehicle_types,
        y=df['Total Loading Delay (h)'],
        name='Human Loading Time (h)',
        marker_color='red'
    ))
    fig_loading.update_layout(barmode='group', yaxis_title='Hours')
    st.plotly_chart(fig_loading, use_container_width=True)

    # 3. Unloading Times (Grouped: Machine & Human)
    st.markdown("##### ⏳ Unloading Times")
    fig_unloading = go.Figure()
    fig_unloading.add_trace(go.Bar(
        x=vehicle_types,
        y=df['Unloading Time (h)'],
        name='Machine Unloading Time (h)',
        marker_color='green'
    ))
    fig_unloading.add_trace(go.Bar(
        x=vehicle_types,
        y=df['Total Unloading Delay (h)'],
        name='Human Unloading Time (h)',
        marker_color='red'
    ))
    fig_unloading.update_layout(barmode='group', yaxis_title='Hours')
    st.plotly_chart(fig_unloading, use_container_width=True)