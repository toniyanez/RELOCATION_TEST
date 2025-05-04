import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
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
app = Dash(__name__)

# Layout of the dashboard
app.layout = html.Div([
    html.H1("DASHBOARD", style={'text-align': 'center'}),

    # Tabs for navigation
    dcc.Tabs([
        dcc.Tab(label='MAIN', children=[
            html.Div([
                # Left Panel: Business Unit Filter and Revenue by Brand Chart
                html.Div([
                    html.H3("Filter by Business Unit"),
                    dcc.Dropdown(
                        id='business-unit-dropdown',
                        options=[{'label': bu, 'value': bu} for bu in brand_data['business_unit'].unique()],
                        placeholder="Select a Business Unit",
                        style={'margin-bottom': '20px'}
                    ),
                    html.H3("Revenue by Brand"),
                    dcc.Graph(id='brand-bar-chart'),
                ], style={
                    'width': '20%',
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'padding': '10px',
                    'border-right': '1px solid #ccc'
                }),

                # Center Panel: Product Table
                html.Div([
                    html.H3("Product Table"),
                    dash_table.DataTable(
                        id='product-table',
                        columns=[
                            {"name": "Product", "id": "product"},
                            {"name": "Tariff", "id": "tariff"},
                            {"name": "Country", "id": "country"},
                            {"name": "Comments", "id": "comments"}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        filter_action="native",
                        sort_action="native",
                        page_size=10
                    )
                ], style={
                    'width': '50%',
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'padding': '10px',
                    'text-align': 'center'
                }),

                # Right Panel: Brand Details Table
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
                dash_table.DataTable(
                    id='competitors-overview-table',
                    columns=[
                        {"name": "Competitor Name", "id": "competitor_name"},
                        {"name": "Revenue (USD)", "id": "revenue_usd"},
                        {"name": "Country", "id": "competitor_supplier_country"}
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    filter_action="native",
                    sort_action="native",
                    page_size=10
                )
            ], style={'width': '100%', 'display': 'inline-block'})
        ]),

        dcc.Tab(label='Relocation Simulation', children=[
            html.Div([
                html.H3("Radar Chart for Country Proposal"),
                dcc.Graph(id='radar-chart')
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

# Callback to update the product table based on selected brand
@app.callback(
    Output('product-table', 'data'),
    Input('brand-bar-chart', 'clickData')
)
def update_product_table(click_data):
    # Fixed product categories for simplicity
    product_categories = ["Helmets", "Binoculars", "Precision Optics", "Electronic Devices"]

    # Prompt OpenAI to get tariffs for these categories
    prompt = f"""
    You are an expert on trade tariffs. List the tariffs for each of these product categories:
    {', '.join(product_categories)}.
    Provide the response in the format: "Product Category, Tariff Applied".
    """
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
    product_data = []
    for result in results:
        parts = result.split(",")  # Split by comma
        if len(parts) == 2:
            product_data.append({
                "product": parts[0].strip(),
                "tariff": parts[1].strip(),
                "country": "N/A",  # Placeholder for simplicity
                "comments": "N/A"  # Placeholder for simplicity
            })

    # Log the parsed data for debugging
    print("Parsed Product Data:", product_data)

    return product_data

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

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
