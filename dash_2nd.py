# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
# df = pd.DataFrame({
#     "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
#     "Amount": [4, 1, 2, 2, 4, 5],
#     "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
# })
df = pd.read_csv(r'C:\LitePoint\Talladega\BRCM4398\CBW_20_160_MCS_0_to_13_NSS_1\BRCM4398_PER.csv')
fig = px.line(df, x="power_level", y="per_percentage", color="data_rate")

app.layout = html.Div(children=[
    html.H1(children='PER Sweep'),

    html.Div(children='''
        BRCM4398 ACK-based PER sweep using waveforms by IQwavegen
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
