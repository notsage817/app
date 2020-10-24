
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import datetime as dt
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pymongo
import dns
import json
import dash_bootstrap_components as dbc
import plotly
from plotly.offline import plot
import random
import yfinance as yf

stocks=['AAPL','GOOG','NFLX','SPY','TSLA']
end_date=dt.datetime.today()
start_date=dt.datetime(2015,10,20)

stats_choice=['return','MA5','MA10','MA22','vol5','vol30','week_mmtm','month_mmtm']

app=dash.Dash()
server=app.server


app.layout = html.Div([
    html.Br(),
    html.Br(),
    
    html.Div([
        html.H1('Stocks Performance', className='ten columns', style={'textAlign':'center','color':'#CD5C5C'})]),
    
    html.Div([
        html.Img(src='https://images.squarespace-cdn.com/content/5c036cd54eddec1d4ff1c1eb/1557908564936-YSBRPFCGYV2CE43OHI7F/GlobalAI_logo.jpg?content-type=image%2Fpng',
            style={
                'height':'11%',
                'width':'11%',
                'float':'right',
                'position':'relative',
                'margin-top':11,
                'margin-right':0
            },className = 'two columns'),],style={'border':'blue solid',},className='row'),
    html.Br(),
    html.Br(),
    
    
    html.Div([
        html.H3('Select Stocks:', style={'paddingRight': '20px'},className='two columns'),
        dcc.Dropdown(id='labels',value='AAPL',options=[{'label':i,'value':i} for i in stocks])],
                style={'verticalAlign': 'top','width':'48%','display': 'inline-block'}),
    html.Br(),
    html.Br(),
    
    html.Div([
        html.H3('Select statistics',style={'paddingLeft': '20px'}),
        dcc.Dropdown(id='statistic',value='return',options=[{'label':i,'value':i} for i in stats_choice])],
                style={'verticalAlign':'top','width':'48%','display':'inline-block'}),
        
    html.Div([
        html.H3('Select interval'),
                dcc.DatePickerRange(id='Date',min_date_allowed=dt.datetime(2015,10,20),max_date_allowed=dt.datetime.today(),\
                                     start_date=dt.datetime(2015,10,20),end_date=dt.datetime.today())],
                style={'verticalAlign':'top','display':'inline-block'}),
    html.Div([
                html.Button(id='submit_button',n_clicks=0,children='Submit',style={'fontSize': 18})],
                style={'display': 'inline-block'}),
    html.Br(),
    html.Br(),
    
    html.Div([dcc.Graph(id="trend", style={'border-style': 'solid'})]),

        html.Br(),
        
        html.Div([dcc.Graph(id="movingaverage", style={'border-style': 'solid'})]),
        
        html.Br(),
        
        html.Div([dcc.Graph(id="momentum", style={'border-style': 'solid'})]),
        
        html.Br(),
        
        dbc.Row([dbc.Col([dcc.Graph(id='scatter'),dcc.Graph(id="heatmap")])]),
        
        html.Br()
])

@app.callback(
    [Output('trend', 'figure'),
     Output('movingaverage', 'figure'),
     Output('momentum', 'figure'),
    Output('scatter','figure'),
    Output('heatmap','figure')],
    [Input('submit_button', 'n_clicks')],
    [State('labels', 'value'),
     State('statistic', 'value'),
     State('Date', 'start_date'),
     State('Date', 'end_date')])
def update_graph(n_clicks,label,statistics,start_date,end_date):

    start=dt.datetime.strptime(start_date[:10],'%Y-%m-%d')
    end=dt.datetime.strptime(end_date[:10],'%Y-%m-%d')
    la=label
    raw_data=yf.download(stocks,start,end)['Adj Close']
    
    columns=['return','MA5','MA10','MA22','vol5','vol30','week_mmtm','month_mmtm']
    stats=pd.DataFrame(None,index=raw_data.index,columns=pd.MultiIndex.from_product([stocks,columns]))
    for stock in stocks:
        stats[stock,'return']=raw_data[stock]/raw_data[stock].shift(1)-1
        stats[stock,'MA5']=raw_data[stock].rolling(5).mean()
        stats[stock,'MA10']=raw_data[stock].rolling(10).mean()
        stats[stock,'MA22']=raw_data[stock].rolling(22).mean()
        stats[stock,'vol5']=raw_data[stock].rolling(5).std()
        stats[stock,'vol30']=raw_data[stock].rolling(30).std()
        stats[stock,'week_mmtm']=raw_data[stock]-raw_data[stock].shift(5)
        stats[stock,'month_mmtm']=raw_data[stock]-raw_data[stock].shift(22)
    #trend
    tr1=go.Scatter(x=list(raw_data.index),y=list(raw_data[la]),mode='lines',name="Adj Close Price of "+la)
    tr2=go.Scatter(x=list(stats.index),y=list(stats[la,statistics]),mode='lines',name=statistics+' of '+la)
    tr3=go.Scatter(x=list(raw_data.index),y=list(raw_data['SPY']),mode='lines',name="Adj Close Price of S&P ETF")
    trend=go.Figure(data=[tr1,tr2,tr3],
                 layout={'title':f"Adj Close Price & {statistics} of {label} "})
    
    #Movingaverage
    
    ma1=go.Scatter(x=list(stats.index),y=list(stats[la,'MA5']),mode='lines',name=la+' MA5')
    ma2=go.Scatter(x=list(stats.index),y=list(stats[la,'MA10']),mode='lines',name=la+' MA10')
    ma3=go.Scatter(x=list(stats.index),y=list(stats[la,'MA22']),mode='lines',name=la+' MA22')
    movingaverage=go.Figure(data=[tr1,ma1,ma2,ma3],layout={'title':f"Moving Average Prices of {label}"})
    
    #momentum
    mo1=go.Scatter(x=list(stats.index),y=list(stats[la,'week_mmtm']),mode='lines',name=la+' Weekly momentum ')
    mo2=go.Scatter(x=list(stats.index),y=list(stats[la,'month_mmtm']),mode='lines',name=la+' monthly momentum ')
    momentum=go.Figure(data=[tr1,mo1,mo2],layout={'title': f"Momentums of {la} "})
    
    
    #scatter
    sc=go.Scatter(x=list(stats[la,'return']),y=list(stats['SPY','return']),mode='markers',name='SPY & '+la)
    scatter=go.Figure(data=sc,layout={'title':f"{la} & SPY returns scallter plot "})
    

    #heatmap
    ret=stats[pd.MultiIndex.from_product([stocks, ['return']])]
    ret.index=stats.index
    he=go.Heatmap(x=stocks,y=stocks,z=ret.corr(),colorscale='Jet')
    heatmap=go.Figure(data=he,layout={'title':"covariance of returns"})
    return trend, movingaverage, momentum, scatter, heatmap


if __name__ == '__main__':
    app.run_server(debug=True)
