from dash import html, dcc
from dash.dependencies import Input, Output, State
from spitec.view import *
from spitec.callbacks import register_callbacks
from app import app

def generate_new_session():
    site_map = create_site_map()
    site_data = create_site_data()
    time_slider = create_time_slider()
    selection_data_types = create_selection_data_types()
    projection_radio = create_projection_radio()
    checkbox_site = create_checkbox_site()
    layout = create_layout(site_map, site_data, time_slider, selection_data_types, projection_radio, checkbox_site)

    register_callbacks(
        site_map,
        site_data,
        time_slider,
        selection_data_types,
        projection_radio, 
        checkbox_site
    )
    return layout 

server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id="href-store", storage_type="session"),
    html.Div(id='page-content')
])

@app.callback(
        [Output('page-content', 'children'),
         Output('href-store', 'data')],
         [Input('url', 'href')],
         [State('href-store', 'data'),
          State('page-content', 'children')]
)
def display_page(href: str, saved_href: str, page: html.Div) -> list[html.Div | str]:
    print(href) 
    print(page)
    if saved_href is None:
        layout = generate_new_session()
        return layout, href
    elif saved_href == href:
        return page, href
    elif saved_href != href:
        layout = generate_new_session()
        return layout, href

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)
