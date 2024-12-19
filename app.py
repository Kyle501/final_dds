import dash
from dash import dcc, html, Input, Output
import sqlite3
import pandas as pd
import plotly.express as px

app = dash.Dash(__name__)
# Initialize Dash app
server = app.server

app.title = "Manager Dashboard"
db_path = "final_dds.db"

# Mapping of full state names to abbreviations
state_abbreviation_map = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

def fetch_data_from_sqlite(db_file):
    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Query to fetch data from orders and products tables
    query_orders = '''
    SELECT order_id, timestamp, shipping_state, payment_method, customer_id, product_id, seller_id
    FROM orders
    '''
    
    query_products = '''
    SELECT product_id, product_category, product_price, product_stock
    FROM products
    '''
    
    orders_df = pd.read_sql(query_orders, conn)
    products_df = pd.read_sql(query_products, conn)
    
    conn.close()
    
    return orders_df, products_df


# Helper function to query the database
def query_database(query):
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(query, conn)

# Load initial data
query = """
SELECT o.shipping_state AS state, 
       strftime('%Y', o.timestamp) || 'Q' || 
       CASE 
           WHEN CAST(strftime('%m', o.timestamp) AS INTEGER) BETWEEN 1 AND 3 THEN '1'
           WHEN CAST(strftime('%m', o.timestamp) AS INTEGER) BETWEEN 4 AND 6 THEN '2'
           WHEN CAST(strftime('%m', o.timestamp) AS INTEGER) BETWEEN 7 AND 9 THEN '3'
           ELSE '4'
       END AS quarter,
       strftime('%Y-%m', o.timestamp) AS month,
       p.product_category AS product, 
       SUM(p.product_price) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY state, quarter, month, product
"""
data = query_database(query)

# Map full state names to abbreviations
if data["state"].dtype == "object":
    data["state"] = data["state"].map(state_abbreviation_map)

orders_df, products_df = fetch_data_from_sqlite(db_path)

# Process orders_df as needed
orders_df['timestamp'] = pd.to_datetime(orders_df['timestamp'])
orders_df['year'] = orders_df['timestamp'].dt.year
orders_df['product_id'] = orders_df['product_id'].astype(int)

products_df['product_id'] = products_df['product_id'].astype(int)
products_df['product_category'] = products_df['product_category'].str.strip("'")
products_df['product_price'] = products_df['product_price'].astype(float)

orders_df = orders_df.merge(products_df[['product_id', 'product_category', 'product_price']], 
                             on='product_id', how='left')
