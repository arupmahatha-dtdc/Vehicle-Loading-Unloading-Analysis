import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# Vehicle data and benchmarks from the notebook
VEHICLES = [
    {"type": "50 ft ODC Trailer / Container", "L": 50, "parcels": 1500},
    {"type": "32 ft Container MXL", "L": 32, "parcels": 1000},
    {"type": "32 ft Container SXL", "L": 32, "parcels": 700},
    {"type": "24 ft Box/Container Truck", "L": 24, "parcels": 600},
    {"type": "Tata 22 ft Container", "L": 22, "parcels": 600},
    {"type": "Eicher 19 ft", "L": 19, "parcels": 500},
    {"type": "Eicher 17 ft", "L": 17, "parcels": 425},
    {"type": "Eicher 14 ft (LCV)", "L": 14, "parcels": 300},
    {"type": "Tata 407 / Dost Bada", "L": 10, "parcels": 215},
    {"type": "Mahindra Bolero Pickup", "L": 9, "parcels": 100},
    {"type": "Tata Ace / Dost", "L": 8, "parcels": 50},
]

# Optimized parameters from the notebook
OPTIMIZED_PARAMS = {
    "f1": 1.296, "f2": 1.200, "f3": 1.008, "f4": 1.029,
    "alpha": 0.830, "tturn": 1.879,
    "v_walk": 0.830, "v_load": 0.534,
    "d_load": 13.96, "d_unld": 9.93
}

# Vehicle type mapping for CSV data
VEHICLE_MAPPING = {
    "19'": "Eicher 19 ft",
    "20'": "Tata 407 / Dost Bada",  # Assuming 20' maps to this
    "32' MA": "32 ft Container MXL",
    "32'SXL": "32 ft Container SXL",
    "14'": "Eicher 14 ft (LCV)",
    "17'": "Eicher 17 ft",
    "22'": "Tata 22 ft Container"
}

def compute_times(vehicle_type, operation_type="manual", custom_parcels=None):
    """Compute loading/unloading times for a vehicle type"""
    # Find vehicle data
    vehicle_data = None
    for v in VEHICLES:
        if v["type"] == vehicle_type:
            vehicle_data = v
            break
    
    if not vehicle_data:
        return None
    
    # Use custom parcels if provided, otherwise use default
    n = custom_parcels if custom_parcels is not None else vehicle_data['parcels']
    L_ft = vehicle_data['L']
    
    # Fatigue multiplier
    if n <= 100:
        fm = OPTIMIZED_PARAMS["f1"]
    elif n <= 200:
        fm = OPTIMIZED_PARAMS["f2"]
    elif n <= 300:
        fm = OPTIMIZED_PARAMS["f3"]
    else:
        fm = OPTIMIZED_PARAMS["f4"]
    
    # Walking distance (m)
    d = L_ft * 0.3048 * OPTIMIZED_PARAMS["alpha"]
    
    # Walking time (hr)
    walk_hr = ((d / OPTIMIZED_PARAMS["v_walk"]) + (d / OPTIMIZED_PARAMS["v_load"])) * n * fm / 3600
    
    # Handling time (hr)
    load_hr = (OPTIMIZED_PARAMS["d_load"] + OPTIMIZED_PARAMS["tturn"]) * n * fm / 3600
    unld_hr = (OPTIMIZED_PARAMS["d_unld"] + OPTIMIZED_PARAMS["tturn"]) * n * fm / 3600
    
    # Machine times (hr) with 50% buffer
    machL = load_hr * 1.5
    machU = unld_hr * 1.5
    
    if operation_type == "manual":
        return {
            "loading": walk_hr + load_hr,
            "unloading": walk_hr + unld_hr
        }
    else:  # machine
        return {
            "loading": machL,
            "unloading": machU
        }

def parse_time(time_str):
    """Parse time string to datetime"""
    try:
        return datetime.strptime(time_str, "%H:%M")
    except:
        return datetime.strptime(time_str, "%H:%M:%S")

