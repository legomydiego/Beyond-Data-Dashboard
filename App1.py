import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import dash_table
from plotly import tools
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output, State
from babel.numbers import format_currency
from DateTime import DateTime
from datetime import datetime

# Styling
external_stylesheets = [
    'https://fonts.googleapis.com/css?family=Open+Sans:400,700&display=swap',
    'https://fonts.googleapis.com/css?family=Source+Sans+Pro:600',
    'https://use.fontawesome.com/releases/v5.7.2/css/all.css'
]

# List of user and password combos
USERNAME_PASSWORD_PAIRS = [
    ['BeyondData', 'Demo123']
]

# Launch the application:
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets
)
auth = dash_auth.BasicAuth(app,USERNAME_PASSWORD_PAIRS)
server = app.server
app.config['suppress_callback_exceptions']=True
# Create a DataFrame from the .csv file:
df = pd.read_excel('Sample DF.xlsm').round(3)
df_hp = pd.read_excel('Sample DF.xlsm','Historical Prices').round(3)
df_cf = pd.read_excel('Sample DF.xlsm','Cash Flow')

#Create a dataframe for returns indexed to 100
rets = df_hp.set_index('DATE')
rets.sort_index(inplace=True)
rets = np.log(rets / rets.shift(1))
for bond in list(rets.columns):
    rets[bond] = 100*np.exp(np.nan_to_num(rets[bond].cumsum()))
rets.sort_index(inplace=True, ascending=False)
rets.reset_index(inplace= True)

#Portfolio Metrics
Face_Value = round(df['ADJ'].sum(),2)
Market_Value = round(df['PRINCIPAL'].sum(),2)
Accrued_Interest = round(df['INT'].sum(),2)
Cost = round(sum(df['ADJ']*df['COST']/100),2)
PNL = round((Market_Value+Accrued_Interest-Cost),2)
PNL_PCT = round(PNL/Cost,2)
Annual_Income = round(sum(df['ADJ']*df['COUPON']/100),2)
Average_Yield = round(sum(df['TOTAL']*df['YTW']/sum(df['TOTAL'])),3)
Average_Maturity = round(sum(df['TOTAL']*df['MATURITY']/sum(df['TOTAL'])),2)
Average_Coupon = round(sum(df['TOTAL']*df['COUPON']/sum(df['TOTAL'])),3)
Average_Duration = round(sum(df['TOTAL']*df['DUR']/sum(df['TOTAL'])),3)

    #Average rating calculation
Rating_String = ['AAA','AAA/*+','AAA/*-','AA+','AA+/*+','AA+/*-','AA','AA/*+','AA/*-','AA-','AA-/*+','AA-/*-','A+','A+/*+','A+/*-','A','A/*+','A/*-','A-','A-/*+','A-/*-','BBB+','BBB+/*+','BBB+/*-','BBB','BBB/*+','BBB/*-','BBB-','BBB-/*+','BBB-/*-','BB+','BB+/*+','BB+/*-','BB','BB/*+','BB/*-','BB-','BB-/*+','BB-/*-','B+','B+/*+','B+/*-','B','B/*+','B/*-','B-','B-/*+','B-/*-','CCC+','CCC+/*+','CCC+/*-','CCC','CCC/*+','CCC/*-','CCC-','CCC-/*+','CCC-/*-','CC','CC/*+','CC/*-','C','C/*+','C/*-','D','D/*+','D/*-','Other']
Rating_Value = [23,23,23,22,22,22,21,21,21,20,20,20,19,19,19,18,18,18,17,17,17,16,16,16,15,15,15,14,14,14,13,13,13,12,12,12,11,11,11,10,10,10,9,9,9,8,8,8,7,7,7,6,6,6,5,5,5,4,4,4,3,3,3,2,2,2,1]
Rating_Lookup = dict(zip(Rating_String, Rating_Value))
df['RATING_NUMERIC'] = df['RATING'].apply(lambda x: Rating_Lookup[x])
Average_Rating = list(Rating_Lookup.keys())[list(Rating_Lookup.values()).index(round(sum(df['TOTAL']*df['RATING_NUMERIC']/sum(df['TOTAL']))))]

