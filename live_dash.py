import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pyodbc
import datetime
from plotly.subplots import make_subplots
import pandas as pd
import time

tic = time.perf_counter()
db = pyodbc.connect('Driver={SQL Server}; SERVER=SERVER-AGV;DATABASE=Vulkoprin;UID=cerastore;PWD=cerastore')
toc = time.perf_counter()
print(f"Connected to DB in {toc - tic:0.4f} seconds")
toc=0
tic=0
tic = time.perf_counter()

df_hist = pd.read_sql("Select * from Production order by [Date] desc", db)
toc = time.perf_counter()
print(f"Performed query in {toc - tic:0.4f} seconds")
toc=0
tic=0

df_act=pd.read_sql("Select * from VUL_Production where [Date]>GETDATE()-1 order by DateTransaction asc", db)
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([

    dcc.Tabs([
        dcc.Tab(label='KPI', children=[
            html.Div(children=['Dashboard PUR ' + datetime.date.today().strftime('%d/%m/%Y')]),
            dcc.Graph(id='gauges'),
            dcc.Graph(id='bars')
            ]),
        dcc.Tab(label='Historisch', children=[
            dcc.Graph(id='fig_hist'),
        dcc.Slider(
            id='hist-slider',
            min=df_hist['Date'].dt.year.min(),
            max=df_hist['Date'].dt.year.max(),
            value=df_hist['Date'].dt.year.max(),
            marks={str(year): str(year) for year in df_hist['Date'].dt.year.unique()},
            step=None),
            ]
                )]),
    
    
    dcc.Interval(
            id='interval-component',
            interval=5*60*1000, # in milliseconds, elke 5 min automatische update
            n_intervals=0
        )
])
#historisch
@app.callback(
    Output('fig_hist', 'figure'),
    Input('hist-slider', 'value'))

def update_figure(selected_year):
    print(selected_year)
    # now the colors
    clrred = 'rgb(222,0,0)'
    clrgrn = 'rgb(0,222,0)'
    filter_df = df_hist[df_hist['Date'].dt.year == selected_year]
    filter_df = filter_df.reset_index()
    print(filter_df)
    clrs=['green' if filter_df['OPCount'].loc[x] >= 288 else 'red' for x in range(len(filter_df.index)-1)]
    print(clrs)
    clrs1=["green","red",'blue']*len(filter_df.index)
    #fig = px.bar(filter_df, x="Date", y="OPCount", marker=dict(color=clrs))
    fig1=go.Figure(go.Bar(x=filter_df["Date"],y=filter_df['OPCount'], marker_color=clrs))
    #fig.update_layout(transition_duration=500)

    return fig1

