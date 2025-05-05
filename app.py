import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table, State
import plotly.express as px
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load data from CSV files
brand_data = pd.read_csv('Data/brand.csv')
competitors_data = pd.read_csv('Data/competitors.csv')
supply_chain_data = pd.read_csv('Data/Competitors_Supply_chain.csv')

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

# Layout of the dashboard
app.layout = html.Div([
    html.H1("DASHBOARD", style={'text-align': 'center'}),

    # Tabs for navigation
    dcc.Tabs([
        dcc.Tab(label='MAIN', children=[
            html.Div([
                # Left Panel: Filter by Business Unit and Simulation Inputs
                html.Div([
                    html.H3("Filter by Business Unit"),
                    dcc.Dropdown(
                        id='business-unit-dropdown',
                        options=[{'label': bu, 'value': bu} for bu in brand_data['business_unit'].unique()],
                        placeholder="Select a Business Unit",
                        style={'margin-bottom': '20px'}
                    ),
                    html.H3("Simulation Inputs"),
                    html.Label("Tariff Increase (%)"),
                    dcc.Input(id='tariff-increase-input', type='number', placeholder="Enter % increase", style={'margin-bottom': '10px'}),
                    html.Button("Apply Scenario", id='apply-scenario-button', n_clicks=0),
                    html.Div([
                        html.H4("Baseline Metrics"),
                        html.Div(id='baseline-card', style={'margin-top': '20px'})
                    ])
                ], style={
                    'width': '20%',
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'padding': '10px',
                    'border-right': '1px solid #ccc'
                }),

                # Central Panel: Revenue by Brand Chart
                html.Div([
                    html.H3("Revenue by Brand"),
                    dcc.Graph(id='brand-bar-chart'),
                    # Add placeholders for the charts in the layout
                    html.Div([
                        dcc.Graph(id='profit-impact-bar-chart-main'),
                        dcc.Graph(id='cogs-pie-chart-main'),
                        dcc.Graph(id='profit-margin-line-chart-main')
                    ], style={'width': '100%', 'display': 'inline-block'}),
                ], style={
                    'width': '50%',
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'padding': '10px',
                    'text-align': 'center'
                }),

                # Right Panel: Brand Details Table and OpenAI Table
                html.Div([
                    html.H3("Brand Details"),
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
                    ),
                    html.H3("OpenAI Tariff Table"),
                    dash_table.DataTable(
                        id='openai-tariff-table',
                        columns=[
                            {"name": "Category", "id": "category"},
                            {"name": "Tariff Applied", "id": "tariff"}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        page_size=10
                    )
                ], style={
                    'width': '30%',
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'padding': '10px',
                    'border-left': '1px solid #ccc'
                })
            ], style={'display': 'flex', 'width': '100%'})
        ]),

        dcc.Tab(label='Competitors', children=[
            html.Div([
                html.H3("Competitors Overview"),
                html.Label("Tariff Increase (%)"),
                dcc.Input(id='competitor-tariff-increase-input', type='number', placeholder="Enter % increase", style={'margin-bottom': '10px'}),
                html.Button("Apply Scenario", id='apply-competitor-scenario-button', n_clicks=0),
                dcc.Graph(id='competitor-profit-impact-bar-chart'),
                dcc.Graph(id='competitor-cogs-pie-chart'),
                dcc.Graph(id='competitor-profit-margin-line-chart')
            ], style={'width': '100%', 'display': 'inline-block'})
        ]),

        dcc.Tab(label='Relocation Simulation', children=[
            html.Div([
                html.H3("Relocation Simulation"),
                html.Label("Select a Brand"),
                dcc.Dropdown(
                    id='relocation-brand-dropdown',
                    options=[{'label': brand, 'value': brand} for brand in brand_data['brand_name'].unique()],
                    placeholder="Select a Brand",
                    style={'margin-bottom': '20px'}
                ),
                dcc.Graph(id='relocation-radar-chart'),
                html.Div(id='relocation-conclusion', style={'margin-top': '20px'}),
                html.H3("Chat with OpenAI Agent"),
                html.Div(
                    id='chat-container',
                    style={
                        'width': '100%',
                        'height': '400px',  # Increase the height of the chat box
                        'overflow-y': 'scroll',  # Enable vertical scrolling
                        'border': '1px solid #ccc',
                        'padding': '10px',
                        'border-radius': '5px',
                        'background-color': '#f9f9f9',
                        'whiteSpace': 'pre-line'
                    }
                ),
                dcc.Input(
                    id='chat-input',
                    placeholder="Type your message here and press Enter...",
                    style={'width': '100%', 'margin-top': '10px', 'padding': '10px'},
                    type='text',
                    n_submit=0  # Detect Enter key press
                )
            ], style={'width': '100%', 'display': 'inline-block', 'margin-top': '20px'})
        ])
    ])
])

