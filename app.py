import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3

from database import init_database, populate_sample_data, get_db_connection
from kpi_calculator import KPICalculator
from ml_models import SupplierMLModels

# Initialize database and models (once at startup)
print("Initializing database...")
init_database()
populate_sample_data()

print("Training ML models...")
kpi_calc = KPICalculator()
ml_models = SupplierMLModels()
ml_models.train_all_models()
kpi_calc.close()
ml_models.close()

# Thread-safe function to get suppliers
def get_suppliers_from_db():
    """Get suppliers from database in thread-safe manner"""
    conn = get_db_connection()
    suppliers_df = pd.read_sql_query('SELECT supplier_id, name FROM Suppliers ORDER BY name', conn)
    conn.close()
    return [{'label': row['name'], 'value': row['supplier_id']} for _, row in suppliers_df.iterrows()]

# KPI Choices
kpi_choices = [
    {'label': 'On-Time Delivery Rate', 'value': 'otd'},
    {'label': 'Defect Rate', 'value': 'defect'},
    {'label': 'Lead Time Trend', 'value': 'lead_time'},
    {'label': 'Cost Variance', 'value': 'cost'},
    {'label': 'Risk Score', 'value': 'risk'},
    {'label': 'Rejection Reasons', 'value': 'rejection'},
]

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Get supplier options for initial load
initial_suppliers = get_suppliers_from_db()

