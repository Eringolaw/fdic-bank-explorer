#!/usr/bin/env python3
"""
FDIC Bank Dashboard
Interactive dashboard to explore FDIC-insured banks and their branch locations.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table, ctx
from dash.exceptions import PreventUpdate

# Noviam color palette
NOVIAM_BLUE = "#004796"
NOVIAM_MID_BLUE = "#006BFF"
NOVIAM_LIGHT_BLUE = "#00c3f5"
NOVIAM_GRAY = "#626366"
NOVIAM_WHITE = "#ffffff"

# Custom color scales for charts
NOVIAM_BLUE_SCALE = [
    [0, NOVIAM_LIGHT_BLUE],
    [0.5, NOVIAM_MID_BLUE],
    [1, NOVIAM_BLUE]
]

NOVIAM_PIE_COLORS = [
    NOVIAM_BLUE,
    NOVIAM_MID_BLUE,
    NOVIAM_LIGHT_BLUE,
    "#3385ff",  # lighter mid blue
    "#66a3ff",  # even lighter
    "#99c2ff",  # very light
    "#cce0ff",  # pale blue
    "#e6f0ff",  # almost white blue
]

# Load data
print("Loading data...")
institutions = pd.read_csv("fdic_institutions.csv")
locations = pd.read_csv("fdic_locations.csv", low_memory=False)

# Clean up data
institutions["CERT"] = institutions["CERT"].astype(str)
locations["CERT"] = locations["CERT"].astype(str)

# Get unique states from locations for filtering
all_states = sorted(locations["STNAME"].dropna().unique())

# Create institution options for dropdown
institution_options = [
    {"label": f"{row['NAME']} (CERT: {row['CERT']})", "value": row["CERT"]}
    for _, row in institutions.sort_values("NAME").iterrows()
]

# Initialize app with Google Fonts
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap"
]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "FDIC Bank Explorer"

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("FDIC Bank Explorer", style={"margin": "0", "color": NOVIAM_WHITE}),
        html.P("Explore FDIC-insured institutions and their branch locations",
               style={"margin": "5px 0 0 0", "color": NOVIAM_LIGHT_BLUE})
    ], style={
        "backgroundColor": NOVIAM_BLUE,
        "padding": "20px",
        "marginBottom": "20px"
    }),

    # Filters section
    html.Div([
        html.Div([
            html.Label("Filter by State:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="state-filter",
                options=[{"label": "All States", "value": "ALL"}] +
                        [{"label": s, "value": s} for s in all_states],
                value="ALL",
                clearable=False,
                style={"marginTop": "5px"}
            )
        ], style={"width": "22%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "15px"}),

        html.Div([
            html.Label("Filter by County:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="county-filter",
                options=[{"label": "All Counties", "value": "ALL"}],
                value="ALL",
                clearable=False,
                placeholder="Select a state first...",
                style={"marginTop": "5px"}
            )
        ], style={"width": "22%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "15px"}),

        html.Div([
            html.Label("Select Institution:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="institution-dropdown",
                options=institution_options,
                placeholder="Search for an institution...",
                style={"marginTop": "5px"}
            )
        ], style={"width": "50%", "display": "inline-block", "verticalAlign": "top"})
    ], style={"padding": "0 20px", "marginBottom": "20px"}),

    # Institution info card
    html.Div(id="institution-info", style={"padding": "0 20px", "marginBottom": "20px"}),

    # Main content - Map and Charts
    html.Div([
        # Map
        html.Div([
            html.H3("Branch Locations Map", style={"marginTop": "0"}),
            dcc.Graph(id="branch-map", style={"height": "500px"})
        ], style={"width": "50%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "10px"}),

        # Charts
        html.Div([
            html.H3("Branches by State", style={"marginTop": "0"}),
            dcc.Graph(id="state-bar-chart", style={"height": "240px"}),
            dcc.Graph(id="state-pie-chart", style={"height": "290px"})
        ], style={"width": "24%", "display": "inline-block", "verticalAlign": "top", "paddingRight": "10px"}),

        # County chart
        html.Div([
            html.H3("Branches by County", style={"marginTop": "0"}),
            dcc.Graph(id="county-bar-chart", style={"height": "490px"})
        ], style={"width": "24%", "display": "inline-block", "verticalAlign": "top"})
    ], style={"padding": "0 20px", "marginBottom": "20px"}),

    # Institutions in area section (shown when state/county selected but no institution)
    html.Div(id="institutions-in-area-section", style={"padding": "0 20px", "marginBottom": "20px"}),

    # Hidden stores for chart click selections
    dcc.Store(id="chart-state-filter", data=None),
    dcc.Store(id="chart-county-filter", data=None),

    # Branch details table
    html.Div([
        html.H3("Branch Details"),
        html.Div(id="table-filter-info", style={"marginBottom": "10px", "color": NOVIAM_GRAY, "fontStyle": "italic"}),
        dash_table.DataTable(
            id="branch-table",
            columns=[
                {"name": "Institution", "id": "NAME"},
                {"name": "Branch Name", "id": "OFFNAME"},
                {"name": "Address", "id": "ADDRESS"},
                {"name": "City", "id": "CITY"},
                {"name": "County", "id": "COUNTY"},
                {"name": "State", "id": "STNAME"},
                {"name": "ZIP", "id": "ZIP"},
                {"name": "Service Type", "id": "SERVTYPE_DESC"},
                {"name": "Main Office", "id": "MAINOFF"},
                {"name": "Established", "id": "ESTYMD"}
            ],
            page_size=15,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "10px",
                "fontSize": "13px"
            },
            style_header={
                "backgroundColor": NOVIAM_BLUE,
                "color": NOVIAM_WHITE,
                "fontWeight": "bold"
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f0f7ff"}
            ]
        )
    ], style={"padding": "0 20px", "marginBottom": "40px"})

], style={"fontFamily": "'Montserrat', Arial, sans-serif", "maxWidth": "1600px", "margin": "0 auto"})


@callback(
    Output("county-filter", "options"),
    Output("county-filter", "value"),
    Input("state-filter", "value")
)
def update_county_options(selected_state):
    """Update county dropdown based on selected state."""
    if selected_state == "ALL":
        return [{"label": "All Counties", "value": "ALL"}], "ALL"

    # Get counties in the selected state
    counties_in_state = sorted(locations[locations["STNAME"] == selected_state]["COUNTY"].dropna().unique())
    options = [{"label": "All Counties", "value": "ALL"}] + [{"label": c, "value": c} for c in counties_in_state]
    return options, "ALL"


@callback(
    Output("institution-dropdown", "options"),
    Input("state-filter", "value"),
    Input("county-filter", "value")
)
def update_institution_options(selected_state, selected_county):
    """Filter institution dropdown based on selected state and county."""
    filtered_locations = locations

    if selected_state != "ALL":
        filtered_locations = filtered_locations[filtered_locations["STNAME"] == selected_state]

    if selected_county != "ALL":
        filtered_locations = filtered_locations[filtered_locations["COUNTY"] == selected_county]

    # Get CERTs of institutions that have branches in the filtered area
    certs_in_area = filtered_locations["CERT"].unique()
    filtered_institutions = institutions[institutions["CERT"].isin(certs_in_area)]

    return [
        {"label": f"{row['NAME']} (CERT: {row['CERT']})", "value": row["CERT"]}
        for _, row in filtered_institutions.sort_values("NAME").iterrows()
    ]


@callback(
    [Output("institution-info", "children"),
     Output("branch-map", "figure"),
     Output("state-bar-chart", "figure"),
     Output("state-pie-chart", "figure")],
    [Input("institution-dropdown", "value"),
     Input("state-filter", "value"),
     Input("county-filter", "value")]
)
def update_dashboard(cert, state_filter, county_filter):
    """Update all dashboard components when institution is selected."""

    # Default empty state
    empty_map = go.Figure()
    empty_map.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    empty_map.add_annotation(
        text="Select an institution to view branch locations",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="gray")
    )

    empty_bar = go.Figure()
    empty_bar.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=230)

    empty_pie = go.Figure()
    empty_pie.update_layout(margin=dict(l=0, r=0, t=10, b=50), height=280)

    if not cert:
        return (
            html.Div("Select an institution to view details", style={"color": "gray", "fontStyle": "italic"}),
            empty_map,
            empty_bar,
            empty_pie
        )

    # Get institution details
    inst = institutions[institutions["CERT"] == cert].iloc[0]

    # Get branch locations for this institution
    branches = locations[locations["CERT"] == cert].copy()

    if branches.empty:
        return (
            html.Div(f"No branch data found for {inst['NAME']}", style={"color": "gray"}),
            empty_map,
            empty_bar,
            empty_pie
        )

    # Institution info card
    info_card = html.Div([
        html.Div([
            html.H2(inst["NAME"], style={"margin": "0 0 10px 0", "color": NOVIAM_BLUE}),
            html.Div([
                html.Span(f"CERT: {inst['CERT']}", style={"marginRight": "20px"}),
                html.Span(f"Charter: {inst['CHARTER']}", style={"marginRight": "20px"}),
                html.Span(f"Class: {inst['BKCLASS']}", style={"marginRight": "20px"}),
                html.Span(f"Total Branches: {len(branches)}", style={"fontWeight": "bold", "color": NOVIAM_MID_BLUE})
            ], style={"color": NOVIAM_GRAY}),
            html.Div([
                html.Span(f"HQ: {inst['ADDRESS']}, {inst['CITY']}, {inst['STNAME']} {inst['ZIP']}")
            ], style={"marginTop": "5px", "color": NOVIAM_GRAY}) if pd.notna(inst.get("ADDRESS")) else None
        ])
    ], style={
        "backgroundColor": "#f0f7ff",
        "padding": "15px 20px",
        "borderRadius": "8px",
        "borderLeft": f"4px solid {NOVIAM_BLUE}"
    })

    # Filter out branches without coordinates
    branches_with_coords = branches.dropna(subset=["LATITUDE", "LONGITUDE"])

    # Create map
    if not branches_with_coords.empty:
        fig_map = px.scatter_mapbox(
            branches_with_coords,
            lat="LATITUDE",
            lon="LONGITUDE",
            hover_name="OFFNAME",
            hover_data={
                "CITY": True,
                "COUNTY": True,
                "STNAME": True,
                "ADDRESS": True,
                "SERVTYPE_DESC": True,
                "LATITUDE": False,
                "LONGITUDE": False
            },
            color="STNAME",
            zoom=3,
            mapbox_style="carto-positron"
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # Auto-zoom to fit all points
        if len(branches_with_coords) > 1:
            fig_map.update_layout(
                mapbox=dict(
                    center=dict(
                        lat=branches_with_coords["LATITUDE"].mean(),
                        lon=branches_with_coords["LONGITUDE"].mean()
                    ),
                    zoom=4
                )
            )
    else:
        fig_map = empty_map
        fig_map.add_annotation(text="No location coordinates available", x=0.5, y=0.5,
                               xref="paper", yref="paper", showarrow=False)

    # State breakdown charts
    state_counts = branches["STNAME"].value_counts().reset_index()
    state_counts.columns = ["State", "Branches"]

    # Bar chart (top 10 states)
    top_states = state_counts.head(10)
    fig_bar = px.bar(
        top_states,
        x="State",
        y="Branches",
        color="Branches",
        color_continuous_scale=NOVIAM_BLUE_SCALE
    )
    fig_bar.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=230,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="Branches"
    )

    # Pie chart
    fig_pie = px.pie(
        state_counts.head(8),  # Top 8 for readability
        values="Branches",
        names="State",
        color_discrete_sequence=NOVIAM_PIE_COLORS
    )
    fig_pie.update_layout(
        margin=dict(l=0, r=0, t=10, b=50),
        height=280,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5)
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")

    return info_card, fig_map, fig_bar, fig_pie


@callback(
    Output("county-bar-chart", "figure"),
    [Input("institution-dropdown", "value"),
     Input("state-filter", "value"),
     Input("chart-state-filter", "data")]
)
def update_county_chart(cert, state_filter, chart_state_filter):
    """Update county chart based on institution and state selection (including chart clicks)."""

    empty_county = go.Figure()
    empty_county.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=490)

    if not cert:
        return empty_county

    # Get branch locations for this institution
    branches = locations[locations["CERT"] == cert].copy()

    if branches.empty:
        return empty_county

    # Determine which state filter to use (chart click takes precedence over dropdown)
    active_state_filter = chart_state_filter if chart_state_filter else (state_filter if state_filter != "ALL" else None)

    # Filter by state if selected
    if active_state_filter:
        county_data = branches[branches["STNAME"] == active_state_filter]
        chart_title = f"Branches by County ({active_state_filter})"
    else:
        county_data = branches
        chart_title = "Branches by County (All States)"

    if county_data.empty:
        empty_county.add_annotation(
            text=f"No branches in {active_state_filter}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=NOVIAM_GRAY)
        )
        return empty_county

    county_counts = county_data["COUNTY"].value_counts().reset_index()
    county_counts.columns = ["County", "Branches"]

    # Show top 15 counties
    top_counties = county_counts.head(15)
    fig_county = px.bar(
        top_counties,
        y="County",
        x="Branches",
        orientation="h",
        color="Branches",
        color_continuous_scale=NOVIAM_BLUE_SCALE
    )
    fig_county.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=490,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Branches",
        yaxis_title="",
        yaxis=dict(autorange="reversed"),
        title=dict(text=chart_title, font=dict(size=12, color=NOVIAM_GRAY))
    )

    return fig_county


@callback(
    Output("institutions-in-area-section", "children"),
    [Input("institution-dropdown", "value"),
     Input("state-filter", "value"),
     Input("county-filter", "value")]
)
def update_institutions_in_area(cert, state_filter, county_filter):
    """Show institutions in the selected area when no specific institution is selected."""

    # Only show when no institution selected but area is filtered
    if cert or (state_filter == "ALL" and county_filter == "ALL"):
        return None

    # Get branches in the filtered area
    filtered_branches = locations.copy()
    area_description = []

    if state_filter != "ALL":
        filtered_branches = filtered_branches[filtered_branches["STNAME"] == state_filter]
        area_description.append(state_filter)
    if county_filter != "ALL":
        filtered_branches = filtered_branches[filtered_branches["COUNTY"] == county_filter]
        area_description.append(f"{county_filter} County")

    # Count branches by institution
    inst_counts = filtered_branches.groupby(["CERT", "NAME"]).size().reset_index(name="Branches")
    inst_counts = inst_counts.sort_values("Branches", ascending=False)

    # Create horizontal bar chart showing top 20 institutions
    top_institutions = inst_counts.head(20)

    fig = px.bar(
        top_institutions,
        y="NAME",
        x="Branches",
        orientation="h",
        color="Branches",
        color_continuous_scale=NOVIAM_BLUE_SCALE,
        title=f"Top Institutions in {', '.join(area_description)} ({len(inst_counts)} total)"
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=400,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Number of Branches",
        yaxis_title="",
        yaxis=dict(autorange="reversed")
    )

    return html.Div([
        html.H3(f"Institutions Operating in {', '.join(area_description)}", style={"marginTop": "0", "color": NOVIAM_BLUE}),
        html.P(f"{len(inst_counts):,} institutions with {len(filtered_branches):,} total branches",
               style={"color": NOVIAM_GRAY, "marginBottom": "10px"}),
        dcc.Graph(figure=fig, style={"height": "400px"})
    ])


@callback(
    Output("chart-state-filter", "data"),
    [Input("state-bar-chart", "clickData"),
     Input("state-pie-chart", "clickData"),
     Input("state-filter", "value"),
     Input("institution-dropdown", "value")],
    State("chart-state-filter", "data")
)
def update_chart_state_filter(bar_click, pie_click, dropdown_state, institution, current_state):
    """Update state filter based on chart clicks."""
    triggered_id = ctx.triggered_id

    # Reset when dropdown filter changes or institution changes
    if triggered_id in ["state-filter", "institution-dropdown"]:
        return None

    # Handle bar chart click
    if triggered_id == "state-bar-chart" and bar_click:
        clicked_state = bar_click["points"][0]["x"]
        # Toggle: if clicking same state, clear filter
        if current_state == clicked_state:
            return None
        return clicked_state

    # Handle pie chart click
    if triggered_id == "state-pie-chart" and pie_click:
        clicked_state = pie_click["points"][0]["label"]
        if current_state == clicked_state:
            return None
        return clicked_state

    return current_state


@callback(
    Output("chart-county-filter", "data"),
    [Input("county-bar-chart", "clickData"),
     Input("state-filter", "value"),
     Input("county-filter", "value"),
     Input("institution-dropdown", "value"),
     Input("chart-state-filter", "data")],
    State("chart-county-filter", "data")
)
def update_chart_county_filter(county_click, dropdown_state, dropdown_county, institution, chart_state, current_county):
    """Update county filter based on chart clicks."""
    triggered_id = ctx.triggered_id

    # Reset when dropdown filters change, institution changes, or state chart filter changes
    if triggered_id in ["state-filter", "county-filter", "institution-dropdown", "chart-state-filter"]:
        return None

    # Handle county chart click
    if triggered_id == "county-bar-chart" and county_click:
        clicked_county = county_click["points"][0]["y"]
        # Toggle: if clicking same county, clear filter
        if current_county == clicked_county:
            return None
        return clicked_county

    return current_county


@callback(
    [Output("branch-table", "data"),
     Output("table-filter-info", "children")],
    [Input("institution-dropdown", "value"),
     Input("state-filter", "value"),
     Input("county-filter", "value"),
     Input("chart-state-filter", "data"),
     Input("chart-county-filter", "data")]
)
def update_branch_table(cert, state_filter, county_filter, chart_state, chart_county):
    """Update branch table based on all filters including chart clicks."""

    # If no institution selected, show all branches filtered by state/county
    if not cert:
        if state_filter == "ALL" and county_filter == "ALL":
            return [], "Select a state/county to view all branches, or select an institution"

        # Get all branches filtered by state/county
        table_branches = locations.copy()
        filter_info_parts = []

        if state_filter != "ALL":
            table_branches = table_branches[table_branches["STNAME"] == state_filter]
            filter_info_parts.append(f"State: {state_filter}")
        if county_filter != "ALL":
            table_branches = table_branches[table_branches["COUNTY"] == county_filter]
            filter_info_parts.append(f"County: {county_filter}")

        filter_info = f"Showing all branches in {', '.join(filter_info_parts)} ({len(table_branches):,} branches from all institutions)"

        table_data = table_branches[["NAME", "OFFNAME", "ADDRESS", "CITY", "COUNTY", "STNAME", "ZIP", "SERVTYPE_DESC", "MAINOFF", "ESTYMD"]].fillna("").to_dict("records")
        return table_data, filter_info

    # Get branch locations for this institution
    branches = locations[locations["CERT"] == cert].copy()

    if branches.empty:
        return [], ""

    # Apply dropdown filters
    table_branches = branches
    if state_filter != "ALL":
        table_branches = table_branches[table_branches["STNAME"] == state_filter]
    if county_filter != "ALL":
        table_branches = table_branches[table_branches["COUNTY"] == county_filter]

    # Apply chart click filters
    filter_info_parts = []
    if chart_state:
        table_branches = table_branches[table_branches["STNAME"] == chart_state]
        filter_info_parts.append(f"State: {chart_state}")
    if chart_county:
        table_branches = table_branches[table_branches["COUNTY"] == chart_county]
        filter_info_parts.append(f"County: {chart_county}")

    # Build filter info message
    if filter_info_parts:
        filter_info = f"Filtered by chart selection: {', '.join(filter_info_parts)} (click again to clear)"
    else:
        filter_info = "Click on a state or county chart to filter"

    table_data = table_branches[["NAME", "OFFNAME", "ADDRESS", "CITY", "COUNTY", "STNAME", "ZIP", "SERVTYPE_DESC", "MAINOFF", "ESTYMD"]].fillna("").to_dict("records")

    return table_data, filter_info


# Expose server for gunicorn
server = app.server

if __name__ == "__main__":
    import os
    print("\n" + "=" * 60)
    print("FDIC Bank Explorer Dashboard")
    print("=" * 60)
    print(f"Loaded {len(institutions):,} institutions")
    print(f"Loaded {len(locations):,} branch locations")
    print("\nStarting server...")
    print("Open your browser to: http://127.0.0.1:8050")
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    # Use PORT env variable for cloud hosting, default to 8050 for local
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "True").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