# Simulate AI-based product categorization and tariff retrieval using OpenAI
def interpret_description_with_openai(brand_name_or_category, description):
    prompt = f"""
    The brand or product category "{brand_name_or_category}" specializes in the following: {description}.
    For each product category, provide the following details in the format:
    "Product_category", "Tariff Applied", "Country", "Comments related to the tariffs".
    Ensure the response is structured as a table with one row per product category.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that extracts product categories and retrieves tariff information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )
    print("Raw OpenAI Response:", response)  # Log the raw response

    # Parse the response
    results = response['choices'][0]['message']['content'].strip().split("\n")
    structured_data = []
    for result in results:
        parts = result.split(",")  # Split by comma
        if len(parts) == 4:
            structured_data.append({
                "product": parts[0].strip(),
                "tariff": parts[1].strip(),
                "country": parts[2].strip(),
                "comments": parts[3].strip()
            })
    return structured_data

# Callback to update the brand bar chart and brand details table
@app.callback(
    [Output('brand-bar-chart', 'figure'),
     Output('brand-details-table', 'data')],
    Input('business-unit-dropdown', 'value')
)
def update_brand_chart_and_table(selected_business_unit):
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

        return bar_chart, filtered_brands.to_dict('records')

    return {}, []

# Callback to update baseline metrics
@app.callback(
    Output('baseline-card', 'children'),
    Input('business-unit-dropdown', 'value')
)
def update_baseline_metrics(selected_business_unit):
    if selected_business_unit:
        filtered_brands = brand_data[brand_data['business_unit'] == selected_business_unit]
        total_revenue = filtered_brands['brand_revenue_USD'].sum()
        baseline_profit = total_revenue * 0.5
        baseline_cogs = total_revenue - baseline_profit
        tariff_trade_costs = baseline_cogs * 0.45  # 45% of COGS is tariff trade costs

        return html.Div([
            html.P(f"Current Revenue: ${total_revenue:,.2f}"),
            html.P(f"Baseline Profit Margin: 50%"),
            html.P(f"Baseline COGS: ${baseline_cogs:,.2f}"),
            html.P(f"Tariff Trade Costs: ${tariff_trade_costs:,.2f}")
        ])

    return html.Div([
        html.P("Select a Business Unit to view baseline metrics.")
    ])

# Callback to simulate tariff impact
@app.callback(
    [Output('profit-impact-bar-chart-main', 'figure'),
     Output('cogs-pie-chart-main', 'figure'),
     Output('profit-margin-line-chart-main', 'figure')],
    [Input('apply-scenario-button', 'n_clicks')],
    [State('tariff-increase-input', 'value'),
     State('business-unit-dropdown', 'value')]
)
def simulate_tariff_impact(n_clicks, tariff_increase, selected_business_unit):
    if n_clicks > 0 and tariff_increase and selected_business_unit:
        # Filter data for the selected business unit
        filtered_brands = brand_data[brand_data['business_unit'] == selected_business_unit]
        total_revenue = filtered_brands['brand_revenue_USD'].sum()
        baseline_profit = filtered_brands['brand_revenue_USD'] * 0.5
        baseline_cogs = filtered_brands['brand_revenue_USD'] - baseline_profit
        tariff_trade_costs = baseline_cogs * 0.45  # 45% of COGS is tariff trade costs

        # Scenario calculations
        new_tariff_trade_costs = tariff_trade_costs * (1 + tariff_increase / 100)
        new_cogs = baseline_cogs + (new_tariff_trade_costs - tariff_trade_costs)
        new_profit = filtered_brands['brand_revenue_USD'] - new_cogs

        # Reshape data for the bar chart
        profit_data = pd.DataFrame({
            'Brand': filtered_brands['brand_name'],
            'Baseline Profit': baseline_profit,
            'New Profit': new_profit
        }).melt(id_vars='Brand', var_name='Scenario', value_name='Profit')

        # Bar Chart: Profit Impact by Brand
        profit_impact_chart = px.bar(
            profit_data,
            x='Brand',
            y='Profit',
            color='Scenario',
            title='Profit Impact by Brand',
            barmode='group',
            labels={'Profit': 'Profit (USD)', 'Scenario': 'Scenario'}
        )

        # Pie Chart: COGS Breakdown
        cogs_pie_chart = px.pie(
            values=[baseline_cogs.sum(), new_tariff_trade_costs.sum()],
            names=['Baseline COGS', 'Increased Tariff Costs'],
            title='COGS Breakdown'
        )

        # Line Chart: Profit Margin Change
        baseline_margin = (baseline_profit.sum() / total_revenue) * 100
        new_margin = (new_profit.sum() / total_revenue) * 100
        profit_margin_chart = px.line(
            x=['Baseline', 'New'],
            y=[baseline_margin, new_margin],
            title='Profit Margin Change',
            labels={'x': 'Scenario', 'y': 'Profit Margin (%)'}
        )

        return profit_impact_chart, cogs_pie_chart, profit_margin_chart

    return {}, {}, {}

# Callback to update OpenAI Tariff Table
@app.callback(
    Output('openai-tariff-table', 'data'),
    Input('business-unit-dropdown', 'value')
)
def update_openai_tariff_table(selected_business_unit):
    if selected_business_unit:
        # Get the products for the selected business unit
        filtered_brands = brand_data[brand_data['business_unit'] == selected_business_unit]
        products = filtered_brands['description'].tolist()

        # Combine product descriptions into a single prompt
        prompt = f"""
        You are an expert on trade tariffs between China and the USA. Look for each of these products:
        {', '.join(products)}.
        Provide the tariff trade applied (cumulative) for each product in the format:
        "Category, Tariff Applied".
        If you don't find anything, reply "9999".
        """

        # Query OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that provides trade tariff information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        print("Raw OpenAI Response:", response)  # Log the raw response

        # Parse the OpenAI response
        results = response['choices'][0]['message']['content'].strip().split("\n")
        tariff_data = []
        for result in results:
            parts = result.split(",")  # Split by comma
            if len(parts) == 2:
                tariff_data.append({
                    "category": parts[0].strip(),
                    "tariff": parts[1].strip()
                })

        # Log the parsed data for debugging
        print("Parsed Tariff Data:", tariff_data)

        return tariff_data

    return []

# Callback to simulate competitor tariff impact
@app.callback(
    [Output('competitor-profit-impact-bar-chart', 'figure')],
    [Input('apply-competitor-scenario-button', 'n_clicks')],
    [State('competitor-tariff-increase-input', 'value')]
)
def simulate_competitor_tariff_impact(n_clicks, tariff_increase):
    if n_clicks > 0 and tariff_increase:
        # Filter supply chain data for China
        china_supply_chain = supply_chain_data[supply_chain_data['competitor_supplier_country'] == 'China']

        # Merge competitors data with filtered supply chain data
        competitors = competitors_data.merge(
            china_supply_chain[['competitor_name', 'Proportion_imports']],
            on='competitor_name',
            how='left'
        )

        # Convert Proportion_imports to numeric and handle non-numeric values
        competitors['Proportion_imports'] = pd.to_numeric(competitors['Proportion_imports'], errors='coerce').fillna(0)

        # Calculate baseline profit and COGS
        competitors['baseline_profit'] = competitors['revenue_usd'] * 0.5
        competitors['baseline_cogs'] = competitors['revenue_usd'] - competitors['baseline_profit']

        # Calculate tariff costs for China (existing + scenario tariff)
        competitors['china_tariff_cost'] = competitors['baseline_cogs'] * (competitors['Proportion_imports'] / 100) * (tariff_increase / 100)

        # Calculate new COGS and profit
        competitors['new_cogs'] = competitors['baseline_cogs'] + competitors['china_tariff_cost']
        competitors['new_profit'] = competitors['revenue_usd'] - competitors['new_cogs']

        # Reshape data for the bar chart
        profit_data = pd.DataFrame({
            'Competitor': competitors['competitor_name'],
            'Baseline Profit': competitors['baseline_profit'],
            'New Profit': competitors['new_profit']
        }).melt(id_vars='Competitor', var_name='Scenario', value_name='Profit')

        # Bar Chart: Profit Impact by Competitor
        profit_impact_chart = px.bar(
            profit_data,
            x='Competitor',
            y='Profit',
            color='Scenario',
            title='Profit Impact by Competitor',
            barmode='group',
            labels={'Profit': 'Profit (USD)', 'Scenario': 'Scenario'}
        )

        return [profit_impact_chart]

    return [{}]

# Callback to find alternative suppliers
@app.callback(
    Output('radar-chart', 'figure'),
    Input('apply-scenario-button', 'n_clicks')
)
def find_alternative_suppliers(n_clicks):
    if n_clicks > 0:
        # Combine product and brand descriptions into a single prompt
        products_and_brands = brand_data[['brand_name', 'description']].drop_duplicates()
        prompt = "You are an expert in global trade. Suggest alternative suppliers for the following products and brands currently sourced from China:\n"
        for _, row in products_and_brands.iterrows():
            prompt += f"- {row['brand_name']}: {row['description']}\n"

        # Query OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that provides alternative supplier recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        print("Raw OpenAI Response:", response)  # Log the raw response

        # Parse the OpenAI response
        results = response['choices'][0]['message']['content'].strip().split("\n")
        supplier_data = []
        for result in results:
            supplier_data.append({"Alternative Supplier": result.strip()})

        # Create a radar chart (or table if preferred)
        radar_chart = px.bar(
            pd.DataFrame(supplier_data),
            x="Alternative Supplier",
            y=[1] * len(supplier_data),  # Dummy values for visualization
            title="Alternative Suppliers for Products and Brands",
            labels={"y": "Relevance"}
        )

        return radar_chart

    return {}

# Callback for relocation recommendations
@app.callback(
    Output('relocation-conclusion', 'children'),
    Input('relocation-brand-dropdown', 'value')
)
def relocation_recommendations(selected_brand):
    if selected_brand:
        # Prompt for OpenAI
        prompt = f"""
        You are an experienced Supply chain manager, working at Revelyst Group (1.2B revenues, 49% dependency on China suppliers).
        For the brand "{selected_brand}", analyze relocation alternatives for the following product categories:
        {', '.join(brand_data[brand_data['brand_name'] == selected_brand]['description'].tolist())}.
        Use the following criteria:
        - Supplier Complexity Fit
        - Key Components & Skills
        - Country Location & Logistics
        - Operating & Labor Costs
        - Transport Costs & Time
        - Tariffs & Trade Agreements with USA
        - Time to Move & Investments
        Provide a detailed analysis for each criterion.
        """
        # Add logic to process the prompt with OpenAI here
        return "Relocation analysis generated."

    return "Please select a brand to view relocation recommendations."
