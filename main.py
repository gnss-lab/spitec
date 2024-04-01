import dash
from pathlib import Path
from spitec import *

LOCAL_FILE = Path("data/2024-01-22.h5")
site_coords = get_sites_coords(LOCAL_FILE)
site_array, lat_array, lon_array = get_namelatlon_arrays(site_coords)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

station_map = create_station_map(site_array, lat_array, lon_array)
station_data = create_station_data()

projection_radio = create_projection_radio()
time_slider = create_time_slider()
checkbox_site = create_checkbox_site()

app.layout = create_layout(
    station_map, station_data, projection_radio, time_slider, checkbox_site
)

register_callbacks(
    app,
    LOCAL_FILE,
    site_coords,
    station_map,
    station_data,
    projection_radio,
    time_slider,
    checkbox_site,
)

if __name__ == "__main__":
    app.run_server(debug=True)