#Total Return calculation
days=30
day_count=360
df['CARRY'] = round((df['COUPON']/100*df['FACE']*days/day_count)/df['ADJ'],3)
df['TOTAL_RETURN'] = round((df['CHANGE'] + df['CARRY'])*100,3)

#Strings for metrics
String_Face_Value = format_currency(Face_Value,'USD',locale='en_US')
String_Market_Value = format_currency(Market_Value,'USD',locale='en_US')
String_Accrued_Interest = format_currency(Accrued_Interest,'USD',locale='en_US')
String_Cost = format_currency(Cost,'USD',locale='en_US')
String_PNL = format_currency(PNL,'USD',locale='en_US')
String_PNL_PCT = ' ('+str(PNL_PCT)+'%)'
String_Annual_Income = format_currency(Annual_Income,'USD',locale='en_US')
String_Average_Yield = str(Average_Yield)+'%'
String_Average_Maturity = str(Average_Maturity)
String_Average_Coupon = str(Average_Coupon)+'%'
String_Average_Duration = str(Average_Duration)
String_Average_Rating = Average_Rating

# Dropdown options for risk exposure
options=['COUNTRY','SECTOR','RATING']

# Create sorting list for rating exposure graph and convert rating column to categorical 
rating_sort_list = list(i for i in Rating_String if i in df['RATING'].unique())
df['RATING'] = pd.Categorical(df['RATING'], Rating_Lookup)

# Create df for ratings and filters rows with 0 on its values
df_rating = df.groupby('RATING').sum().sort_values('RATING')
df_rating = df_rating[df_rating[df_rating==0].all(axis=1)]

# Create index for duration graph by converting to datetime
#duration_int_list = df.groupby('DURATION').sum()['ADJ'].sort_values(ascending=False).index.tolist()
#duration_str_list = list(map(str, duration_int_list))
#datetime_list = []
#for year in duration_str_list:
#    datetime_list.append(datetime.strptime(year, '%Y'))

# Dropdown options for historical price graph
options_hp= []
for bond in list(df_hp.columns[1:]):
        mydict={}
        mydict['label']=bond
        mydict['value']=bond
        options_hp.append(mydict)

# Create traces for the initial historical price graph
hp_traces=[]
for bond in list(df_hp.columns[1:]):
    hp_traces.append({'x':df_hp['DATE'],'y':df_hp[bond],'name':bond})

# Create traces for the initial historical price graph
rets_traces=[]
for bond in list(df_hp.columns[1:]):
    rets_traces.append({'x':rets['DATE'],'y':rets[bond],'name':bond})

# For Cash Flow df, convert columns to strings, move index to bonds column
#df_cf.columns[1:] = df_cf.columns[1:].strftime("%b %Y")
header_values = df_cf.columns.tolist()
header_values_string = ['<b>Bond</b>']
for col in header_values[1:]:
    header_values_string.append('<b>'+col.strftime("%b %Y")+'</b>')
df_cf.reset_index(inplace=True)
print(header_values_string[1:])
print(df_cf.sum()[-12:])
#print(df_cf.T.values.tolist())
#df_cf.rename({'index':'Bond'}, axis=1, inplace=True)

# Create list with alternating colors for cash flow rows
odd_row = ['rgba(47,84,118,0.075)']
even_row = ['rgb(255,255,255)'] 
cf_row_colors = [odd_row]
for row in range(len(df_cf.T.values.tolist())):
    if row%2 == 1:
        cf_row_colors.append(odd_row)
    else:
        cf_row_colors.append(even_row)
#print(cf_row_colors)
cf_row_colors = list(map(list, np.transpose(cf_row_colors)))
print(cf_row_colors)

#Function to build left nav
# Diego, uncomment this and comment the other left_nav function to make it look like what you actually want
def left_nav():
    return ''

# def left_nav():
#     return html.Div([
#         html.Img(src='../assets/profile.jpg', className='profile'),
#         nav_item('user', 'Account', ''),
#         nav_item('globe-americas', 'Portfolio', 'nav-selected'),
#         nav_item('envelope-open-text', 'Alerts', '')
#     ],className='leftnav')

def nav_item(icon, name, selected):
    return html.Div([
        html.Span('', className='fas fa-' + icon),
        ' ' + name
    ], className= selected + ' nav-option')