orders_df['revenue'] = orders_df['product_price']

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body { 
                background-color: #f0f2f5; 
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            }
            .metric-card {
                background: white;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }
            .metric-card:hover {
                transform: translateY(-5px);
            }
            .metric-value {
                font-size: 28px;
                font-weight: 700;
                color: #1a237e;
            }
            .metric-label {
                color: #64748b;
                font-size: 14px;
                margin-bottom: 8px;
            }
            .chart-container {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            .chat-container {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                height: 400px;
                display: flex;
                flex-direction: column;
            }
            .chat-messages {
                flex-grow: 1;
                overflow-y: auto;
                margin-bottom: 10px;
                padding: 10px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            .chat-input {
                display: flex;
                gap: 10px;
            }
            .message {
                margin: 5px 0;
                padding: 8px;
                border-radius: 8px;
            }
            .user-message {
                background: #e2e8f0;
                margin-left: 20%;
            }
            .bot-message {
                background: #4F46E5;
                color: white;
                margin-right: 20%;
            }
            /* Tooltip container */
            .tooltip-container {
                position: relative;
                display: inline-block;
                z-index: 999;
            }           
            /* Tooltip text */
            .tooltip-text {
                visibility: hidden;
                width: 250px;
                background-color: #f9f9f9;
                color: #000;
                text-align: center;
                border-radius: 5px;
                padding: 10px;
                border: 1px solid #ccc;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                position: absolute;
                z-index: 999;  /* Ensure it's above other content */
                top: 100%;  /* Position it below the parent element */
                left: 50%;
                transform: translateX(-50%);  /* Center the tooltip horizontally */
                margin-top: 10px;  /* Add space between the element and the tooltip */
            }

            /* Show tooltip text on hover */
            .tooltip-container:hover .tooltip-text {
                visibility: visible;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    dcc.Store(id="selected-products", data=[]),  # Store for selected products

     # Header Section
    html.Div([
    html.H1("Amazon's Inventory Management and Expansion for 2019",
            style={'fontSize': '32px', 'fontWeight': '700', 'color': '#1a237e', 'margin': '0', 'textAlign': 'center'}),
    # html.P(f"Last updated: {datetime.now().strftime('%B %d, %Y')}",
    #        style={'color': '#64748b'})
    ], style={'padding': '24px', 'backgroundColor': 'white', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),

    html.Div([  # Metrics
        html.Div([
            html.Div([  # Total Revenue
                html.Div("Total Revenue", className='metric-label'),
                html.Div(f"${orders_df['revenue'].sum():,.0f}", className='metric-value'),
                html.Div("+12.3% vs prev year", className='trend-indicator-positive'),
                html.P("Understanding the total revenue gives an immediate overview of the business's financial health, helping "
                       "decision-makers track performance over time and assess growth. Comparing with the previous year’s performance can "
                       "help identify areas for improvement.",
                       className="tooltip-text",
                       ),
            ], className='metric-card tooltip-container'),

            html.Div([  # Average Order Value
                html.Div("Average Order Value", className='metric-label'),
                html.Div(f"${orders_df['revenue'].mean():,.2f}", className='metric-value'),
                html.Div("-2.1% vs prev year", className='trend-indicator-negative'),
                 html.P("The Average Order Value (AOV) provides insight into the average spending behavior of customers. If this metric "
                       "is low, it could indicate opportunities for upselling or adjusting pricing strategies.", className="tooltip-text"),
            ], className='metric-card tooltip-container'),

            html.Div([  # Total Orders
                html.Div("Total Orders", className='metric-label'),
                html.Div(f"{len(orders_df):,}", className='metric-value'),
                html.Div("+8.7% vs prev year", className='trend-indicator-positive'),
                html.P("Tracking the total number of orders allows businesses to measure customer activity. Analyzing this in conjunction "
                      "with total revenue helps uncover potential issues such as declining order volumes or opportunities for growth.", className="tooltip-text"),
            ], className='metric-card tooltip-container')
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr', 'gap': '24px', 'margin': '24px'})
    ]),

    # Filter Section
        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "marginBottom": "20px",
                "backgroundColor": "#ecf0f1",
                "padding": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.1)",
            },
            children=[
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.Label("Filter by State:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="state-filter",
                            options=[{"label": state, "value": state} for state in data["state"].dropna().unique()],
                            multi=True,
                            placeholder="Select states...",
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.Label("Filter by Quarter:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="quarter-filter",
                            options=[{"label": quarter, "value": quarter} for quarter in data["quarter"].unique()],
                            multi=True,
                            placeholder="Select quarters...",
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.Label("Filter by Product:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="product-filter",
                            options=[{"label": product, "value": product} for product in data["product"].unique()],
                            multi=True,
                            placeholder="Select products...",
                        ),
                    ],
                ),
            ],
        ),

   # Graphs Section
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gridTemplateRows": "1fr 1fr",
                "gap": "20px",
            },
            children=[
                dcc.Graph(id="us-heatmap", style={"gridColumn": "1", "gridRow": "1"}),
                dcc.Graph(id="product-bar-chart", style={"gridColumn": "2", "gridRow": "1"}),
                dcc.Graph(id="product-pie-chart", style={"gridColumn": "1", "gridRow": "2"}),
                dcc.Graph(id="product-line-chart", style={"gridColumn": "2", "gridRow": "2"}),
            ],
        ),

])

# Callbacks for interactivity
@app.callback(
    [Output("us-heatmap", "figure"),
     Output("product-pie-chart", "figure"),
     Output("product-line-chart", "figure"),
     Output("product-bar-chart", "figure")],
    [Input("state-filter", "value"),
     Input("quarter-filter", "value"),
     Input("product-filter", "value")]
)
def update_charts(selected_states, selected_quarters, selected_products):
    # Apply filters
    filtered_data = data.copy()
    if selected_states:
        filtered_data = filtered_data[filtered_data["state"].isin(selected_states)]
    if selected_quarters:
        filtered_data = filtered_data[filtered_data["quarter"].isin(selected_quarters)]
    if selected_products:
        filtered_data = filtered_data[filtered_data["product"].isin(selected_products)]

    # US Heatmap
    heatmap_data = filtered_data.groupby("state")["revenue"].sum().reset_index()
    heatmap_fig = px.choropleth(
        heatmap_data,
        locations="state",
        locationmode="USA-states",
        color="revenue",
        scope="usa",
        title="Revenue by State",
    )

    # Product Pie Chart
    pie_data = filtered_data.groupby("product")["revenue"].sum().reset_index()
    pie_fig = px.pie(
        pie_data,
        names="product",
        values="revenue",
        title="Revenue by Product Category",
        color="product",
    )

    # Product Line Chart
    line_data = filtered_data.groupby(["month", "product"])["revenue"].sum().reset_index()
    line_fig = px.line(
        line_data,
        x="month",
        y="revenue",
        color="product",
        title="Product Revenue Over Time"
    )

    # Product Bar Chart (affected only by state and quarter filters)
    bar_filtered_data = data.copy()
    if selected_states:
        bar_filtered_data = bar_filtered_data[bar_filtered_data["state"].isin(selected_states)]
    if selected_quarters:
        bar_filtered_data = bar_filtered_data[bar_filtered_data["quarter"].isin(selected_quarters)]

    bar_data = bar_filtered_data.groupby("product")["revenue"].sum().reset_index()
    bar_fig = px.bar(
        bar_data,
        x="product",
        y="revenue",
        title="Revenue by Product Category (Bar Chart)",
        labels={"revenue": "Revenue", "product": "Product Category"},
        color="product",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )

    return heatmap_fig, pie_fig, line_fig, bar_fig

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
