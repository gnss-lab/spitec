from dash import html, dcc
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from enum import Enum
import numpy as np
from numpy.typing import NDArray


class ProjectionType(Enum):
    MERCATOR = "mercator"
    ROBINSON = "robinson"
    ORTHOGRAPHIC = "orthographic"


class PointColor(Enum):
    SILVER = "silver"
    RED = "red"
    GREEN = "green"


def create_layout(station_map: go.Figure, station_data: go.Figure) -> html.Div:
    projection_radio = _create_projection_radio()
    time_slider = _create_time_slider()

    size_map = 5
    size_data = 7
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button("Загрузить", className="me-1"),
                            dbc.Button(
                                "Открыть",
                                className="me-1",
                                style={"margin-left": "20px"},
                            ),
                            dbc.Button(
                                "Настройки",
                                className="me-1",
                                style={"margin-left": "20px"},
                            ),
                        ]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(id="graph-station-map", figure=station_map),
                        width={"size": size_map},
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id="graph-station-data", figure=station_data
                        ),
                        width={"size": size_data},
                    ),
                ],
                align="center",
                style={"margin-top": "30px"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        projection_radio,
                        width={"size": size_map},
                        style={"margin-top": "30px"},
                    ),
                    dbc.Col(
                        time_slider,
                        width={"size": size_data},
                        style={"margin-top": "30px"},
                    ),
                ],
                style={"text-align": "center", "fontSize": "18px"},
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "Очистить всё", id="clear-all", className="me-1"
                    ),
                    width={"size": size_data, "offset": size_map},
                    style={
                        "margin-top": "20px",
                        "fontSize": "18px",
                        "text-align": "center",
                    },
                )
            ),
        ],
        style={
            "margin-top": "30px",
            "margin-left": "50px",
            "margin-right": "50px",
        },
    )
    return layout


def create_station_map(
    site_names: NDArray, latitudes_array: NDArray, longitudes_array: NDArray
) -> go.Figure:
    colors = np.array([PointColor.SILVER.value] * site_names.shape[0])
    station_map = go.Scattergeo(
        lat=latitudes_array,
        lon=longitudes_array,
        text=[site.upper() for site in site_names],
        mode="markers+text",
        marker=dict(size=8, color=colors, line=dict(color="gray", width=1)),
        hoverlabel=dict(bgcolor="white"),
        textposition="top center",
        hoverinfo="lat+lon",
    )

    figure = go.Figure(station_map)
    figure.update_layout(
        title="Карта",
        title_font=dict(size=28, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
    )
    figure.update_geos(
        landcolor="white",
        # landcolor="LightGreen",
        # showocean=True,
        # oceancolor="LightBlue",
        # showcountries=True,
        # countrycolor="Black",
    )

    return figure


def _create_projection_radio() -> html.Div:
    options = [
        {"label": projection.value.capitalize(), "value": projection.value}
        for projection in ProjectionType
    ]
    checklist = html.Div(
        dbc.RadioItems(
            options=options,
            id="projection-radio",
            inline=True,
        )
    )
    return checklist


def create_station_data() -> go.Figure:
    station_data = go.Figure()

    station_data.update_layout(
        title="Данные",
        title_font=dict(size=28, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
        xaxis=dict(title="Время"),
    )
    return station_data


def _create_time_slider() -> html.Div:
    marks = {i: f"{i:02d}:00" if i % 3 == 0 else "" for i in range(25)}
    time_slider = html.Div(
        dcc.RangeSlider(
            id="time-slider",
            min=0,
            max=24,
            step=1,
            marks=marks,
            value=[0, 24],
            allowCross=False,
            tooltip={
                "placement": "top",
                "style": {"fontSize": "18px"},
                "template": "{value}:00",
            },
        ),
    )
    return time_slider