def header():
    return html.Div([
        logo(),
        tabs(),
        user_container()
    ], className='header')

def tabs():
    return html.Div([
        dcc.Tabs(id="tabs-example", value='metrics', children=[
        dcc.Tab(label='Metrics', value='metrics'),
        dcc.Tab(label='Risk Exposure', value='risk-exposure'),
        dcc.Tab(label='Performance', value='performance'),
        dcc.Tab(label='Cash Flow', value='cash-flow'),
        dcc.Tab(label='Price History', value='price-history'),
        dcc.Tab(label='Detailed View', value='detailed-view')
        ])
    ], className='maincontent')

def user_container():
    return html.Div([
        'Some user stuff!'
    ], className='user')

def logo():
    return html.Div([
        '',
        html.Img(src='../assets/Logo.png', className='logo')
    ], className='logo')

def tab_container(title, insides):
    return html.Div([
        insides
    ], className='tabcontainer')

def metric_item(title, value):
    return html.Div([
        html.Div(title, className='metricTitle'),
        html.Div(value, className='metricValue')
    ], className='metricCard')

def metric_large(title, value, percent):
    return html.Div([
        html.Div(title, className='metricTitle'),
        html.Div(value, className='metricValue'),
        html.Div(percent, className='metricPercent')
    ], className='metricCard')

def tab_metrics():
    return html.Div([
        html.H1('Portfolio Snapshot'),
        html.Div([
            html.Div([
                metric_large('PROFIT & LOSS', String_PNL, String_PNL_PCT)
            ], className='facevalue'),
            html.Div([
                metric_item('FACE VALUE', String_Face_Value),
                metric_item('MARKET VALUE', String_Market_Value),
                metric_item('ACCRUED INTEREST', String_Accrued_Interest),
                metric_item('COST', String_Cost),
                metric_item('ANNUAL INCOME', String_Annual_Income),
                metric_item('AVERAGE RATING', String_Average_Rating),
                metric_item('AVERAGE COUPON', String_Average_Coupon),
                metric_item('AVERAGE YIELD', String_Average_Yield),
                metric_item('AVERAGE MATURITY', String_Average_Maturity),
                metric_item('AVERAGE DURATION', String_Average_Duration)
            ], className='othermetrics')

        ],className='row tabsrow'),
        html.H1('Portfolio Status'),
        html.Div([
            dcc.Graph(id='portfolio-bubble-graph',
                figure = {'data': [go.Scatter(          # start with a normal scatter plot
                    x=df['DUR'],
                    y=df['YTW'],
                    text=df['DESCRIPTION'],
                    mode='markers',
                    marker=dict(size=df['ADJ']/10000) # set the marker size
                    )],
                    'layout' : go.Layout(
                        xaxis = dict(title = '<b>Duration</b>', tickmode='linear'), # x-axis label
                        yaxis = dict(title = '<b>Yield (%)</b>'),        # y-axis label
                        hovermode='closest'
                    )
                }
            )
        ], className='status-container')
    ])

