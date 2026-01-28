# Standard Imports
import dash
from dash import dcc
from dash import html
import pandas as pd
import plotly.graph_objects as go

analytics = pd.DataFrame({'country': ['USA', 'UK', 'France', 'Germany', ' China', 'Pakistan', 'India'],
                          'users': [1970, 950, 760, 810, 2800, 1780, 2250],
                          'page_views': [2500, 1210, 760, 890, 3200, 1910, 2930],
                          'avg_duration': [75, 60, 63, 79, 57, 61, 72],
                          'bounce_rate': [51, 65, 77, 43, 54, 57, 51]})

# ======================== Setting the margins
layout = go.Layout(
    margin=go.layout.Margin(
        l=40,  # left margin
        r=40,  # right margin
        b=10,  # bottom margin
        t=35  # top margin
    )
)

# ======================== Plotly Graphs
def get_bar_chart():
    barChart = dcc.Graph(figure=go.Figure(layout=layout).add_trace(go.Bar(x=analytics['country'],
                                                                          y=analytics['users'],
                                                                          marker=dict(color='#351e15'))).update_layout(
        title='Users', plot_bgcolor='rgba(0,0,0,0)'),
        style={'width': '50%', 'height': '40vh', 'display': 'inline-block'})
    return barChart


def get_line_chart():
    lineChart = dcc.Graph(figure=go.Figure(layout=layout).add_trace(go.Scatter(x=analytics['country'],
                                                                               y=analytics['page_views'],
                                                                               marker=dict(
                                                                                   color='#351e15'))).update_layout(
        title='Page Views', plot_bgcolor='rgba(0,0,0,0)'),
        style={'width': '50%', 'height': '40vh', 'display': 'inline-block'})
    return lineChart


def get_scatter_plot():
    scatterPlot = dcc.Graph(figure=go.Figure(layout=layout).add_trace(go.Scatter(x=analytics['country'],
                                                                                 y=analytics['avg_duration'],
                                                                                 marker=dict(
                                                                                     color='#351e15'),
                                                                                 mode='markers')).update_layout(
        title='Average Duration', plot_bgcolor='rgba(0,0,0,0)'),
        style={'width': '50%', 'height': '40vh', 'display': 'inline-block'})
    return scatterPlot


def get_pie_chart():
    pieChart = dcc.Graph(
        figure=go.Figure(layout=layout).add_trace(go.Pie(
            labels=analytics['country'],
            values=analytics['bounce_rate'],
            marker=dict(colors=['#120303', '#300f0f', '#381b1b', '#4f2f2f', '#573f3f', '#695a5a', '#8a7d7d'],
                        line=dict(color='#ffffff', width=2)))).update_layout(title='Bounce Rate',
                                                                             plot_bgcolor='rgba(0,0,0,0)',
                                                                             showlegend=False),
        style={'width': '50%', 'height': '40vh', 'display': 'inline-block'})
    return pieChart


# ======================== Dash App
app = dash.Dash(__name__)

# ======================== App Layout
app.layout = html.Div([
    html.H1('Website Analytics Dashboard', style={'text-align': 'center', 'background-color': '#ede9e8'}),
    get_bar_chart(),
    get_line_chart(),
    get_scatter_plot(),
    get_pie_chart()
])

if __name__ == '__main__':
    app.run_server()