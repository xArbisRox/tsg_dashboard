from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from FileMerger import FileMerger
from WinsLosses import StatsGetter

df = FileMerger().merge_dfs()


def get_overall_goals(_df):
    overall_sort_order = dict()
    grouped_df = _df.groupby('Name', as_index=False)['Tore'].sum()
    grouped_df.sort_values('Tore', ascending=False, inplace=True)

    for num, name in enumerate(grouped_df['Name']):
        overall_sort_order[name] = num

    _df['goal_sorter'] = _df['Name'].map(overall_sort_order)
    _df.sort_values(['goal_sorter', 'date'], ascending=[True, True],
                    inplace=True)
    _df['total_goals'] = [0] * len(_df.index)

    goal_df = _df.groupby('Name')['Tore'].sum()

    def _calc_overall_goals(name):
        return goal_df[name]

    for idx, series in _df.iterrows():
        _df.loc[idx, 'total_goals'] = _calc_overall_goals(series['Name'])

    return _df


wins_df = StatsGetter(file_name='Tore und Siege kicken.xlsx',
                      list_of_sheets=['October-2022', 'November-2022'],
                      list_of_columns=[*['A, B, E'], *['A, B, E, AR']],
                      list_of_endrows=[11, 8]).output

app = Dash(__name__)


title_style = {'title_font_family': 'Simplifica, Arial, sans-serif',
               'title_font_size': 25
               }

div_style = {'backgroundColor': '#0000FF',
             'color': '#FFFFFF',
             'textAlign': 'center',
             'fontFamily': 'Arial, Helvetica, sans-serif'
             }

plot_style = {'grey': '#DCDCDC',
              'darkgrey': '#707070',
              'blue': '#0000FF',
              'white': '#FFFFFF'
              }


def update_layout(fig):
    fig.update_layout(
        plot_bgcolor=plot_style['darkgrey'],
        paper_bgcolor=plot_style['darkgrey'],
        font_color=plot_style['white'],
        **title_style)


app.layout = html.Div(style=div_style,
                      children=[
                        html.Div(style={
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'space-between'
                        },
                            children=[
                            html.Img(src=r'static/tsg_logo.jpg', alt='image',
                                     style={'width': '220px',
                                            'height': 'auto',
                                            'visibility': 'hidden'
                                            }
                                     ),
                            html.H1('TSG Muenster 1b'),
                            html.Img(src=r'static/tsg_logo.jpg', alt='image',
                                     style={'width': '220px',
                                            'height': 'auto',
                                            }
                                     ),
                            ]
                        ),
                        html.Div('Fußball Statistik',
                                 style={'fontStyle': 'italic'}),
                        html.Br(),
                        html.Div([html.P('Please select your months of '
                                         'interest!'),
                                  html.P('\'Overall\' represents the '
                                         'complete available timeline',
                                         style={'textAlign': 'center'}),
                                  dcc.Dropdown(id='month_selector',
                                               options=['Overall'] + wins_df[
                                                  'month'].unique().tolist(),
                                               value='Overall',
                                               multi=True,
                                               style={'color': div_style[
                                                  'backgroundColor']
                                                     }
                                               )
                                  ]
                                 ),
                        dcc.Graph('soccer_bar'),
                        html.Br(),
                        dcc.Graph('sub_pie_charts')
                      ]
                      )


def _slice_months(_df, selected_dates):
    sliced_df = _df.copy()
    if 'Overall' in selected_dates:
        sliced_df = sliced_df
    else:
        sliced_df = sliced_df.loc[sliced_df['month'].isin(selected_dates), :]
    return sliced_df


@app.callback(
    Output('soccer_bar', 'figure'),
    Input('month_selector', 'value')
)
def update_bar_charts(selected_dates):
    bar_df = _slice_months(df, selected_dates)
    bar_df = get_overall_goals(bar_df)
    fig_goals = px.bar(bar_df, x='Name', y='Tore', color='month',
                       barmode='stack', text_auto=True,
                       hover_data=['Name', 'month', 'Tore', 'total_goals'],
                       title=f'Goals {selected_dates}',
                       labels={'month': 'Monat',
                               'total_goals': 'Gesamttore'},
                       )
    update_layout(fig_goals)
    return fig_goals


@app.callback(
    Output('sub_pie_charts', 'figure'),
    Input('month_selector', 'value')
)
def update_pie_charts(selected_dates):
    pie_df = _slice_months(wins_df, selected_dates)

    def equal_players_selector():
        return not_na['Gleichzahl'] == 1

    overall_games = pie_df.shape[0]
    na_games = len(pie_df['Gleichzahl'].isnull())
    not_na = pie_df.loc[~pie_df['Gleichzahl'].isnull(), :]
    equal_df = not_na.loc[equal_players_selector(), :]
    unequal_df = not_na.loc[~equal_players_selector(), :]

    sub_pie_fig = make_subplots(rows=1, cols=3, subplot_titles=
                                ['All Games', 'Equal Players', 'Not Equal'],
                                specs=[[{'type': 'domain'}, {'type': 'domain'},
                                        {'type': 'domain'}
                                        ]]
                                )

    sub_pie_fig.add_trace(go.Pie(values=pie_df['Games'],
                                 labels=pie_df['Winner'],
                                 ),
                          row=1, col=1
                          )

    sub_pie_fig.add_trace(go.Pie(values=equal_df['Games'],
                                 labels=equal_df['Winner']),
                          row=1, col=2
                          )

    sub_pie_fig.add_trace(go.Pie(values=unequal_df['Games'],
                                 labels=unequal_df['Winner']),
                          row=1, col=3
                          )

    update_layout(sub_pie_fig)
    sub_pie_fig.update_layout(title_text=f'Win and Loss Distribution, '
                                         f'Dates: {selected_dates}')

    return sub_pie_fig

    # fig_wins = px.pie(pie_df, values='Games', names='Winner', title=
    #                   f'Overall Win and Loss Distribution, '
    #                   f'Dates: {selected_dates}',
    #                   width=800, height=400
    #                   )
    # equal_df = pie_df.loc[pie_df['Gleichzahl'] == 1, :]
    # fig_equals = px.pie(equal_df, values='Games', names='Winner', title=
    #                     f'Equal Players Win and Loss Distribution Equal '
    #                     f'Players, Dates: {selected_dates}',
    #                     width=800, height=400)
    # update_layout(fig_wins)
    # return fig_wins, fig_equals





if __name__ == '__main__':
    app.run_server(debug=True)