def create_gantt_chart(df, operation_type, operation_mode):
    """Create Gantt chart from vehicle data"""
    tasks = []
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    current_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for idx, row in df.iterrows():
        vehicle_type = row['Vehicle Type']
        arrival_time = parse_time(row['Arrival Time'])
        
        # Map vehicle type to full name
        mapped_type = VEHICLE_MAPPING.get(vehicle_type, vehicle_type)
        
        # Calculate operation time
        times = compute_times(mapped_type, operation_mode)
        if times is None:
            continue
            
        operation_time = times[operation_type.lower()]
        
        # Convert to hours and minutes
        hours = int(operation_time)
        minutes = int((operation_time - hours) * 60)
        
        # Calculate start and end times
        start_time = current_time + timedelta(hours=arrival_time.hour, minutes=arrival_time.minute)
        end_time = start_time + timedelta(hours=hours, minutes=minutes)
        
        tasks.append(dict(
            Task=f"Vehicle {idx+1} ({vehicle_type})",
            Start=start_time,
            Finish=end_time,
            Resource=mapped_type
        ))
    
    if not tasks:
        return None
    
    # Create Gantt chart
    fig = ff.create_gantt(tasks, 
                          colors=colors,
                          index_col='Resource',
                          show_colorbar=True,
                          group_tasks=True,
                          title=f"Vehicle {operation_type.title()} Schedule ({operation_mode.title()})")
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Vehicles",
        height=400 + len(tasks) * 30
    )
    
    return fig