def tab_risk_exposure():
    trace_country = go.Bar(
                        x=df.groupby('COUNTRY').sum()['ADJ'].sort_values(ascending=False).index,
                        y=df.groupby('COUNTRY').sum()['ADJ'].sort_values(ascending=False),
                        marker=dict(color='rgb(230,115,0)')
                    )
    trace_ticker = go.Bar(
                        x=df.groupby('TICKER').sum()['ADJ'].sort_values(ascending=False).index,
                        y=df.groupby('TICKER').sum()['ADJ'].sort_values(ascending=False),
                        marker=dict(color='rgb(230,115,0)')
                    )
    trace_sector = go.Bar(
                        x=df.groupby('SECTOR').sum()['ADJ'].sort_values(ascending=False).index,
                        y=df.groupby('SECTOR').sum()['ADJ'].sort_values(ascending=False),
                        marker=dict(color='rgb(230,115,0)')
                    )
    trace_currency = go.Bar(
                        x=df.groupby('CURRENCY').sum()['ADJ'].sort_values(ascending=False).index,
                        y=df.groupby('CURRENCY').sum()['ADJ'].sort_values(ascending=False),
                        marker=dict(color='rgb(230,115,0)')
                    )
    trace_rating = go.Bar(
                        x=df_rating['ADJ'].index,
                        y=df_rating['ADJ'],
                        marker=dict(color='rgb(230,115,0)')
                    )
    trace_duration = go.Bar(
                        x=df.groupby('DURATION').sum()['ADJ'].sort_values(ascending=False).index,
                        y=df.groupby('DURATION').sum()['ADJ'].sort_values(ascending=False),
                        marker=dict(color='rgb(230,115,0)')
                    )
    
    layout_country = go.Layout(title='Country Exposure', showlegend=False)
    layout_ticker = go.Layout(title='Issuer Exposure', showlegend=False)
    layout_sector = go.Layout(title='Sector Exposure', showlegend=False)
    layout_currency = go.Layout(title='Currency Exposure', showlegend=False)
    layout_rating = go.Layout(title='Rating Exposure', showlegend=False)
    layout_duration = go.Layout(title='Duration Ladder', showlegend=False, xaxis=dict(dtick=1,tickmode='linear'))

    fig_country = {'data':[trace_country], 'layout': layout_country}
    fig_ticker = {'data':[trace_ticker], 'layout': layout_ticker}
    fig_sector = {'data':[trace_sector], 'layout': layout_sector}
    fig_currency = {'data':[trace_currency], 'layout': layout_currency}
    fig_rating = {'data':[trace_rating], 'layout': layout_rating}
    fig_duration = {'data':[trace_duration], 'layout': layout_duration}
    

    return html.Div([

        html.Div([
            dcc.Graph(id='risk-country', figure = fig_country )
        ]),
        html.Div([
            dcc.Graph(id='risk-ticker', figure = fig_ticker)
        ]),
        html.Div([
            dcc.Graph(id='risk-sector', figure = fig_sector)
        ]),
        html.Div([
            dcc.Graph(id='risk-currency', figure = fig_currency)
        ]),
        html.Div([
            dcc.Graph(id='risk-rating', figure = fig_rating)
        ]),
        html.Div([
            dcc.Graph(id='risk-duration', figure = fig_duration)
        ])        
    ])


app.layout = html.Div([
    header(),
    html.Div(id='tabs-content-example')
], className='container')

#Callback to render tabs
@app.callback(Output('tabs-content-example', 'children'),
              [Input('tabs-example', 'value')])
