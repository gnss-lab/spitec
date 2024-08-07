from ..view import *
from ..processing import *
from datetime import datetime, timezone


def create_map_with_sites(
    site_coords: dict[Site, dict[Coordinate, float]],
    projection_value: ProjectionType,
    check_value: bool,
    region_site_names: dict[str, int],
    site_data_store: dict[str, int],
    relayout_data: dict[str, float],
    scale_map_store: float,
) -> go.Figure:
    site_map = create_site_map()

    if projection_value != site_map.layout.geo.projection.type:
        site_map.update_layout(geo=dict(projection_type=projection_value))
    if site_coords is not None:
        site_array, lat_array, lon_array = get_namelatlon_arrays(site_coords)

        if check_value:
            site_map.data[0].text = [site.upper() for site in site_array]
        else:
            if site_data_store is not None:
                sites_name_lower = list(site_data_store.keys())
            else:
                sites_name_lower = []
            site_map.data[0].text = [
                site.upper() if site in sites_name_lower else ""
                for site in site_array
            ]
            site_map.data[0].customdata = [
                site.upper() if site not in sites_name_lower else ""
                for site in site_array
            ]
            site_map.data[0].hoverinfo = "text"
            site_map.data[0].hovertemplate = (
                "%{customdata} (%{lat}, %{lon})<extra></extra>"
            )
        colors = np.array([PointColor.SILVER.value] * site_array.shape[0])

        site_map.data[0].lat = lat_array
        site_map.data[0].lon = lon_array
        site_map.data[0].marker.color = colors

        _change_points_on_map(region_site_names, site_data_store, site_map)
    if relayout_data is not None:
        _change_scale_map(
            site_map, relayout_data, scale_map_store, projection_value
        )
    return site_map


def _change_scale_map(
    site_map: go.Figure,
    relayout_data: dict[str, float],
    scale_map_store: float,
    projection_value: ProjectionType,
) -> None:
    if relayout_data.get("geo.projection.scale", None) is not None:
        scale = relayout_data.get("geo.projection.scale")
    else:
        scale = scale_map_store
    if projection_value != ProjectionType.ORTHOGRAPHIC.value:
        site_map.update_layout(
            geo=dict(
                projection=dict(
                    rotation=dict(
                        lon=relayout_data.get("geo.projection.rotation.lon", 0)
                    ),
                    scale=scale,
                ),
                center=dict(
                    lon=relayout_data.get("geo.center.lon", 0),
                    lat=relayout_data.get("geo.center.lat", 0),
                ),
            )
        )
    else:
        site_map.update_layout(
            geo=dict(
                projection=dict(
                    rotation=dict(
                        lon=relayout_data.get(
                            "geo.projection.rotation.lon", 0
                        ),
                        lat=relayout_data.get(
                            "geo.projection.rotation.lat", 0
                        ),
                    ),
                    scale=scale,
                )
            )
        )


def _change_points_on_map(
    region_site_names: dict[str, int],
    site_data_store: dict[str, int],
    site_map: go.Figure,
) -> None:
    colors = site_map.data[0].marker.color.copy()

    if region_site_names is not None:
        for idx in region_site_names.values():
            colors[idx] = PointColor.GREEN.value
    if site_data_store is not None:
        for idx in site_data_store.values():
            colors[idx] = PointColor.RED.value
    site_map.data[0].marker.color = colors


def create_site_data_with_values(
    site_data_store: dict[str, int],
    sat: Sat,
    data_types: str,
    local_file: str,
    time_value: list[int],
    shift: float,
) -> go.Figure:
    site_data = create_site_data()
    
    if site_data_store is not None:
        dataproduct = _define_data_type(data_types)
        if shift is None or shift == 0:
            shift = -1
            if dataproduct in [DataProducts.dtec_2_10, DataProducts.roti, DataProducts.dtec_10_20]:
                shift = -0.5
        _add_lines(
            site_data,
            list(site_data_store.keys()),
            sat,
            dataproduct,
            local_file,
            shift,
        )
        if len(site_data.data) > 0:
            limit = _create_limit_xaxis(time_value, site_data)
            site_data.update_layout(xaxis=dict(range=[limit[0], limit[1]]))
    return site_data


def _define_data_type(data_types: str) -> DataProducts:
    dataproduct = DataProducts.dtec_2_10
    for name_data in DataProducts.__members__:
        if data_types == name_data:
            dataproduct = DataProducts.__members__[name_data]
            break
    return dataproduct


def _add_lines(
    site_data: go.Figure,
    sites_name: list[Site],
    sat: Sat,
    dataproduct: DataProducts,
    local_file: str,
    shift: float,
) -> None:
    site_data_tmp, is_satellite = retrieve_data(
        local_file, sites_name, sat, dataproduct
    )
    scatters = []
    for i, name in enumerate(sites_name):
        if sat is None or not is_satellite[name]:
            sat_tmp = list(site_data_tmp[name].keys())[0]

            vals = site_data_tmp[name][sat_tmp][dataproduct]
            times = site_data_tmp[name][sat_tmp][DataProducts.time]
            vals_tmp = np.zeros_like(vals)

            scatters.append(
                go.Scatter(
                    x=times,
                    y=vals_tmp + shift * (i + 1),
                    customdata=vals_tmp,
                    mode="markers",
                    name=name.upper(),
                    line=dict(color="gray"),
                    hoverinfo="text",
                    hovertemplate="%{x}, %{customdata}<extra></extra>",
                    marker=dict(
                        size=2,
                    ),
                )
            )
        else:
            if (
                dataproduct == DataProducts.azimuth
                or dataproduct == DataProducts.elevation
            ):
                vals = np.degrees(site_data_tmp[name][sat][dataproduct])
            else:
                vals = site_data_tmp[name][sat][dataproduct]
            times = site_data_tmp[name][sat][DataProducts.time]

            scatters.append(
                go.Scatter(
                    x=times,
                    y=vals + shift * (i + 1),
                    customdata=vals,
                    mode="markers",
                    name=name.upper(),
                    hoverinfo="text",
                    hovertemplate="%{x}, %{customdata}<extra></extra>",
                    marker=dict(
                        size=3,
                    ),
                )
            )
    site_data.add_traces(scatters)

    site_data.layout.yaxis.tickmode = "array"
    site_data.layout.yaxis.tickvals = [
        shift * (i + 1) for i in range(len(sites_name))
    ]
    site_data.layout.yaxis.ticktext = list(map(str.upper, sites_name))


def _create_limit_xaxis(
    time_value: list[int], site_data: go.Figure
) -> tuple[datetime]:
    date = site_data.data[0].x[0]

    hour_start_limit = 23 if time_value[0] == 24 else time_value[0]
    minute_start_limit = 59 if time_value[0] == 24 else 0
    second_start_limit = 59 if time_value[0] == 24 else 0

    hour_end_limit = 23 if time_value[1] == 24 else time_value[1]
    minute_end_limit = 59 if time_value[1] == 24 else 0
    second_end_limit = 59 if time_value[1] == 24 else 0

    start_limit = datetime(
        date.year,
        date.month,
        date.day,
        hour=hour_start_limit,
        minute=minute_start_limit,
        second=second_start_limit,
        tzinfo=timezone.utc,
    )
    end_limit = datetime(
        date.year,
        date.month,
        date.day,
        hour=hour_end_limit,
        minute=minute_end_limit,
        second=second_end_limit,
        tzinfo=timezone.utc,
    )
    return (start_limit, end_limit)