def calculate_hourly_workload(df, operation_type, operation_mode, num_workers=1):
    """Calculate number of vehicles being worked on per hour"""
    hourly_data = {}
    
    for idx, row in df.iterrows():
        vehicle_type = row['Vehicle Type']
        arrival_time = parse_time(row['Arrival Time'])
        
        # Get custom parcels if available in CSV
        custom_parcels = None
        if 'Parcels' in df.columns:
            custom_parcels = row.get('Parcels')
            if pd.isna(custom_parcels):
                custom_parcels = None
        
        mapped_type = VEHICLE_MAPPING.get(vehicle_type, vehicle_type)
        times = compute_times(mapped_type, operation_mode, custom_parcels)
        
        if times is None:
            continue
            
        operation_time = times[operation_type.lower()]
        
        # Divide operation time by number of workers
        operation_time = operation_time / num_workers
        
        # Calculate total minutes and proper clock wrapping
        total_minutes = arrival_time.hour * 60 + arrival_time.minute + (operation_time * 60)
        end_hour = int((total_minutes // 60) % 24)  # Wrap around 24 hours, convert to int
        end_minute = int(total_minutes % 60)  # Convert to int
        
        start_hour = arrival_time.hour
        
        # Handle operations that cross midnight
        if end_hour < start_hour:
            # Operation crosses midnight
            # Add vehicle to hours from start to 23
            for hour in range(start_hour, 24):
                if hour not in hourly_data:
                    hourly_data[hour] = 0
                hourly_data[hour] += 1
            
            # Add vehicle to hours from 0 to end_hour
            for hour in range(0, end_hour + 1):
                if hour not in hourly_data:
                    hourly_data[hour] = 0
                hourly_data[hour] += 1
        else:
            # Normal case: operation within same day
            # Add vehicle to each hour it's being worked on
            for hour in range(start_hour, end_hour + 1):
                if hour not in hourly_data:
                    hourly_data[hour] = 0
                hourly_data[hour] += 1
    
    return hourly_data

def create_time_based_gantt_chart(df, operation_type, operation_mode, num_workers=1):
    """Create time-based Gantt chart showing actual vehicle operation times"""
    tasks = []
    
    current_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for idx, row in df.iterrows():
        vehicle_type = row['Vehicle Type']
        arrival_time = parse_time(row['Arrival Time'])
        
        # Get custom parcels if available in CSV
        custom_parcels = None
        if 'Parcels' in df.columns:
            custom_parcels = row.get('Parcels')
            if pd.isna(custom_parcels):
                custom_parcels = None
        
        mapped_type = VEHICLE_MAPPING.get(vehicle_type, vehicle_type)
        times = compute_times(mapped_type, operation_mode, custom_parcels)
        
        if times is None:
            continue
            
        operation_time = times[operation_type.lower()]
        
        # Divide operation time by number of workers
        operation_time = operation_time / num_workers
        
        # Calculate actual start and end times
        start_time = current_time + timedelta(hours=arrival_time.hour, minutes=arrival_time.minute)
        
        # Calculate end time with proper clock wrapping
        total_minutes = arrival_time.hour * 60 + arrival_time.minute + (operation_time * 60)
        end_hour = int((total_minutes // 60) % 24)  # Wrap around 24 hours, convert to int
        end_minute = int(total_minutes % 60)  # Convert to int
        
        end_time = current_time + timedelta(hours=end_hour, minutes=end_minute)
        
        # If end time is before start time, it means it wrapped around midnight
        if end_time < start_time:
            # Create two separate tasks: one from start to midnight, one from midnight to end
            midnight = current_time + timedelta(hours=24)
            
            # First part: from start to midnight
            tasks.append(dict(
                Task=f"Vehicle {idx+1} (Part 1)",
                Start=start_time,
                Finish=midnight,
                Resource="Vehicle"
            ))
            
            # Second part: from midnight to end
            tasks.append(dict(
                Task=f"Vehicle {idx+1} (Part 2)",
                Start=current_time,
                Finish=end_time,
                Resource="Vehicle"
            ))
        else:
            # Normal case: start and end on same day
            tasks.append(dict(
                Task=f"Vehicle {idx+1}",
                Start=start_time,
                Finish=end_time,
                Resource="Vehicle"
            ))
    
    if not tasks:
        return None
    
    # Create Gantt chart without grouping
    fig = ff.create_gantt(tasks, 
                          colors=['#1f77b4'],  # Single blue color
                          index_col='Resource',
                          show_colorbar=False,
                          group_tasks=False,  # Don't group tasks
                          title=f"Vehicle {operation_type.title()} Schedule ({operation_mode.title()}) - {num_workers} Workers")
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=200 + len(tasks) * 15,  # Reduced height and spacing
        showlegend=False
    )
    
    # Update x-axis to show time labels at the top
    fig.update_xaxes(
        tickformat="%H:%M",
        tickmode='array',
        tickvals=[current_time + timedelta(hours=h) for h in range(0, 24)],
        ticktext=[f"{h:02d}:00" for h in range(0, 24)],
        side='top',  # Move time labels to top
        rangeslider_visible=False,  # Disable range slider
        rangeselector_visible=False  # Disable range selector buttons (1y, 1w, 1m)
    )
    
    # Remove y-axis labels and make lines thinner
    fig.update_yaxes(showticklabels=False)
    
    # Make the bars thinner by updating the layout
    fig.update_layout(
        bargap=0.8,  # Increase gap between bars
        bargroupgap=0.1  # Reduce gap between groups
    )
    
    return fig

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Vehicle Loading/Unloading Analysis", layout="wide")
    
    st.title("🚛 Vehicle Loading/Unloading Analysis")
    st.markdown("---")
    
    # File upload
    st.header("📁 Upload Data")
    uploaded_file = st.file_uploader(
        "Upload your CSV file with 'Arrival Time', 'Vehicle Type', 'Type', and 'Hub Code' columns",
        type=['csv']
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ File uploaded successfully!")
            
            # --- Hub selection ---
            st.header("🏢 Select Hub")
            hub_codes = df['Hub Code'].unique().tolist()
            selected_hub = st.selectbox("Select Hub Code:", hub_codes)
            df = df[df['Hub Code'] == selected_hub]
            
            # --- Operation Mode and Workers ---
            st.header("⚙️ Operation Settings")
            col1, col2 = st.columns(2)
            with col1:
                operation_mode = st.selectbox(
                    "Select Operation Mode:",
                    ["Manual", "Machine"]
                )
            with col2:
                num_workers = st.number_input(
                    "Number of Workers:",
                    min_value=1,
                    max_value=20,
                    value=1,
                    step=1
                )
            
            # --- Time Calculations Table ---
            st.header("⏱️ Time Calculations")
            time_data = []
            for idx, row in df.iterrows():
                vehicle_type = row['Vehicle Type']
                arrival_time = row['Arrival Time']
                operation_type = row['Type']  # Now from CSV
                mapped_type = VEHICLE_MAPPING.get(vehicle_type, vehicle_type)
                # Get custom parcels if available in CSV
                custom_parcels = None
                if 'Parcels' in df.columns:
                    custom_parcels = row.get('Parcels')
                    if pd.isna(custom_parcels):
                        custom_parcels = None
                times = compute_times(mapped_type, operation_mode.lower(), custom_parcels)
                if times:
                    original_time = times[operation_type.lower()]
                    adjusted_time = original_time / num_workers
                    # Get default parcel count for this vehicle type
                    default_parcels = None
                    for v in VEHICLES:
                        if v["type"] == mapped_type:
                            default_parcels = v['parcels']
                            break
                    time_data.append({
                        "Arrival Time": arrival_time,
                        "Original Type": vehicle_type,
                        "Mapped Type": mapped_type,
                        "Operation": operation_type,
                        "Parcels Used": custom_parcels if custom_parcels is not None else f"{default_parcels} (default)",
                        f"{operation_type} Time (hours)": round(original_time, 2),
                        f"Adjusted Time ({num_workers} workers)": round(adjusted_time, 2)
                    })
            time_df = pd.DataFrame(time_data)
            st.dataframe(time_df)
            
            # --- Time-based Gantt Chart ---
            st.header("📈 Time-Based Gantt Chart")
            gantt_tasks = []
            current_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            for idx, row in df.iterrows():
                vehicle_type = row['Vehicle Type']
                arrival_time = parse_time(row['Arrival Time'])
                operation_type = row['Type']
                mapped_type = VEHICLE_MAPPING.get(vehicle_type, vehicle_type)
                custom_parcels = None
                if 'Parcels' in df.columns:
                    custom_parcels = row.get('Parcels')
                    if pd.isna(custom_parcels):
                        custom_parcels = None
                times = compute_times(mapped_type, operation_mode.lower(), custom_parcels)
                if not times:
                    continue
                operation_time = times[operation_type.lower()] / num_workers
                start_time = current_time + timedelta(hours=arrival_time.hour, minutes=arrival_time.minute)
                total_minutes = arrival_time.hour * 60 + arrival_time.minute + (operation_time * 60)
                end_hour = int((total_minutes // 60) % 24)
                end_minute = int(total_minutes % 60)
                end_time = current_time + timedelta(hours=end_hour, minutes=end_minute)
                if end_time < start_time:
                    midnight = current_time + timedelta(hours=24)
                    gantt_tasks.append(dict(
                        Task=f"Vehicle {idx+1} (Part 1)",
                        Start=start_time,
                        Finish=midnight,
                        Resource=operation_type
                    ))
                    gantt_tasks.append(dict(
                        Task=f"Vehicle {idx+1} (Part 2)",
                        Start=current_time,
                        Finish=end_time,
                        Resource=operation_type
                    ))
                else:
                    gantt_tasks.append(dict(
                        Task=f"Vehicle {idx+1}",
                        Start=start_time,
                        Finish=end_time,
                        Resource=operation_type
                    ))
            if gantt_tasks:
                fig = ff.create_gantt(gantt_tasks,
                                     colors={'Loading': '#1f77b4', 'Unloading': '#ff7f0e'},
                                     index_col='Resource',
                                     show_colorbar=True,
                                     group_tasks=True,
                                     title=f"Vehicle Loading/Unloading Schedule ({operation_mode.title()}) - {selected_hub}")
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Vehicles",
                    height=200 + len(gantt_tasks) * 15,
                    showlegend=True
                )
                fig.update_xaxes(
                    tickformat="%H:%M",
                    tickmode='array',
                    tickvals=[current_time + timedelta(hours=h) for h in range(0, 24)],
                    ticktext=[f"{h:02d}:00" for h in range(0, 24)],
                    side='top',
                    rangeslider_visible=False,
                    rangeselector_visible=False
                )
                fig.update_yaxes(showticklabels=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Could not create time-based Gantt chart. Check vehicle type mappings.")
            
            # --- Hourly Workload ---
            st.header("📊 Hourly Workload Analysis")
            hourly_data = {}
            for idx, row in df.iterrows():
                vehicle_type = row['Vehicle Type']
                arrival_time = parse_time(row['Arrival Time'])
                operation_type = row['Type']
                mapped_type = VEHICLE_MAPPING.get(vehicle_type, vehicle_type)
                custom_parcels = None
                if 'Parcels' in df.columns:
                    custom_parcels = row.get('Parcels')
                    if pd.isna(custom_parcels):
                        custom_parcels = None
                times = compute_times(mapped_type, operation_mode.lower(), custom_parcels)
                if not times:
                    continue
                operation_time = times[operation_type.lower()] / num_workers
                total_minutes = arrival_time.hour * 60 + arrival_time.minute + (operation_time * 60)
                end_hour = int((total_minutes // 60) % 24)
                start_hour = arrival_time.hour
                if end_hour < start_hour:
                    for hour in range(start_hour, 24):
                        if hour not in hourly_data:
                            hourly_data[hour] = 0
                        hourly_data[hour] += 1
                    for hour in range(0, end_hour + 1):
                        if hour not in hourly_data:
                            hourly_data[hour] = 0
                        hourly_data[hour] += 1
                else:
                    for hour in range(start_hour, end_hour + 1):
                        if hour not in hourly_data:
                            hourly_data[hour] = 0
                        hourly_data[hour] += 1
            if hourly_data:
                hours = list(hourly_data.keys())
                counts = list(hourly_data.values())
                fig = go.Figure(data=[
                    go.Bar(x=hours, y=counts, 
                          marker_color='lightblue',
                          text=counts,
                          textposition='auto')
                ])
                fig.update_layout(
                    title=f"Number of Vehicles Being Worked per Hour ({operation_mode}) - {num_workers} Workers - {selected_hub}",
                    xaxis_title="Hour of Day",
                    yaxis_title="Number of Vehicles",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                workload_df = pd.DataFrame([
                    {"Hour": hour, "Vehicles": count}
                    for hour, count in sorted(hourly_data.items())
                ])
                st.dataframe(workload_df)
            else:
                st.warning("⚠️ Could not calculate hourly workload.")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure your CSV has 'Arrival Time', 'Vehicle Type', 'Type', and 'Hub Code' columns.")
    else:
        st.info("📤 Please upload a CSV file to begin analysis.")
        st.subheader("📋 Expected CSV Format")
        sample_data = {
            "Arrival Time": ["0:00", "1:00", "2:00"],
            "Vehicle Type": ["19'", "32' MA", "32'SXL"],
            "Type": ["Loading", "Unloading", "Loading"],
            "Hub Code": ["HUB1", "HUB2", "HUB3"]
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df)
        st.markdown("""
        **Supported Vehicle Types:**
        - 19' → Eicher 19 ft
        - 20' → Tata 407 / Dost Bada
        - 32' MA → 32 ft Container MXL
        - 32'SXL → 32 ft Container SXL
        - 14' → Eicher 14 ft (LCV)
        - 17' → Eicher 17 ft
        - 22' → Tata 22 ft Container
        """)

if __name__ == "__main__":
    main()