#gauges
@app.callback(Output('gauges', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_figure(n):
    
    try:
        print('try gauges start', datetime.datetime.now())
       
        tic = time.perf_counter()
        df_hist = pd.read_sql("Select * from Production order by [Date] desc", db)
        toc = time.perf_counter()
        print('gauge ok')
    except:
        print('gauges error')
    
    #Aantal MP
    doel = df_hist['DoelPallet'].loc[0]
    actueel = df_hist['ActueelPallet'].loc[0]
    if actueel>=0.8*doel:
        gauge_mp = {'axis': {'range': [None, 352]},
                     'threshold' : {'line': {'color': "red", 'width': 4}, 
                     'thickness': 0.75, 
                     'value': 0.8*doel}, 
                     'bar': {'color': "limegreen"}}
    elif 0.7*doel<actueel<0.8*doel:
        gauge_mp ={'axis': {'range': [None, 352]},
                 'threshold' : {'line': {'color': "red", 'width': 4}, 
                 'thickness': 0.75, 
                 'value': 0.8*doel}, 
                 'bar': {'color': "orange"}}
    else: 
        gauge_mp ={'axis': {'range': [None, 352]},
                 'threshold' : {'line': {'color': "red", 'width': 4}, 
                 'thickness': 0.75, 
                 'value': 0.8*doel}, 
                 'bar': {'color': "red"}}

    fig1 = (go.Indicator(
        domain = {'x': [0, 1], 'y': [0, 1]},
        value = actueel,
        mode = "gauge+number+delta",
        delta = {'reference': round(0.8*doel,0)},
        title={'text': 'Aantal MP'},
        gauge = gauge_mp
        ))
    #Lege doorgangen
    OP = df_hist['OPCount'].loc[0]
    MP = df_hist['MPCount'].loc[0]
    if (OP/MP*100)<70:
        gauge_ld = {'axis': {'range': [None, 100]},
                     'threshold' : {'line': {'color': "red", 'width': 4}, 
                     'thickness': 0.75, 
                     'value': 80}, 
                     'bar': {'color': "red"}}
    elif 70<=(OP/MP*100)<=80:
        gauge_ld = {'axis': {'range': [None, 100]},
                     'threshold' : {'line': {'color': "red", 'width': 4}, 
                     'thickness': 0.75, 
                     'value': 80}, 
                     'bar': {'color': "orange"}}
    else:
        gauge_ld = {'axis': {'range': [None, 100]},
                     'threshold' : {'line': {'color': "red", 'width': 4}, 
                     'thickness': 0.75, 
                     'value': 80}, 
                     'bar': {'color': "limegreen"}}
    fig2 = (go.Indicator(
            domain = {'x': [0, 1], 'y': [0, 1]},
            value = round(OP/MP*100,2),
            mode = "gauge+number",
            title={'text': 'Lege doorgangen'},
            gauge = gauge_ld
            ))

    #Aantal KG
    KG = df_hist['TotalWeight'].loc[0]
    KGDoel = df_hist['TargetWeight'].loc[0]
  
    if KG<0.70*KGDoel:
        gauge_kg = {'axis': {'range': [None, 2500]},
                     'threshold' : {'line': {'color': "red", 'width': 4}, 
                     'thickness': 0.75, 
                     'value': 0.80*KGDoel}, 
                     'bar': {'color': "red"}}
    elif 0.70*KGDoel<=(KG)<=0.80*KGDoel:
        gauge_kg = {'axis': {'range': [None, 2500]},
                     'threshold' : {'line': {'color': "red", 'width': 4}, 
                     'thickness': 0.75, 
                     'value': 0.80*KGDoel}, 
                     'bar': {'color': "orange"}}
    else:
        gauge_kg = {'axis': {'range': [None, 2500]},
                     'threshold' : {'line': {'color': "red", 'width': 4}, 
                     'thickness': 0.75, 
                     'value': 0.80*KGDoel}, 
                     'bar': {'color': "limegreen"}}
    fig3 = (go.Indicator(
            domain = {'x': [0, 1], 'y': [0, 1]},
            value = KG,
            mode = "gauge+number",
            title={'text': "Gegoten KG's"},
            gauge = gauge_kg
            ))

    #Subplot
    fig_subplot = make_subplots(rows=1, cols=3, specs=[[{'type':'indicator'}, {'type':'indicator'}, {'type':'indicator'}]])
    fig_subplot.add_trace(fig1, row=1,col=1)
    fig_subplot.add_trace(fig2, row=1, col=2)
    fig_subplot.add_trace(fig3, row=1, col=3)
    fig_subplot.update_layout(autosize=True)
    print('gauges updated')
    return fig_subplot

#bars
@app.callback(Output('bars', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_figure(n):
    today = datetime.date.today()
    week = datetime.date.today().isocalendar()[1]
    year = datetime.date.today().isocalendar()[0]
    df_hist_filtered = df_hist[df_hist['Date'].dt.isocalendar().week == week] 
    df_hist_filtered=df_hist_filtered[df_hist_filtered['Date'].dt.year == year]
    fig_dezeweek = px.bar(df_hist_filtered, x='Date', y='OPCount')

    try:
        time.sleep(5)
        print('start try bars', datetime.datetime.now())
        df_act=pd.read_sql("Select * from VUL_Production where [Date]>GETDATE()-1 order by DateTransaction asc", db)
        
    except:
        print('error bars')
    
    fig_bars= make_subplots(rows=1, cols=2,subplot_titles=("Vandaag", "Deze week"))
    fig_bars.add_trace(go.Bar(x=df_act['DateTransaction'], y=-1*(df_act['OPCount']-df_act['OPCount'].shift(-1))), row=1,col=1)
    fig_bars.add_trace(go.Bar(x=df_hist_filtered["Date"], y=df_hist_filtered['OPCount']),row=1,col=2 )
    fig_bars.update_traces(marker=dict(color="RoyalBlue"))
    fig_bars.add_trace(go.Line(x=df_act['DateTransaction'], y = [22]*df_act.size),row=1,col=1)
    fig_bars.add_trace(go.Line(x=df_hist_filtered['Date'], y = df_hist_filtered['DoelPallet'], marker=dict(color='limegreen')),row=1,col=2)
    fig_bars.add_trace(go.Line(x=df_hist_filtered['Date'], y = df_hist_filtered['DoelPallet']*0.8, marker=dict(color='limegreen')),row=1,col=2)

    fig_bars.update_layout(showlegend=False,autosize=True)
   
    print('bars updated')
    return fig_bars

if __name__ == '__main__':
    app.run_server(debug=True)