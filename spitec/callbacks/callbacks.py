from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from ..view import *
from ..processing import *
from .figure import create_map_with_sites, create_site_data_with_values
import dash
from pathlib import Path
from numpy.typing import NDArray
import time

import requests


language = languages["en"]
FILE_FOLDER = Path("data")

BASE_URL = "http://127.0.0.1:8000"


def register_callbacks(app: dash.Dash) -> None:
    @app.callback(
        Output("graph-site-map", "figure", allow_duplicate=True),
        [Input("projection-radio", "value")],
        [
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_map_projection(
        projection_value: ProjectionType,
        check_value: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
    ) -> go.Figure:
        site_map = create_map_with_sites(
            site_coords,
            projection_value,
            check_value,
            region_site_names,
            site_data_store,
        )
        return site_map

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("graph-site-map", "clickData"),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-data-store", "data", allow_duplicate=True),
        ],
        [Input("graph-site-map", "clickData")],
        [
            State("local-file-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("selection-data-types", "value"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("selection-satellites", "value"),
            State("input-shift", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_site_data(
        clickData: dict[str, list[dict[str, float | str | dict]]],
        local_file: str,
        projection_value: ProjectionType,
        check_value: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        data_types: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        sat: Sat,
        shift: float,
    ) -> list[go.Figure | None | bool | dict[str, int]]:
        if clickData is not None:
            pointIndex = clickData["points"][0]["pointIndex"]
            site_name = list(site_coords.keys())[pointIndex]
            if site_data_store is None:
                site_data_store = {}
            if site_name in site_data_store.keys():
                del site_data_store[site_name]
            else:
                site_data_store[site_name] = pointIndex
        site_map = create_map_with_sites(
            site_coords,
            projection_value,
            check_value,
            region_site_names,
            site_data_store
        )
        site_data = create_site_data_with_values(
            site_data_store, sat, data_types, local_file, time_value, shift
        )

        disabled = True if len(site_data.data) == 0 else False
        return site_map, None, site_data, disabled, site_data_store

    @app.callback(
        [
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
        ],
        [Input("time-slider", "value")],
        [
            State("selection-data-types", "value"),
            State("site-data-store", "data"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("input-shift", "value"),
        ],
        prevent_initial_call=True,
    )
    def change_xaxis(
        time_value: list[int],
        data_types: str,
        site_data_store: dict[str, int],
        local_file: str,
        sat: Sat,
        shift: float,
    ) -> list[go.Figure | bool]:
        site_data = create_site_data_with_values(
            site_data_store, sat, data_types, local_file, time_value, shift
        )
        disabled = True if len(site_data.data) == 0 else False
        return site_data, disabled

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-data-store", "data", allow_duplicate=True),
        ],
        [Input("clear-all", "n_clicks")],
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def clear_all(
        n: int,
        projection_value: ProjectionType,
        check_value: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
    ) -> list[go.Figure | bool | None]:
        site_data = create_site_data_with_values(
            None, None, None, None, None, None
        )
        site_map = create_map_with_sites(
            site_coords, projection_value, check_value, region_site_names, None
        )
        disabled = True
        return site_map, site_data, disabled, None

    @app.callback(
        Output("graph-site-map", "figure", allow_duplicate=True),
        [Input("hide-show-site", "value")],
        [
            State("projection-radio", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("site-data-store", "data")
        ],
        prevent_initial_call=True,
    )
    def hide_show_site(
        check_value: bool,
        projection_value: ProjectionType,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
    ) -> go.Figure:
        site_map = create_map_with_sites(
            site_coords,
            projection_value,
            check_value,
            region_site_names,
            site_data_store,
        )
        return site_map

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("min-lat", "invalid"),
            Output("max-lat", "invalid"),
            Output("min-lon", "invalid"),
            Output("max-lon", "invalid"),
            Output("region-site-names-store", "data", allow_duplicate=True),
        ],
        [Input("apply-lat-lon", "n_clicks")],
        [
            State("min-lat", "value"),
            State("max-lat", "value"),
            State("min-lon", "value"),
            State("max-lon", "value"),
            State("region-site-names-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def apply_selection_by_region(
        n: int,
        min_lat: int,
        max_lat: int,
        min_lon: int,
        max_lon: int,
        region_site_names: dict[str, int],
        projection_value: ProjectionType,
        check_value: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
    ) -> list[go.Figure | bool | dict[str, int]]:
        return_value_list = [
            None,
            False,
            False,
            False,
            False,
            region_site_names,
        ]
        sites = region_site_names

        check_region_value(min_lat, 1, return_value_list)
        check_region_value(max_lat, 2, return_value_list)
        check_region_value(min_lon, 3, return_value_list)
        check_region_value(max_lon, 4, return_value_list)

        if True in return_value_list or site_coords is None:
            return_value_list[0] = create_map_with_sites(
                site_coords,
                projection_value,
                check_value,
                region_site_names,
                site_data_store,
            )
            return return_value_list
        else:
            sites_by_region = select_sites_by_region(
                site_coords, min_lat, max_lat, min_lon, max_lon
            )
            if len(sites_by_region) > 0:
                tmp_sites, _, _ = get_namelatlon_arrays(sites_by_region)

                keys = list(site_coords.keys())
                sites = dict()
                for site in tmp_sites:
                    sites[site] = keys.index(site)
                return_value_list[-1] = sites
        return_value_list[0] = create_map_with_sites(
            site_coords, projection_value, check_value, sites, site_data_store
        )
        return return_value_list

    def check_region_value(
        value: int,
        idx: int,
        return_value_list: dict[str, go.Figure | bool],
    ) -> None:
        if value is None:
            return_value_list[idx] = True

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("distance", "invalid"),
            Output("center-point-lat", "invalid"),
            Output("center-point-lon", "invalid"),
            Output("region-site-names-store", "data", allow_duplicate=True),
        ],
        [Input("apply-great-circle-distance", "n_clicks")],
        [
            State("distance", "value"),
            State("center-point-lat", "value"),
            State("center-point-lon", "value"),
            State("region-site-names-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def apply_great_circle_distance(
        n: int,
        distance: int,
        lat: int,
        lon: int,
        region_site_names: dict[str, int],
        projection_value: ProjectionType,
        check_value: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
    ) -> list[go.Figure | bool | dict[str, int]]:
        return_value_list = [None, False, False, False, region_site_names]
        sites = region_site_names

        check_region_value(distance, 1, return_value_list)
        check_region_value(lat, 2, return_value_list)
        check_region_value(lon, 3, return_value_list)

        if True in return_value_list or site_coords is None:
            return_value_list[0] = create_map_with_sites(
                site_coords,
                projection_value,
                check_value,
                region_site_names,
                site_data_store,
            )
            return return_value_list
        else:
            central_point = dict()
            central_point[Coordinate.lat.value] = lat
            central_point[Coordinate.lon.value] = lon
            sites_by_region = select_sites_in_circle(
                site_coords, central_point, distance
            )
            if len(sites_by_region) > 0:
                tmp_sites, _, _ = get_namelatlon_arrays(sites_by_region)

                keys = list(site_coords.keys())
                sites = dict()
                for site in tmp_sites:
                    sites[site] = keys.index(site)
                return_value_list[-1] = sites
        return_value_list[0] = create_map_with_sites(
            site_coords, projection_value, check_value, sites, site_data_store
        )
        return return_value_list

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("region-site-names-store", "data", allow_duplicate=True),
        ],
        [
            Input("clear-selection-by-region1", "n_clicks"),
            Input("clear-selection-by-region2", "n_clicks"),
        ],
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def clear_selection_by_region(
        n1: int,
        n2: int,
        projection_value: ProjectionType,
        check_value: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
    ) -> list[go.Figure | None]:
        site_map = create_map_with_sites(
            site_coords, projection_value, check_value, None, site_data_store
        )
        return site_map, None

    @app.callback(
        [
            Output("download-window", "is_open"),
            Output("downloaded", "style", allow_duplicate=True),
            Output("downloaded", "children", allow_duplicate=True),
        ],
        [Input("download", "n_clicks")],
        [State("download-window", "is_open")],
        prevent_initial_call=True,
    )
    def open_close_download_window(
        n1: int, is_open: bool
    ) -> list[bool | dict[str, str] | str]:
        style = {"visibility": "hidden"}
        return not is_open, style, ""
    
    @app.callback(
        [
            Output("downloading-file-store", "data", allow_duplicate=True),
            Output("boot-process", "value", allow_duplicate=True),
            Output("load-per", "children", allow_duplicate=True)
        ],
        [Input("boot-progress-window", "is_open")],
        [
            State("downloading-file-store", "data"), 
            State("boot-process", "value"),
            State("load-per", "children")
        ],
        prevent_initial_call=True,
    )
    def delete_incomplete_file(
        is_open: bool, incomplete_file: str, boot_process_value: int, per_value: str
    ) -> list[None | str | int]:
        if not is_open:
            if incomplete_file is not None:
                local_file = FILE_FOLDER / (incomplete_file + ".h5")
                try:
                    f = h5py.File(local_file)
                    f.close
                except:
                    local_file.unlink()
            return None, 0, "0%"
        return incomplete_file, boot_process_value, per_value

    @app.callback(
        [
            Output("downloaded", "style", allow_duplicate=True),
            Output("downloaded", "children", allow_duplicate=True),
        ],
        [Input("download-file", "n_clicks")],
        [State("date-selection", "date")],
        # background=True,
        # running=[
        #     (Output("boot-progress-window", "is_open"), True, True),
        #     (Output("boot-progress-window", "backdrop"), "static", True),
        #     (Output("download-window", "is_open"), False, False),
        #     (
        #         Output("loading-process-modal-header", "close_button"),
        #         False,
        #         True,
        #     ),
        #     (Output("cancel-download", "disabled"), False, True),
        # ],
        # cancel=Input("cancel-download", "n_clicks"),
        # progress=[
        #     Output("boot-process", "value"),
        #     Output("load-per", "children"),
        # ],
        prevent_initial_call=True,
    )
    def download_file(
        # set_progress, 
        n1: int, 
        date: str
    ) -> list[dict[str, str] | str]:
        text = language["download_window"]["successаfuly"]
        color = "green"
        if date is None:
            text = language["download_window"]["unsuccessаfuly"]
        else:
            if not FILE_FOLDER.exists():
                FILE_FOLDER.mkdir()
            local_file = FILE_FOLDER / (date + ".h5")
            if local_file.exists():
                text = language["download_window"]["repeat-action"]
            else:
                local_file.touch()
                response = requests.post(f"{BASE_URL}/download/", json={"filename": date, "local_file": f"{local_file}"})
                if response.status_code == 200:
                    task_id = response.json().get("task_id")
                else:
                    task_id = "Failed to start download"
                # try:
                #     for done in load_data(date, local_file):
                #         set_progress((done, f"{done}%"))
                # except requests.exceptions.HTTPError as err:
                #     text = language["download_window"]["error"]
                #     local_file.unlink()
        if text != language["download_window"]["successаfuly"]:
            color = "red"
        style = {
            "text-align": "center",
            "margin-top": "10px",
            "color": color,
        }
        return style, task_id
    
    @app.callback(
        [
            Output("status-id-task", "children"),
            Output("status-id-task", "style"),
        ],
        [Input("check-id-task", "n_clicks")],
        [State("id-task", "value")],
        prevent_initial_call=True,
    )
    def check_status_task(n: int, id_task: int) -> list[dict[str, str] | str]:
        if id_task == 0:
            return "", {"visibility": "hidden"}
        response = requests.get(f"{BASE_URL}/task_status/{id_task}")
        if response.status_code == 200:
            status = response.json()
            text=f"{status}"
        else:
            text = response.status_code
        style = {
            "margin-top": "20px",
            "text-align": "center",
            "fontSize": "18px",
            "color": "blue",
        }
        return text, style
    
    @app.callback(
        Output("downloading-file-store", "data"),
        [Input("cancel-download", "n_clicks")],
        [State("date-selection", "date")],
        prevent_initial_call=True,
    )
    def save_file_name(n: int, date: str) -> str:
        if date is not None:
            return date
        return None

    @app.callback(
        Output("file-size", "children"),
        [Input("check-file-size", "n_clicks")],
        [State("date-selection", "date")],
        prevent_initial_call=True,
    )
    def check_file_size(n: int, date: str) -> str:
        text = language["download_window"]["file-size"]
        if date is None:
            text += "none"
        else:
            Mb = сheck_file_size(date)
            if Mb is None:
                text += "none"
            elif Mb == 0:
                text += language["download_window"]["unknown"]
            else:
                text += str(Mb)
        return text

    @app.callback(
        [
            Output("open-window", "is_open", allow_duplicate=True),
            Output("select-file", "options"),
        ],
        [Input("open", "n_clicks")],
        [State("open-window", "is_open")],
        prevent_initial_call=True,
    )
    def open_close_open_window(
        n1: int, is_open: bool
    ) -> list[bool | list[dict[str, str]]]:
        options = []
        if FILE_FOLDER.exists():
            for file_path in FILE_FOLDER.iterdir():
                if file_path.is_file():
                    options.append(
                        {"label": file_path.name, "value": file_path.name}
                    )
        return not is_open, options

    @app.callback(
        [
            Output("open-window", "is_open"),
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("local-file-store", "data"),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-coords-store", "data"),
            Output("region-site-names-store", "data"),
            Output("site-data-store", "data"),
            Output("selection-satellites", "options", allow_duplicate=True),
            Output("satellites-options-store", "data"),
        ],
        [Input("open-file", "n_clicks")],
        [
            State("select-file", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
        ],
        prevent_initial_call=True,
    )
    def open_file(
        n1: int,
        filename: str,
        projection_value: ProjectionType,
        check_value: bool,
    ) -> list[
        bool
        | go.Figure
        | str
        | dict[Site, dict[Coordinate, float]]
        | None
        | list[dict[str, str]]
    ]:
        local_file = FILE_FOLDER / filename
        site_coords = get_sites_coords(local_file)

        site_map = create_map_with_sites(
            site_coords, projection_value, check_value, None, None
        )
        site_data = create_site_data()
        satellites = get_satellites(local_file)
        options = [{"label": sat, "value": sat} for sat in satellites]

        return (
            False,
            site_map,
            str(local_file),
            site_data,
            True,
            site_coords,
            None,
            None,
            options,
            options,
        )

    @app.callback(
        Output("graph-site-data", "figure", allow_duplicate=True),
        [Input("selection-data-types", "value")],
        [
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("selection-satellites", "value"),
            State("input-shift", "value"),
        ],
        prevent_initial_call=True,
    )
    def change_data_types(
        data_types: str,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        sat: Sat,
        shift: float,
    ) -> go.Figure:
        site_data = create_site_data_with_values(
            site_data_store, sat, data_types, local_file, time_value, shift
        )
        return site_data

    @app.callback(
        Output("graph-site-data", "figure", allow_duplicate=True),
        [Input("selection-satellites", "value")],
        [
            State("selection-data-types", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("input-shift", "value"),
        ],
        prevent_initial_call=True,
    )
    def change_satellite(
        sat: Sat,
        data_types: str,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        shift: float,
    ) -> go.Figure:
        site_data = create_site_data_with_values(
            site_data_store, sat, data_types, local_file, time_value, shift
        )
        return site_data

    @app.callback(
        Output("graph-site-data", "figure", allow_duplicate=True),
        [Input("input-shift", "value")],
        [
            State("selection-data-types", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("selection-satellites", "value"),
        ],
        prevent_initial_call=True,
    )
    def change_shift(
        shift: float,
        data_types: str,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        sat: Sat,
    ) -> go.Figure:
        site_data = create_site_data_with_values(
            site_data_store, sat, data_types, local_file, time_value, shift
        )
        return site_data

    @app.callback(
        [
            Output("graph-site-map", "figure"),
            Output("graph-site-data", "figure"),
            Output("time-slider", "disabled"),
            Output("selection-satellites", "options"),
        ],
        [Input("url", "pathname")],
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("local-file-store", "data"),
            State("time-slider", "value"),
            State("selection-data-types", "value"),
            State("satellites-options-store", "data"),
            State("selection-satellites", "value"),
            State("input-shift", "value"),
        ],
    )
    def update_all(
        pathname: str,
        projection_value: ProjectionType,
        check_value: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        local_file: str,
        time_value: list[int],
        data_types: str,
        satellites_options: list[dict[str, str]],
        sat: Sat,
        shift: float,
    ) -> list[go.Figure, bool, list[dict[str, str]]]:
        site_map = create_map_with_sites(
            site_coords,
            projection_value,
            check_value,
            region_site_names,
            site_data_store,
        )
        site_data = create_site_data_with_values(
            site_data_store, sat, data_types, local_file, time_value, shift
        )
        disabled = True if len(site_data.data) == 0 else False
        if satellites_options is None:
            satellites_options = []
        return site_map, site_data, disabled, satellites_options