def render_content(tab):
    if tab == 'metrics':
        return tab_container('Metrics', tab_metrics())
    elif tab == 'risk-exposure':
        return tab_container('Risk Exposure', tab_risk_exposure())
    elif tab == 'performance':
        return tab_container('Performance', html.Div([
            html.Div([
                dcc.Dropdown(
                    id='column_filter',
                    options= [{'label': 'Country Exposure', 'value': 'COUNTRY'},
                             {'label': 'Sector Exposure', 'value': 'SECTOR'},
                             {'label': 'Rating Exposure', 'value': 'RATING'}],
                    multi=False
            )], style={'display':'inline-block','width':'30%'}),
            html.Div([
                dcc.Dropdown(
                    id='value_filter',
                    multi=False
            )], style={'display':'inline-block','width':'30%'}),
            html.Div([
                html.Button(id='filter-button',
                    n_clicks=0,
                    children = 'Submit',
                    style={'fontsize':24,'marginLeft':'30px'}
                )],style={'display':'inline-block','verticalAlign':'top'}),
            html.Div([
                dcc.Graph(id='total_return_graph',
                figure = {'data':[go.Bar(
                            y=df['DESCRIPTION'],
                            x=df['CHANGE']*100,
                            name='Price Change',
                            marker=dict(color='rgb(224,141,60)'),
                            orientation= 'h'
                            ),
                        go.Bar(
                            y=df['DESCRIPTION'],
                            x=df['CARRY']*100,
                            text=df['CARRY']*100,
                            name='Carry',
                            marker=dict(color='rgb(0,51,102)'),
                            orientation= 'h'
                            ),
                        go.Bar(
                            y=df['DESCRIPTION'],
                            x=df['TOTAL_RETURN'],
                            name='Total Return',
                            marker=dict(color='rgb(93,173,236)'),
                            orientation= 'h'
                            )
                        ],
                        'layout': go.Layout(
                            title = 'Total Return Components',
                            yaxis = {'automargin': True, 'visible': True, 'showgrid': True, 'gridcolor':'rgb(179,170,170)'},
                            xaxis = dict(dtick=1, tickfont = dict(size= 11)),
                            hovermode= 'closest',
                            height= 70*len(df.index)
                        )
                    }
                
                )
            ],style={'max-height':'800px', 'overflow-y': 'auto', 'position': 'relative'})
            
        ]))
    elif tab == 'cash-flow':
        return tab_container('Cash Flow', html.Div([
            html.Div([
                dcc.Graph(id='cash-flow-graph',
                    figure = {'data': [go.Table(
                                        columnwidth = [1.5,1,1,1,1,1,1,1,1,1,1,1,1],
                                        header = dict(values=header_values_string, align = ['center'], fill = dict(color = 'rgba(144,166,209,0.7)'), line = dict(color = 'white')),
                                        cells = dict(values=df_cf.T.values.tolist()[1:], align = ['left', 'center'], fill=dict(color = cf_row_colors), line = dict(color = 'white'))
                                        )
                                    ],
                            'layout' : go.Layout(height=500, margin=dict(t=30))
                    }
                )
            ]),
            html.Div([
                dcc.Graph(id='monthly-cashflow',
                    figure = {'data':[go.Bar(
                                x=header_values_string[1:],
                                y=df_cf.sum()[-12:],
                                name='Monthly Cashflow',
                                marker=dict(color='rgb(230,115,0)'),
                                orientation= 'v'
                                )
                            ],
                            'layout': go.Layout(
                                title = 'Monthly Cashflow',
                                yaxis = {'automargin': True},
                                hovermode= 'closest'
                            )
                        }
                )
            ])  
        ]))
    elif tab == 'price-history':
        return tab_container('Price History', html.Div([
            html.Div([
                dcc.Dropdown(
                    id='my_bond_picker',
                    options= options_hp,
                    multi=True
            )], style={'display':'inline-block','verticalAlign':'top','width':'50%'}),
            html.Div([
                dcc.RadioItems(
                    id='chart_picker',
                    options= [
                        {'label': 'Price', 'value': 'Price'},
                        {'label': 'Return', 'value': 'Return'}
                    ],
                    value= 'Price'
            )], style={'display':'inline-block','verticalAlign':'top', 'width':10}),
            html.Div([
                html.Button(id='submit-button',
                    n_clicks=0,
                    children = 'Submit',
                    style={'fontsize':24,'marginLeft':'30px'}
                )],style={'display':'inline-block','verticalAlign':'top'}),
            html.Div([
                dcc.Graph(id='price_history_graph',
                    
                    figure={
                        'data':hp_traces,
                        'layout':go.Layout(title="Historical Price", height=700)
                    }
                )
            ])
        ]))
    elif tab == 'detailed-view':
        return tab_container('Detailed View', html.Div([
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in ['ISSUER','COUPON','MATURITY','ADJ','COST','PX','CHANGE','TOTAL','RTG','GROUP','COUNTRY']],
                data=df.to_dict("rows"),
                style_header={
                    'fontWeight': 'bold',
                    'fontSize': 18,
                    'vertical-align': 'middle',
                    'color': 'rgb(74,74,74)',
                    'backgroundColor': 'rgba(144,166,209,0.7)'
                },
                style_cell={'textAlign': 'center', 'font-family': 'Open Sans'},
                style_as_list_view=True,
                style_cell_conditional=[{
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgba(47,84,118,0.075)'
                }],
                sorting=True
            )
        ]))
    

#Callback to Render graphs for Risk Exposures

@app.callback(Output('main-graph', 'figure'),
              [Input('graph-picker', 'value')])
