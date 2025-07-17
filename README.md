# Vehicle-Loading-Unloading-Analysis

This project provides an interactive Streamlit web application to analyze and compare the loading and unloading times for various types of vehicles, considering both human and machine-assisted operations. The tool allows users to select vehicle types, adjust parcel and worker parameters, and visualize comparative results.

## Features
- Select from a variety of common vehicle types and customize their dimensions and payloads.
- Adjust parcel size and worker operation parameters (speed, fatigue, delays, etc.).
- Instantly see calculated metrics for loading/unloading times, walking times, and parcel arrangements.
- Add or remove multiple vehicles for side-by-side comparison.
- Visualize results with interactive bar charts (Plotly).
- Unit conversion utility for flexible dimension handling.

## File Structure
- `app.py`: Main Streamlit application. Handles UI, calculations, and visualizations.
- `unit_converter.py`: Utility for unit conversions using a CSV-based conversion table.
- `data/unit_conversion.csv`: CSV file containing unit conversion factors between common length units.
- `README.md`: Project documentation and instructions.

## Setup Instructions
1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Vehicle-Loading-Unloading-Analysis
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```

## Usage
- Use the sidebar and controls to select vehicle types and adjust parameters.
- Add or remove vehicles to compare different configurations.
- View calculated metrics and comparative graphs for walking, loading, and unloading times.

## Requirements
See `requirements.txt` for the full list of dependencies.

## Notes
- The unit conversion table can be extended by editing `data/unit_conversion.csv`.
- All calculations assume rectangular parcels and vehicles.
- For any issues or suggestions, please open an issue or pull request.
