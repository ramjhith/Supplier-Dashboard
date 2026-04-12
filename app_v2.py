import dash
from dash import dcc, html, Input, Output, callback, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3

from database import init_database, populate_sample_data, get_db_connection
from kpi_calculator import KPICalculator
from ml_models import SupplierMLModels

# Initialize database and models
init_database()
populate_sample_data()

# Initialize KPI calculator and ML models
ml_models = SupplierMLModels()
ml_models.train_all_models()

def get_suppliers_from_db():
    """Load supplier dropdown options using a short-lived connection."""
    conn = get_db_connection()
    try:
        suppliers_df = pd.read_sql_query('SELECT supplier_id, name FROM Suppliers ORDER BY name', conn)
        return [{'label': row['name'], 'value': row['supplier_id']} for _, row in suppliers_df.iterrows()]
    finally:
        conn.close()

supplier_options = get_suppliers_from_db()

# KPI Choices
kpi_choices = [
    {'label': '📊 On-Time Delivery Rate', 'value': 'otd'},
    {'label': '⚠️ Defect Rate', 'value': 'defect'},
    {'label': '📅 Lead Time Trend', 'value': 'lead_time'},
    {'label': '💰 Cost Variance', 'value': 'cost'},
    {'label': '🎯 Risk Score', 'value': 'risk'},
    {'label': '📋 Rejection Reasons', 'value': 'rejection'},
]

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🚀 Supplier Relationship Management Dashboard", style={'textAlign': 'center', 'margin': '0'}),
        html.P("Problem Statement P6 - Real-time Supplier Performance & ML Predictions", 
               style={'textAlign': 'center', 'color': '#666', 'marginTop': '5px', 'marginBottom': '0'})
    ], style={'backgroundColor': '#1f77b4', 'color': 'white', 'padding': '30px', 'marginBottom': '20px', 'borderRadius': '8px'}),
    
    html.Div([
        # LEFT PANEL - Filters & Settings
        html.Div([
            html.H3("📋 Filters & Settings", style={'borderBottom': '2px solid #1f77b4', 'paddingBottom': '10px'}),
            
            html.Label("Select Supplier:", style={'fontWeight': 'bold', 'marginTop': '15px', 'display': 'block'}),
            dcc.Dropdown(
                id='supplier-dropdown',
                options=[{'label': 'All Suppliers', 'value': 'all'}] + supplier_options,
                value='all',
                style={'width': '100%'}
            ),
            
            html.Label("Date Range:", style={'fontWeight': 'bold', 'marginTop': '15px', 'display': 'block'}),
            dcc.DatePickerRange(
                id='date-range',
                start_date=datetime.now() - timedelta(days=180),
                end_date=datetime.now(),
                display_format='YYYY-MM-DD',
                style={'width': '100%'}
            ),
            
            html.Label("Filter by Status:", style={'fontWeight': 'bold', 'marginTop': '15px', 'display': 'block'}),
            dcc.Dropdown(
                id='status-dropdown',
                options=[
                    {'label': 'All', 'value': 'all'},
                    {'label': 'Delivered', 'value': 'Delivered'},
                    {'label': 'Pending', 'value': 'Pending'},
                ],
                value='all',
                style={'width': '100%'}
            ),
            
            html.Label("Select KPIs to Display:", style={'fontWeight': 'bold', 'marginTop': '20px', 'display': 'block'}),
            dcc.Checklist(
                id='kpi-checklist',
                options=kpi_choices,
                value=['otd', 'defect', 'lead_time'],  # Default selections
                style={'marginTop': '10px'},
                labelStyle={'display': 'block', 'marginBottom': '8px'}
            ),
            
            html.Button(
                "🔄 Refresh Data",
                id='refresh-button',
                n_clicks=0,
                style={
                    'width': '100%',
                    'marginTop': '20px',
                    'padding': '10px',
                    'backgroundColor': '#1f77b4',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                    'fontSize': '14px'
                }
            ),
            
        ], style={
            'width': '22%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '20px',
            'backgroundColor': '#f8f9fa',
            'marginRight': '2%',
            'borderRadius': '8px',
            'height': '100%',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }),
        
        # RIGHT PANEL - Content
        html.Div([
            # KPI Summary Cards
            html.Div(id='kpi-cards', style={'marginBottom': '30px'}),
            
            # Charts Container
            html.Div(id='charts-container', style={'marginTop': '20px'})
            
        ], style={
            'width': '76%',
            'display': 'inline-block',
            'verticalAlign': 'top',
        }),
    ], style={'padding': '20px'}),
    
    # Bottom Section - Open POs Table
    html.Div([
        html.H3("📋 Open Purchase Orders", style={'marginBottom': '15px', 'borderBottom': '2px solid #1f77b4', 'paddingBottom': '10px'}),
        html.Div(id='open-pos-table', style={'overflowX': 'auto'})
    ], style={'padding': '20px', 'backgroundColor': '#ffffff', 'marginTop': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # ML Predictions Section
    html.Div([
        html.H3("🤖 ML Predictions for Selected Supplier", style={'marginBottom': '15px', 'borderBottom': '2px solid #1f77b4', 'paddingBottom': '10px'}),
        html.Div(id='ml-predictions', style={'minHeight': '150px'})
    ], style={'padding': '20px', 'backgroundColor': '#ffffff', 'marginTop': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})

# ============= CALLBACKS =============

@app.callback(
    [Output('kpi-cards', 'children'),
     Output('charts-container', 'children'),
     Output('open-pos-table', 'children'),
     Output('ml-predictions', 'children')],
    [Input('supplier-dropdown', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('status-dropdown', 'value'),
     Input('kpi-checklist', 'value'),
     Input('refresh-button', 'n_clicks')],
)
def update_dashboard(selected_supplier, start_date, end_date, status_filter, selected_kpis, n_clicks):
    conn = None
    kpi_calc_local = None
    try:
        conn = get_db_connection()
        kpi_calc_local = KPICalculator()

        # Get KPIs
        if selected_supplier == 'all':
            all_kpis_df = kpi_calc_local.get_all_suppliers_kpis()
            otd_avg = all_kpis_df['On-Time Delivery Rate (%)'].mean()
            defect_avg = all_kpis_df['Defect Rate (%)'].mean()
            lead_time_avg = all_kpis_df['Avg Lead Time (days)'].mean()
            risk_score_avg = all_kpis_df['Supplier Risk Score (0-100)'].mean()
        else:
            kpis = kpi_calc_local.get_all_kpis_for_supplier(selected_supplier)
            otd_avg = kpis['On-Time Delivery Rate (%)']
            defect_avg = kpis['Defect Rate (%)']
            lead_time_avg = kpis['Avg Lead Time (days)']
            risk_score_avg = kpis['Supplier Risk Score (0-100)']
        
        # KPI Cards
        kpi_cards = html.Div([
            html.Div([
                html.H4("On-Time Delivery", style={'margin': '0', 'fontSize': '12px'}),
                html.H2(f"{otd_avg:.1f}%", style={'margin': '10px 0', 'color': '#28a745' if otd_avg > 80 else '#ffc107' if otd_avg > 60 else '#dc3545'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff', 'marginRight': '2%', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("Defect Rate", style={'margin': '0', 'fontSize': '12px'}),
                html.H2(f"{defect_avg:.1f}%", style={'margin': '10px 0', 'color': '#28a745' if defect_avg < 2 else '#ffc107' if defect_avg < 4 else '#dc3545'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff', 'marginRight': '2%', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("Avg Lead Time", style={'margin': '0', 'fontSize': '12px'}),
                html.H2(f"{lead_time_avg:.0f}d", style={'margin': '10px 0', 'color': '#007bff'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff', 'marginRight': '2%', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("Risk Score", style={'margin': '0', 'fontSize': '12px'}),
                html.H2(f"{risk_score_avg:.0f}/100", style={'margin': '10px 0', 'color': '#6f42c1' if risk_score_avg < 50 else '#ffc107' if risk_score_avg < 75 else '#dc3545'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        ], style={'marginBottom': '20px'})
        
        # Build where clause
        where_clause = "WHERE 1=1"
        params = []
        
        if selected_supplier != 'all':
            where_clause += " AND po.supplier_id = ?"
            params.append(selected_supplier)
        
        if status_filter != 'all':
            where_clause += " AND po.status = ?"
            params.append(status_filter)
        
        where_clause += " AND po.order_date >= ? AND po.order_date <= ?"
        params.extend([start_date, end_date])
        
        # Build Charts
        chart_divs = []
        
        # Chart 1: OTD
        if 'otd' in selected_kpis:
            otd_query = f'''
                SELECT s.name, 
                       SUM(CASE WHEN ship.delay_flag = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as otd
                FROM PurchaseOrders po
                JOIN Suppliers s ON po.supplier_id = s.supplier_id
                LEFT JOIN Shipments ship ON po.po_id = ship.po_id
                {where_clause} AND po.status = 'Delivered'
                GROUP BY s.name
                ORDER BY otd DESC
            '''
            otd_data = pd.read_sql_query(otd_query, conn, params=params)
            
            if len(otd_data) > 0:
                fig_otd = go.Figure(data=go.Bar(
                    x=otd_data['name'],
                    y=otd_data['otd'],
                    marker_color=['#28a745' if x > 80 else '#ffc107' if x > 60 else '#dc3545' for x in otd_data['otd']],
                    text=[f"{x:.1f}%" for x in otd_data['otd']],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>OTD: %{y:.1f}%<extra></extra>'
                ))
                fig_otd.update_layout(
                    title="On-Time Delivery Rate by Supplier",
                    yaxis_title="OTD %",
                    hovermode='x',
                    height=400,
                    margin=dict(l=50, r=50, t=50, b=50),
                    template='plotly_white'
                )
                chart_divs.append(dcc.Graph(figure=fig_otd, style={'display': 'inline-block', 'width': '48%', 'marginRight': '2%'}))
        
        # Chart 2: Defect Rate
        if 'defect' in selected_kpis:
            defect_query = f'''
                SELECT s.name, AVG(qr.defect_rate) as defect_rate
                FROM PurchaseOrders po
                JOIN Suppliers s ON po.supplier_id = s.supplier_id
                LEFT JOIN QualityRecords qr ON po.supplier_id = qr.supplier_id
                {where_clause}
                GROUP BY s.name
                ORDER BY defect_rate DESC
            '''
            defect_data = pd.read_sql_query(defect_query, conn, params=params)
            
            if len(defect_data) > 0:
                fig_defect = go.Figure(data=go.Bar(
                    x=defect_data['name'],
                    y=defect_data['defect_rate'],
                    marker_color=['#28a745' if x < 2 else '#ffc107' if x < 4 else '#dc3545' for x in defect_data['defect_rate']],
                    text=[f"{x:.2f}%" for x in defect_data['defect_rate']],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Defect Rate: %{y:.2f}%<extra></extra>'
                ))
                fig_defect.update_layout(
                    title="Defect Rate by Supplier",
                    yaxis_title="Defect %",
                    hovermode='x',
                    height=400,
                    margin=dict(l=50, r=50, t=50, b=50),
                    template='plotly_white'
                )
                chart_divs.append(dcc.Graph(figure=fig_defect, style={'display': 'inline-block', 'width': '48%'}))
        
        # Chart 3: Lead Time Trend
        if 'lead_time' in selected_kpis:
            lt_query = f'''
                SELECT DATE(po.order_date) as date, 
                       AVG(julianday(po.actual_delivery_date) - julianday(po.order_date)) as avg_lt
                FROM PurchaseOrders po
                {where_clause} AND po.status = 'Delivered'
                GROUP BY DATE(po.order_date)
                ORDER BY date
            '''
            lt_data = pd.read_sql_query(lt_query, conn, params=params)
            
            if len(lt_data) > 0:
                fig_lt = go.Figure(data=go.Scatter(
                    x=lt_data['date'],
                    y=lt_data['avg_lt'],
                    mode='lines+markers',
                    fill='tozeroy',
                    name='Lead Time',
                    line=dict(color='#007bff', width=3),
                    hovertemplate='<b>%{x}</b><br>Lead Time: %{y:.1f} days<extra></extra>'
                ))
                fig_lt.update_layout(
                    title="Lead Time Trend",
                    yaxis_title="Days",
                    hovermode='x',
                    height=400,
                    margin=dict(l=50, r=50, t=50, b=50),
                    template='plotly_white'
                )
                chart_divs.append(dcc.Graph(figure=fig_lt, style={'display': 'inline-block', 'width': '48%', 'marginRight': '2%'}))
        
        # Chart 4: Cost Variance
        if 'cost' in selected_kpis:
            cost_query = f'''
                SELECT s.name, AVG(((po.actual_cost - po.quoted_cost) / po.quoted_cost) * 100) as cost_var
                FROM PurchaseOrders po
                JOIN Suppliers s ON po.supplier_id = s.supplier_id
                {where_clause} AND po.quoted_cost > 0
                GROUP BY s.name
                ORDER BY ABS(cost_var) DESC
            '''
            cost_data = pd.read_sql_query(cost_query, conn, params=params)
            
            if len(cost_data) > 0:
                fig_cost = go.Figure(data=go.Bar(
                    x=cost_data['name'],
                    y=cost_data['cost_var'],
                    marker_color=['#dc3545' if x > 10 else '#ffc107' if x > 5 else '#28a745' for x in cost_data['cost_var']],
                    text=[f"{x:.1f}%" for x in cost_data['cost_var']],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Cost Variance: %{y:.1f}%<extra></extra>'
                ))
                fig_cost.update_layout(
                    title="Cost Variance by Supplier",
                    yaxis_title="Variance %",
                    hovermode='x',
                    height=400,
                    margin=dict(l=50, r=50, t=50, b=50),
                    template='plotly_white'
                )
                chart_divs.append(dcc.Graph(figure=fig_cost, style={'display': 'inline-block', 'width': '48%'}))
        
        # Chart 5: Risk Score
        if 'risk' in selected_kpis:
            if selected_supplier == 'all':
                risk_data = all_kpis_df[['Supplier', 'Supplier Risk Score (0-100)']].sort_values('Supplier Risk Score (0-100)', ascending=False)
            else:
                supplier_name = pd.read_sql_query('SELECT name FROM Suppliers WHERE supplier_id = ?', conn, params=[selected_supplier])
                risk_score = kpi_calc_local.supplier_risk_score(selected_supplier)
                risk_data = pd.DataFrame({'Supplier': [supplier_name['name'].values[0]], 'Supplier Risk Score (0-100)': [risk_score]})
            
            if len(risk_data) > 0:
                fig_risk = go.Figure(data=go.Bar(
                    x=risk_data['Supplier'],
                    y=risk_data['Supplier Risk Score (0-100)'],
                    marker_color=['#28a745' if x < 50 else '#ffc107' if x < 75 else '#dc3545' for x in risk_data['Supplier Risk Score (0-100)']],
                    text=[f"{x:.0f}" for x in risk_data['Supplier Risk Score (0-100)']],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Risk Score: %{y:.0f}/100<extra></extra>'
                ))
                fig_risk.update_layout(
                    title="Supplier Risk Score (0=Low, 100=High)",
                    yaxis_title="Risk Score",
                    hovermode='x',
                    height=400,
                    margin=dict(l=50, r=50, t=50, b=50),
                    template='plotly_white'
                )
                chart_divs.append(dcc.Graph(figure=fig_risk, style={'display': 'inline-block', 'width': '48%', 'marginRight': '2%'}))
        
        # Chart 6: Rejection Reasons
        if 'rejection' in selected_kpis:
            reject_query = f'''
                SELECT qr.rejection_reason, COUNT(*) as count
                FROM QualityRecords qr
                JOIN PurchaseOrders po ON qr.po_id = po.po_id
                {where_clause} AND qr.rejection_reason IS NOT NULL
                GROUP BY qr.rejection_reason
            '''
            reject_data = pd.read_sql_query(reject_query, conn, params=params)
            
            if len(reject_data) > 0:
                fig_reject = go.Figure(data=go.Pie(
                    labels=reject_data['rejection_reason'],
                    values=reject_data['count'],
                    hole=0.3,
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
                ))
                fig_reject.update_layout(
                    title="Rejection Reasons Distribution",
                    height=400,
                    margin=dict(l=50, r=50, t=50, b=50)
                )
                chart_divs.append(dcc.Graph(figure=fig_reject, style={'display': 'inline-block', 'width': '48%'}))
        
        charts_container = html.Div(chart_divs, style={'marginTop': '20px'})
        
        # Open POs Table
        open_pos_query = f'''
            SELECT s.name, po.po_id, po.order_date, po.expected_delivery_date, 
                   po.order_quantity, po.status
            FROM PurchaseOrders po
            JOIN Suppliers s ON po.supplier_id = s.supplier_id
            {where_clause}
            ORDER BY po.expected_delivery_date ASC
            LIMIT 20
        '''
        open_pos_data = pd.read_sql_query(open_pos_query, conn, params=params)
        
        if len(open_pos_data) > 0:
            table = html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Supplier", style={'padding': '10px', 'textAlign': 'left', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6'}),
                        html.Th("PO ID", style={'padding': '10px', 'textAlign': 'left', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6'}),
                        html.Th("Order Date", style={'padding': '10px', 'textAlign': 'left', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6'}),
                        html.Th("Expected Delivery", style={'padding': '10px', 'textAlign': 'left', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6'}),
                        html.Th("Quantity", style={'padding': '10px', 'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6'}),
                        html.Th("Status", style={'padding': '10px', 'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6'}),
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(row['name'], style={'padding': '10px', 'borderBottom': '1px solid #ddd'}),
                        html.Td(f"PO-{row['po_id']}", style={'padding': '10px', 'borderBottom': '1px solid #ddd', 'fontWeight': 'bold'}),
                        html.Td(row['order_date'], style={'padding': '10px', 'borderBottom': '1px solid #ddd'}),
                        html.Td(row['expected_delivery_date'], style={'padding': '10px', 'borderBottom': '1px solid #ddd'}),
                        html.Td(row['order_quantity'], style={'padding': '10px', 'textAlign': 'center', 'borderBottom': '1px solid #ddd'}),
                        html.Td(
                            row['status'],
                            style={
                                'padding': '10px',
                                'textAlign': 'center',
                                'borderBottom': '1px solid #ddd',
                                'color': '#28a745' if row['status'] == 'Delivered' else '#ffc107',
                                'fontWeight': 'bold'
                            }
                        ),
                    ])
                    for _, row in open_pos_data.iterrows()
                ])
            ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '13px'})
        else:
            table = html.Div("No purchase orders found for selected filters", style={'textAlign': 'center', 'padding': '20px', 'color': '#999'})
        
        # ML Predictions
        ml_content = html.Div()
        if selected_supplier != 'all':
            supplier_name = pd.read_sql_query('SELECT name, location FROM Suppliers WHERE supplier_id = ?', conn, params=[selected_supplier])
            name = supplier_name['name'].values[0]
            location = supplier_name['location'].values[0]
            
            recent_po_query = '''
                SELECT order_quantity, 
                       julianday(expected_delivery_date) - julianday(order_date) as expected_lt,
                       strftime('%m', order_date) as month,
                       product_category
                FROM PurchaseOrders
                WHERE supplier_id = ?
                ORDER BY order_date DESC
                LIMIT 1
            '''
            recent_po = pd.read_sql_query(recent_po_query, conn, params=[selected_supplier])
            
            if len(recent_po) > 0:
                qty = recent_po['order_quantity'].values[0]
                exp_lt = recent_po['expected_lt'].values[0]
                month = int(recent_po['month'].values[0])
                category = recent_po['product_category'].values[0]
                
                delay_prob = ml_models.predict_delay_probability(selected_supplier, qty, exp_lt, month) or 0
                defect_prob = ml_models.predict_defect_risk_probability(selected_supplier, qty, category, 30) or 0
                lt_cat = ml_models.predict_lead_time_category(selected_supplier, 'Medium', month, location) or 'Unknown'
                
                ml_content = html.Div([
                    html.H4(f"Predictions for {name}", style={'marginBottom': '15px'}),
                    html.Div([
                        html.Div([
                            html.H5("⚠️ Delay Risk"),
                            html.H3(f"{delay_prob}%", style={'color': '#dc3545' if delay_prob > 60 else '#ffc107' if delay_prob > 40 else '#28a745'}),
                            html.P("Probability of order delay", style={'fontSize': '12px', 'color': '#666'})
                        ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px', 'backgroundColor': '#fff', 'marginRight': '2%', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'}),
                        
                        html.Div([
                            html.H5("⚠️ Quality Risk"),
                            html.H3(f"{defect_prob}%", style={'color': '#dc3545' if defect_prob > 50 else '#ffc107' if defect_prob > 30 else '#28a745'}),
                            html.P("Probability of high defect rate", style={'fontSize': '12px', 'color': '#666'})
                        ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px', 'backgroundColor': '#fff', 'marginRight': '2%', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'}),
                        
                        html.Div([
                            html.H5("📅 Lead Time"),
                            html.H3(lt_cat, style={'color': '#28a745' if lt_cat == 'On-time' else '#ffc107' if lt_cat == 'Early' else '#dc3545'}),
                            html.P("Expected delivery category", style={'fontSize': '12px', 'color': '#666'})
                        ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'}),
                    ])
                ])
        else:
            ml_content = html.Div(
                "Select a specific supplier to view AI/ML predictions",
                style={'textAlign': 'center', 'padding': '30px', 'color': '#999', 'fontSize': '14px'}
            )
        
        return kpi_cards, charts_container, table, ml_content
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"Error: {str(e)}"), html.Div(), html.Div(), html.Div()
    finally:
        if conn is not None:
            conn.close()
        if kpi_calc_local is not None:
            kpi_calc_local.close()

# ============= RUN APP =============

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Supplier Relationship Management Dashboard v2.0")
    print("="*60)
    print("\n📊 Dashboard ready!")
    print("🌐 Open your browser and go to: http://127.0.0.1:8050/")
    print("\n" + "="*60 + "\n")
    app.run_server(debug=False, port=8050)