def update_figure(selected_graph):
  
    if selected_graph == 'RATING':
        rating_sort_list = list(i for i in Rating_String if i in df['RATING'].unique())
        return {
            'data':[go.Bar(
                x=df.groupby(selected_graph).sum()['ADJ'].sort_values(ascending=False).index,
                y=df.groupby(selected_graph).sum()['ADJ'].sort_values(ascending=False),
                marker=dict(color='rgb(230,115,0)')
                )
            ],
            'layout': go.Layout(
                        autosize = True,
                        title = selected_graph.capitalize() +' Exposure',
                        xaxis= dict(categoryorder = "array", categoryarray = rating_sort_list)                    
                    )
        }
    else:
        return {
            'data':[go.Bar(
                x=df.groupby(selected_graph).sum()['ADJ'].sort_values(ascending=False).index,
                y=df.groupby(selected_graph).sum()['ADJ'].sort_values(ascending=False),
                marker=dict(color='rgb(230,115,0)')
                )
            ],
            'layout': go.Layout(
                        autosize = True,
                        title = selected_graph.capitalize() +' Exposure'                    
                    )
        }

#Callback for setting values on second dropdown to filter Total Return Graph

@app.callback(
    Output('value_filter', 'options'),
    [Input('column_filter', 'value')])
def set_values_options(column):
    return [{'label': i, 'value': i} for i in df[column].unique()]

#Callback to update Total Return Graph based on the column and value dropdowns

@app.callback(
    Output('total_return_graph','figure'),
    [Input('filter-button','n_clicks')],
    [State('column_filter','value'),
    State('value_filter','value')])
def updated_total_return_graph(n_clicks,column,value):
    if column != None and value != None:
        filtered_df = df[df[column]==value]
        height_value = 0
        if len(filtered_df.index) == 1: 
            height_value = 300
        elif len(filtered_df.index) > 1 and len(filtered_df.index) <= 4:
            height_value = 200*len(filtered_df.index)
        else: 
            height_value = 130*len(filtered_df.index)

        fig = {'data':[go.Bar(
                                y=filtered_df['DESCRIPTION'],
                                x=filtered_df['CHANGE']*100,
                                name='<b>Price Change</b>',
                                marker=dict(color='rgb(0,128,85)'),
                                orientation= 'h',
                                width= 0.25
                                ),
                            go.Bar(
                                y=filtered_df['DESCRIPTION'],
                                x=filtered_df['CARRY']*100,
                                name='<b>Carry</b>',
                                marker=dict(color='rgb(0,51,102)'),
                                orientation= 'h',
                                width= 0.25
                                ),
                            go.Bar(
                                y=filtered_df['DESCRIPTION'],
                                x=filtered_df['TOTAL_RETURN'],
                                name='<b>Total Return</b>',
                                marker=dict(color='rgb(93,173,236)'),
                                orientation= 'h',
                                width= 0.25
                                )
                            ],
                            'layout': go.Layout(
                                title = value +' Total Return Components',
                                yaxis = {'automargin': True, 'visible': True, 'showgrid': True, 'gridcolor':'rgb(179,170,170)'},
                                xaxis = dict(tickfont = dict(size= 11)),
                                hovermode= 'closest',
                                bargap= 0,
                                height= height_value
                            )
                        }
        return fig


#Callback to Render graphs for Price History

@app.callback(
    Output('price_history_graph','figure'),
    [Input('submit-button','n_clicks')],
    [State('my_bond_picker','value'),
    State('chart_picker','value')])
def update_hp_chart(n_clicks,selected_bonds,chart_picker):
    if selected_bonds is None or len(selected_bonds)==0: 
        if chart_picker == 'Price':
            fig={
                    'data':hp_traces,
                    'layout':go.Layout(title="Historical Price", height=700)
                }
            return fig

        elif chart_picker == 'Return':
            fig={
                    'data':rets_traces,
                    'layout':go.Layout(title="Historical Price", height=700)
                }
            return fig
    elif len(selected_bonds) >= 1:
        traces=[]
        if chart_picker == 'Price':
            for bond in selected_bonds:
                traces.append({'x':df_hp['DATE'],'y':df_hp[bond],'name':bond})
            fig={
                'data':traces,
                'layout':{'title':'Historical Price'}
                }
            return fig
        elif chart_picker == 'Return':
            for bond in selected_bonds:
                traces.append({'x':rets['DATE'],'y':rets[bond],'name':bond})
            fig={
                'data':traces,
                'layout':{'title':'Historical Price'}
                }
            return fig


    

if __name__ == '__main__':
    app.run_server()