# Professional color scheme
PRIMARY_COLOR = '#2c3e50'
SECONDARY_COLOR = '#3498db'
ACCENT_COLOR = '#e74c3c'
SUCCESS_COLOR = '#27ae60'
WARNING_COLOR = '#f39c12'
BG_COLOR = '#ecf0f1'
CARD_BG = '#ffffff'

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Supplier Relationship Management", style={
            'textAlign': 'center', 
            'margin': '0', 
            'fontSize': '36px', 
            'fontWeight': '700', 
            'letterSpacing': '0.3px',
            'color': 'white'
        }),
        html.P("Real-time Performance Analytics & AI-Powered Insights", 
            style={
                'textAlign': 'center', 
                'color': 'rgba(255,255,255,0.85)', 
                'marginTop': '10px', 
                'marginBottom': '0', 
                'fontSize': '15px',
                'fontWeight': '300'
            })
    ], style={
        'backgroundColor': PRIMARY_COLOR, 
        'padding': '45px 30px', 
        'marginBottom': '35px', 
        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
        'borderBottom': f'4px solid {SECONDARY_COLOR}'
    }),
    
    html.Div([
        # LEFT PANEL - Filters & Settings
        html.Div([
            html.H3("Filters & Settings", style={
                'borderBottom': f'3px solid {SECONDARY_COLOR}', 
                'paddingBottom': '15px', 
                'marginTop': '0',
                'marginBottom': '20px',
                'fontSize': '18px', 
                'fontWeight': '700', 
                'color': PRIMARY_COLOR
            }),
            
            html.Label("Supplier", style={
                'fontWeight': '600', 
                'marginTop': '22px', 
                'display': 'block', 
                'fontSize': '12px', 
                'color': PRIMARY_COLOR, 
                'marginBottom': '8px',
                'textTransform': 'uppercase',
                'letterSpacing': '0.5px'
            }),
            dcc.Dropdown(
                id='supplier-dropdown',
                options=[{'label': 'All Suppliers', 'value': 'all'}] + initial_suppliers,
                value='all',
                style={'width': '100%'},
                clearable=False
            ),
            
            html.Label("Date Range", style={
                'fontWeight': '600', 
                'marginTop': '20px', 
                'display': 'block', 
                'fontSize': '12px', 
                'color': PRIMARY_COLOR, 
                'marginBottom': '8px',
                'textTransform': 'uppercase',
                'letterSpacing': '0.5px'
            }),
            dcc.DatePickerRange(
                id='date-range',
                start_date=datetime.now() - timedelta(days=180),
                end_date=datetime.now(),
                display_format='YYYY-MM-DD',
                style={'width': '100%'}
            ),
            
            html.Label("Status", style={
                'fontWeight': '600', 
                'marginTop': '20px', 
                'display': 'block', 
                'fontSize': '12px', 
                'color': PRIMARY_COLOR, 
                'marginBottom': '8px',
                'textTransform': 'uppercase',
                'letterSpacing': '0.5px'
            }),
            dcc.Dropdown(
                id='status-dropdown',
                options=[
                    {'label': 'All', 'value': 'all'},
                    {'label': 'Delivered', 'value': 'Delivered'},
                    {'label': 'Pending', 'value': 'Pending'},
                ],
                value='all',
                style={'width': '100%'},
                clearable=False
            ),
            
            html.Label("KPI Selection", style={
                'fontWeight': '600', 
                'marginTop': '22px', 
                'display': 'block', 
                'fontSize': '12px', 
                'color': PRIMARY_COLOR, 
                'marginBottom': '12px',
                'textTransform': 'uppercase',
                'letterSpacing': '0.5px'
            }),
            dcc.Checklist(
                id='kpi-checklist',
                options=kpi_choices,
                value=['otd', 'defect', 'lead_time'],
                style={'marginTop': '8px'},
                labelStyle={
                    'display': 'block', 
                    'marginBottom': '10px', 
                    'fontSize': '13px', 
                    'color': '#34495e', 
                    'fontWeight': '500'
                }
            ),
            
            html.Button(
                "Refresh Dashboard",
                id='refresh-button',
                n_clicks=0,
                style={
                    'width': '100%',
                    'marginTop': '28px',
                    'padding': '13px 16px',
                    'backgroundColor': SECONDARY_COLOR,
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '5px',
                    'cursor': 'pointer',
                    'fontWeight': '600',
                    'fontSize': '13px',
                    'transition': 'all 0.3s ease',
                    'boxShadow': '0 2px 4px rgba(52, 152, 219, 0.3)',
                    'textTransform': 'uppercase',
                    'letterSpacing': '0.5px'
                }
            ),
            
        ], style={
            'width': '22%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '28px',
            'backgroundColor': BG_COLOR,
            'marginRight': '2%',
            'borderRadius': '8px',
            'height': 'fit-content',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.06)'
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
    ], style={'padding': '20px 30px'}),
    
    # Bottom Section - Open POs Table
    html.Div([
        html.H3("Open Purchase Orders", style={
            'marginBottom': '20px', 
            'borderBottom': f'3px solid {SECONDARY_COLOR}', 
            'paddingBottom': '12px',
            'fontSize': '18px',
            'fontWeight': '700',
            'color': PRIMARY_COLOR
        }),
        html.Div(id='open-pos-table', style={'overflowX': 'auto'})
    ], style={
        'padding': '28px', 
        'backgroundColor': CARD_BG, 
        'marginTop': '30px', 
        'marginLeft': '30px',
        'marginRight': '30px',
        'borderRadius': '8px', 
        'boxShadow': '0 2px 8px rgba(0,0,0,0.06)'
    }),
    
    # ML Predictions Section
    html.Div([
        html.H3("AI/ML Predictions", style={
            'marginBottom': '20px', 
            'borderBottom': f'3px solid {SECONDARY_COLOR}', 
            'paddingBottom': '12px',
            'fontSize': '18px',
            'fontWeight': '700',
            'color': PRIMARY_COLOR
        }),
        html.Div(id='ml-predictions', style={'minHeight': '150px'})
    ], style={
        'padding': '28px', 
        'backgroundColor': CARD_BG, 
        'marginTop': '30px',
        'marginLeft': '30px', 
        'marginRight': '30px',
        'marginBottom': '30px',
        'borderRadius': '8px', 
        'boxShadow': '0 2px 8px rgba(0,0,0,0.06)'
    }),
    
], style={'padding': '0', 'fontFamily': "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif", 'backgroundColor': '#f8f9fa', 'minHeight': '100vh'})

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
    """Main callback - creates thread-safe database connections"""

    conn = None
    kpi_calc_local = None
    try:
        # Create fresh database connection for this callback (thread-safe)
        conn = get_db_connection()

        # Initialize a fresh KPI calculator for this callback.
        # Reuse the ML models trained at startup instead of retraining on every refresh.
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
        def get_card_color(value, thresholds):
            """Determine color based on value and thresholds"""
            for threshold, color in thresholds:
                if value >= threshold:
                    return color
            return thresholds[-1][1]
        
        otd_color = get_card_color(otd_avg, [(80, SUCCESS_COLOR), (60, WARNING_COLOR), (0, ACCENT_COLOR)])
        defect_color = get_card_color(100 - defect_avg, [(98, SUCCESS_COLOR), (96, WARNING_COLOR), (0, ACCENT_COLOR)])
        risk_color = get_card_color(100 - risk_score_avg, [(50, SUCCESS_COLOR), (25, WARNING_COLOR), (0, ACCENT_COLOR)])
        
        kpi_cards = html.Div([
            html.Div([
                html.H4("On-Time Delivery", style={'margin': '0', 'fontSize': '12px', 'color': '#7f8c8d', 'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                html.H2(f"{otd_avg:.1f}%", style={'margin': '12px 0 0 0', 'color': otd_color, 'fontWeight': '700'})
            ], style={
                'width': '23%', 
                'display': 'inline-block', 
                'textAlign': 'center', 
                'padding': '22px', 
                'backgroundColor': CARD_BG,
                'marginRight': '2%', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                'borderTop': f'4px solid {otd_color}',
                'transition': 'box-shadow 0.3s ease'
            }),
            
            html.Div([
                html.H4("Defect Rate", style={'margin': '0', 'fontSize': '12px', 'color': '#7f8c8d', 'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                html.H2(f"{defect_avg:.1f}%", style={'margin': '12px 0 0 0', 'color': defect_color, 'fontWeight': '700'})
            ], style={
                'width': '23%', 
                'display': 'inline-block', 
                'textAlign': 'center', 
                'padding': '22px', 
                'backgroundColor': CARD_BG,
                'marginRight': '2%', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                'borderTop': f'4px solid {defect_color}',
                'transition': 'box-shadow 0.3s ease'
            }),
            
            html.Div([
                html.H4("Average Lead Time", style={'margin': '0', 'fontSize': '12px', 'color': '#7f8c8d', 'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                html.H2(f"{lead_time_avg:.0f}d", style={'margin': '12px 0 0 0', 'color': SECONDARY_COLOR, 'fontWeight': '700'})
            ], style={
                'width': '23%', 
                'display': 'inline-block', 
                'textAlign': 'center', 
                'padding': '22px', 
                'backgroundColor': CARD_BG,
                'marginRight': '2%', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                'borderTop': f'4px solid {SECONDARY_COLOR}',
                'transition': 'box-shadow 0.3s ease'
            }),
            
            html.Div([
                html.H4("Risk Score", style={'margin': '0', 'fontSize': '12px', 'color': '#7f8c8d', 'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                html.H2(f"{risk_score_avg:.0f}/100", style={'margin': '12px 0 0 0', 'color': risk_color, 'fontWeight': '700'})
            ], style={
                'width': '23%', 
                'display': 'inline-block', 
                'textAlign': 'center', 
                'padding': '22px', 
                'backgroundColor': CARD_BG,
                'borderRadius': '8px', 
                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                'borderTop': f'4px solid {risk_color}',
                'transition': 'box-shadow 0.3s ease'
            }),
        ], style={'marginBottom': '25px'})
        
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
            try:
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
                    colors = ['#27ae60' if x > 80 else '#f39c12' if x > 60 else '#e74c3c' for x in otd_data['otd']]
                    fig_otd = go.Figure(data=go.Bar(
                        x=otd_data['name'],
                        y=otd_data['otd'],
                        marker_color=colors,
                        text=[f"{x:.1f}%" for x in otd_data['otd']],
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>On-Time Delivery: %{y:.1f}%<extra></extra>'
                    ))
                    fig_otd.update_layout(
                        title="On-Time Delivery Rate by Supplier",
                        yaxis_title="Percentage (%)",
                        hovermode='x',
                        height=420,
                        margin=dict(l=60, r=60, t=80, b=60),
                        template='plotly_white',
                        font=dict(family="Segoe UI, sans-serif", size=12),
                        title_font_size=16,
                        showlegend=False
                    )
                    chart_divs.append(dcc.Graph(figure=fig_otd, style={'display': 'inline-block', 'width': '48%', 'marginRight': '2%'}))
            except Exception as e:
                print(f"Error rendering OTD chart: {e}")
        
        # Chart 2: Defect Rate
        if 'defect' in selected_kpis:
            try:
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
                    colors = ['#27ae60' if x < 2 else '#f39c12' if x < 4 else '#e74c3c' for x in defect_data['defect_rate'].fillna(0)]
                    fig_defect = go.Figure(data=go.Bar(
                        x=defect_data['name'],
                        y=defect_data['defect_rate'].fillna(0),
                        marker_color=colors,
                        text=[f"{x:.2f}%" if pd.notna(x) else "N/A" for x in defect_data['defect_rate']],
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>Defect Rate: %{y:.2f}%<extra></extra>'
                    ))
                    fig_defect.update_layout(
                        title="Defect Rate by Supplier",
                        yaxis_title="Percentage (%)",
                        hovermode='x',
                        height=420,
                        margin=dict(l=60, r=60, t=80, b=60),
                        template='plotly_white',
                        font=dict(family="Segoe UI, sans-serif", size=12),
                        title_font_size=16,
                        showlegend=False
                    )
                    chart_divs.append(dcc.Graph(figure=fig_defect, style={'display': 'inline-block', 'width': '48%'}))
            except Exception as e:
                print(f"Error rendering Defect chart: {e}")
        
        # Chart 3: Lead Time Trend
        if 'lead_time' in selected_kpis:
            try:
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
                        line=dict(color=SECONDARY_COLOR, width=3),
                        marker=dict(size=6),
                        fillcolor='rgba(52, 152, 219, 0.1)',
                        hovertemplate='<b>%{x}</b><br>Lead Time: %{y:.1f} days<extra></extra>'
                    ))
                    fig_lt.update_layout(
                        title="Lead Time Trend Over Time",
                        yaxis_title="Days",
                        hovermode='x',
                        height=420,
                        margin=dict(l=60, r=60, t=80, b=60),
                        template='plotly_white',
                        font=dict(family="Segoe UI, sans-serif", size=12),
                        title_font_size=16,
                        showlegend=False
                    )
                    chart_divs.append(dcc.Graph(figure=fig_lt, style={'display': 'inline-block', 'width': '48%', 'marginRight': '2%'}))
            except Exception as e:
                print(f"Error rendering Lead Time chart: {e}")
        
        # Chart 4: Cost Variance
        if 'cost' in selected_kpis:
            try:
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
                    colors = ['#e74c3c' if x > 10 else '#f39c12' if x > 5 else '#27ae60' for x in cost_data['cost_var'].fillna(0)]
                    fig_cost = go.Figure(data=go.Bar(
                        x=cost_data['name'],
                        y=cost_data['cost_var'].fillna(0),
                        marker_color=colors,
                        text=[f"{x:.1f}%" if pd.notna(x) else "N/A" for x in cost_data['cost_var']],
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>Cost Variance: %{y:.1f}%<extra></extra>'
                    ))
                    fig_cost.update_layout(
                        title="Cost Variance by Supplier",
                        yaxis_title="Percentage (%)",
                        hovermode='x',
                        height=420,
                        margin=dict(l=60, r=60, t=80, b=60),
                        template='plotly_white',
                        font=dict(family="Segoe UI, sans-serif", size=12),
                        title_font_size=16,
                        showlegend=False
                    )
                    chart_divs.append(dcc.Graph(figure=fig_cost, style={'display': 'inline-block', 'width': '48%'}))
            except Exception as e:
                print(f"Error rendering Cost Variance chart: {e}")
        
        # Chart 5: Risk Score
        if 'risk' in selected_kpis:
            try:
                if selected_supplier == 'all':
                    risk_data = all_kpis_df[['Supplier', 'Supplier Risk Score (0-100)']].sort_values('Supplier Risk Score (0-100)', ascending=False)
                else:
                    supplier_name = pd.read_sql_query('SELECT name FROM Suppliers WHERE supplier_id = ?', conn, params=[selected_supplier])
                    risk_score = kpi_calc_local.supplier_risk_score(selected_supplier)
                    risk_data = pd.DataFrame({'Supplier': [supplier_name['name'].values[0]], 'Supplier Risk Score (0-100)': [risk_score]})
                
                if len(risk_data) > 0:
                    colors = ['#27ae60' if x < 50 else '#f39c12' if x < 75 else '#e74c3c' for x in risk_data['Supplier Risk Score (0-100)']]
                    fig_risk = go.Figure(data=go.Bar(
                        x=risk_data['Supplier'],
                        y=risk_data['Supplier Risk Score (0-100)'],
                        marker_color=colors,
                        text=[f"{x:.0f}" for x in risk_data['Supplier Risk Score (0-100)']],
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>Risk Score: %{y:.0f}/100<extra></extra>'
                    ))
                    fig_risk.update_layout(
                        title="Supplier Risk Score (0=Low Risk, 100=High Risk)",
                        yaxis_title="Score",
                        hovermode='x',
                        height=420,
                        margin=dict(l=60, r=60, t=80, b=60),
                        template='plotly_white',
                        font=dict(family="Segoe UI, sans-serif", size=12),
                        title_font_size=16,
                        showlegend=False
                    )
                    chart_divs.append(dcc.Graph(figure=fig_risk, style={'display': 'inline-block', 'width': '48%', 'marginRight': '2%'}))
            except Exception as e:
                print(f"Error rendering Risk Score chart: {e}")
        
        # Chart 6: Rejection Reasons
        if 'rejection' in selected_kpis:
            try:
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
                        hole=0.35,
                        marker=dict(colors=['#3498db', '#e74c3c', '#f39c12', '#27ae60', '#9b59b6']),
                        hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
                    ))
                    fig_reject.update_layout(
                        title="Rejection Reasons Distribution",
                        height=420,
                        margin=dict(l=60, r=60, t=80, b=60),
                        font=dict(family="Segoe UI, sans-serif", size=12),
                        title_font_size=16
                    )
                    chart_divs.append(dcc.Graph(figure=fig_reject, style={'display': 'inline-block', 'width': '48%'}))
            except Exception as e:
                print(f"Error rendering Rejection Reasons chart: {e}")
        
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
                        html.Th("Supplier", style={'padding': '14px', 'textAlign': 'left', 'backgroundColor': '#ecf0f1', 'borderBottom': '2px solid #bdc3c7', 'fontWeight': '600', 'fontSize': '13px', 'color': PRIMARY_COLOR}),
                        html.Th("PO ID", style={'padding': '14px', 'textAlign': 'left', 'backgroundColor': '#ecf0f1', 'borderBottom': '2px solid #bdc3c7', 'fontWeight': '600', 'fontSize': '13px', 'color': PRIMARY_COLOR}),
                        html.Th("Order Date", style={'padding': '14px', 'textAlign': 'left', 'backgroundColor': '#ecf0f1', 'borderBottom': '2px solid #bdc3c7', 'fontWeight': '600', 'fontSize': '13px', 'color': PRIMARY_COLOR}),
                        html.Th("Expected Delivery", style={'padding': '14px', 'textAlign': 'left', 'backgroundColor': '#ecf0f1', 'borderBottom': '2px solid #bdc3c7', 'fontWeight': '600', 'fontSize': '13px', 'color': PRIMARY_COLOR}),
                        html.Th("Quantity", style={'padding': '14px', 'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'borderBottom': '2px solid #bdc3c7', 'fontWeight': '600', 'fontSize': '13px', 'color': PRIMARY_COLOR}),
                        html.Th("Status", style={'padding': '14px', 'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'borderBottom': '2px solid #bdc3c7', 'fontWeight': '600', 'fontSize': '13px', 'color': PRIMARY_COLOR}),
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(row['name'], style={'padding': '12px 14px', 'borderBottom': '1px solid #ecf0f1', 'fontSize': '13px'}),
                        html.Td(f"PO-{row['po_id']}", style={'padding': '12px 14px', 'borderBottom': '1px solid #ecf0f1', 'fontWeight': '600', 'fontSize': '13px', 'color': SECONDARY_COLOR}),
                        html.Td(row['order_date'], style={'padding': '12px 14px', 'borderBottom': '1px solid #ecf0f1', 'fontSize': '13px'}),
                        html.Td(row['expected_delivery_date'], style={'padding': '12px 14px', 'borderBottom': '1px solid #ecf0f1', 'fontSize': '13px'}),
                        html.Td(row['order_quantity'], style={'padding': '12px 14px', 'textAlign': 'center', 'borderBottom': '1px solid #ecf0f1', 'fontSize': '13px'}),
                        html.Td(
                            row['status'],
                            style={
                                'padding': '12px 14px',
                                'textAlign': 'center',
                                'borderBottom': '1px solid #ecf0f1',
                                'color': SUCCESS_COLOR if row['status'] == 'Delivered' else WARNING_COLOR,
                                'fontWeight': '600',
                                'fontSize': '13px'
                            }
                        ),
                    ])
                    for _, row in open_pos_data.iterrows()
                ])
            ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '13px'})
        else:
            table = html.Div("No purchase orders found for selected filters", style={'textAlign': 'center', 'padding': '30px', 'color': '#95a5a6', 'fontSize': '14px'})
        
        # ML Predictions
        ml_content = html.Div()
        if selected_supplier != 'all':
            try:
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
                    
                    delay_color = '#e74c3c' if delay_prob > 60 else '#f39c12' if delay_prob > 40 else '#27ae60'
                    defect_color = '#e74c3c' if defect_prob > 50 else '#f39c12' if defect_prob > 30 else '#27ae60'
                    lt_color = '#27ae60' if lt_cat == 'On-time' else '#f39c12' if lt_cat == 'Early' else '#e74c3c'
                    
                    ml_content = html.Div([
                        html.H4(f"Risk Assessment for {name}", style={'marginBottom': '20px', 'fontSize': '15px', 'fontWeight': '600', 'color': PRIMARY_COLOR}),
                        html.Div([
                            html.Div([
                                html.H5("Delay Risk", style={'margin': '0 0 10px 0', 'fontSize': '11px', 'color': '#7f8c8d', 'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                                html.H3(f"{delay_prob}%", style={'color': delay_color, 'fontWeight': '700', 'margin': '0'}),
                                html.P("Probability of order delay", style={'fontSize': '12px', 'color': '#95a5a6', 'margin': '8px 0 0 0'})
                            ], style={
                                'width': '30%', 
                                'display': 'inline-block', 
                                'padding': '24px', 
                                'backgroundColor': CARD_BG,
                                'marginRight': '2%', 
                                'borderRadius': '8px', 
                                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                                'textAlign': 'center',
                                'borderTop': f'4px solid {delay_color}',
                                'transition': 'box-shadow 0.3s ease'
                            }),
                            
                            html.Div([
                                html.H5("Quality Risk", style={'margin': '0 0 10px 0', 'fontSize': '11px', 'color': '#7f8c8d', 'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                                html.H3(f"{defect_prob}%", style={'color': defect_color, 'fontWeight': '700', 'margin': '0'}),
                                html.P("Probability of high defect rate", style={'fontSize': '12px', 'color': '#95a5a6', 'margin': '8px 0 0 0'})
                            ], style={
                                'width': '30%', 
                                'display': 'inline-block', 
                                'padding': '24px', 
                                'backgroundColor': CARD_BG,
                                'marginRight': '2%', 
                                'borderRadius': '8px', 
                                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                                'textAlign': 'center',
                                'borderTop': f'4px solid {defect_color}',
                                'transition': 'box-shadow 0.3s ease'
                            }),
                            
                            html.Div([
                                html.H5("Lead Time Category", style={'margin': '0 0 10px 0', 'fontSize': '11px', 'color': '#7f8c8d', 'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                                html.H3(lt_cat, style={'color': lt_color, 'fontWeight': '700', 'margin': '0'}),
                                html.P("Expected delivery category", style={'fontSize': '12px', 'color': '#95a5a6', 'margin': '8px 0 0 0'})
                            ], style={
                                'width': '30%', 
                                'display': 'inline-block', 
                                'padding': '24px', 
                                'backgroundColor': CARD_BG,
                                'borderRadius': '8px', 
                                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                                'textAlign': 'center',
                                'borderTop': f'4px solid {lt_color}',
                                'transition': 'box-shadow 0.3s ease'
                            }),
                        ])
                    ])
            except Exception as e:
                print(f"Error generating ML predictions: {e}")
                ml_content = html.Div(f"Unable to generate predictions: {str(e)}", style={'color': ACCENT_COLOR, 'padding': '20px'})
        else:
            ml_content = html.Div(
                "Select a specific supplier to view AI-powered risk predictions",
                style={'textAlign': 'center', 'padding': '40px', 'color': '#95a5a6', 'fontSize': '14px'}
            )
        
        return kpi_cards, charts_container, table, ml_content
        
    except Exception as e:
        print(f"Error in callback: {e}")
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
    print("Supplier Relationship Management Dashboard")
    print("="*60)
    print("\nDashboard ready!")
    print("Open your browser and go to: http://127.0.0.1:8050/")
    print("\n" + "="*60 + "\n")
    app.run_server(debug=False, port=8050)
