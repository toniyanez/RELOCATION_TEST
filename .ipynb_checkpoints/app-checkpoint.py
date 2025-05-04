import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px

# Load data from CSV files
brand_data = pd.read_csv('Data/brand.csv')
competitors_data = pd.read_csv('Data/competitors.csv')
supply_chain_data = pd.read_csv('Data/Competitors_Supply_chain.csv')

# Initialize the Dash app
app = Dash(__name__)

# Layout of the dashboard
app.layout = html.Div([
    html.H1("DASHBOARD", style={'text-align': 'center'}),

    # Tabs for navigation
    dcc.Tabs([
        dcc.Tab(label='MAIN', children=[
            html.Div([
                html.Label("Business Unit:"),
                dcc.Dropdown(
                    id='business-unit-dropdown',
                    options=[{'label': bu, 'value': bu} for bu in brand_data['business_unit'].unique()],
                    placeholder="Select a Business Unit"
                )
            ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'top'}),

            # Bar chart for brands and brand details table
            html.Div([
                dcc.Graph(id='brand-bar-chart'),
                dash_table.DataTable(
                    id='brand-details-table',
                    columns=[
                        {"name": "Brand Name", "id": "brand_name"},
                        {"name": "Revenue (USD)", "id": "brand_revenue_USD"},
                        {"name": "Description", "id": "description"}
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    filter_action="native",
                    sort_action="native",
                    page_size=10
                )
            ], style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'top'}),

            # Competitors table and supplier bar chart
            html.Div([
                html.H3("Competitors Table"),
                dash_table.DataTable(
                    id='competitors-table',
                    columns=[
                        {"name": "Competitor ID", "id": "competitor_id"},
                        {"name": "Competitor Name", "id": "competitor_name"},
                        {"name": "Brand ID", "id": "brand_id"},
                        {"name": "Revenue (USD)", "id": "revenue_usd"}
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    filter_action="native",
                    sort_action="native",
                    page_size=10
                ),
                html.H3("Supplier Bar Chart"),
                dcc.Graph(id='supplier-bar-chart')
            ], style={'width': '35%', 'display': 'inline-block', 'vertical-align': 'top'})
        ]),

        dcc.Tab(label='Relocation Simulation', children=[
            html.Div([
                html.H3("Radar Chart for Country Proposal"),
                dcc.Graph(id='radar-chart')
            ], style={'width': '100%', 'display': 'inline-block', 'margin-top': '20px'})
        ])
    ])
])

# Callback to update the brand bar chart and brand details table
@app.callback(
    [Output('brand-bar-chart', 'figure'),
     Output('brand-details-table', 'data')],
    [Input('business-unit-dropdown', 'value'),
     Input('brand-bar-chart', 'clickData')]
)
def update_brand_chart_and_table(selected_business_unit, click_data):
    if selected_business_unit:
        filtered_brands = brand_data[brand_data['business_unit'] == selected_business_unit]

        # Create the bar chart
        bar_chart = px.bar(
            filtered_brands.sort_values(by='brand_revenue_USD', ascending=False),
            x='brand_name',
            y='brand_revenue_USD',
            title='Revenue by Brand (in Millions USD)',
            color='brand_name',
            text='brand_revenue_USD'
        )
        bar_chart.update_traces(texttemplate='%{text:.2s}', textposition='outside')

        # Filter the table based on clicked bar(s)
        selected_brands = []
        if click_data:
            selected_brands = [point['x'] for point in click_data['points']]
            filtered_brands = filtered_brands[filtered_brands['brand_name'].isin(selected_brands)]

        return bar_chart, filtered_brands.to_dict('records')

    return {}, []

# Callback to update the competitors table and supplier bar chart
@app.callback(
    [Output('competitors-table', 'data'),
     Output('supplier-bar-chart', 'figure')],
    [Input('business-unit-dropdown', 'value'),
     Input('brand-bar-chart', 'clickData')]
)
def update_competitors_and_suppliers(selected_business_unit, click_data):
    if selected_business_unit:
        # Filter brands by the selected business unit
        filtered_brands = brand_data[brand_data['business_unit'] == selected_business_unit]
        relevant_brand_ids = filtered_brands['brand_id'].astype(str).tolist()

        # Filter competitors based on the relevant brand IDs
        def has_relevant_brand_id(row):
            competitor_brand_ids = row['brand_id'].split(',')  # Split the brand_id field by commas
            return any(brand_id in relevant_brand_ids for brand_id in competitor_brand_ids)

        filtered_competitors = competitors_data[competitors_data.apply(has_relevant_brand_id, axis=1)]

        # Filter supply chain data for the selected competitor
        selected_competitors = []
        if click_data:
            selected_competitors = [point['x'] for point in click_data['points']]
            filtered_competitors = filtered_competitors[filtered_competitors['competitor_name'].isin(selected_competitors)]

        relevant_competitor_ids = filtered_competitors['competitor_id'].tolist()
        filtered_supply_chain = supply_chain_data[supply_chain_data['competitor_id'].isin(relevant_competitor_ids)]

        # Create the supplier bar chart
        supplier_chart = px.bar(
            filtered_supply_chain,
            x='competitor_supplier_country',
            y='Proportion_imports',
            title='Supplier Proportion by Country',
            color='competitor_name',
            text='Proportion_imports'
        )
        supplier_chart.update_traces(texttemplate='%{text:.2s}', textposition='outside')

        return filtered_competitors.to_dict('records'), supplier_chart

    return [], {}

# Run the app
if __name__ == '__main__':
    app.run(debug=True)