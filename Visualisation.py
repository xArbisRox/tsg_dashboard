from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
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


def backfill_missing_months(_df: pd.DataFrame) -> pd.DataFrame:
    """
    Synthetically backfill months where certain players did not participate
    with zero values, so all included players have the same amount of
    entries within the DataFrame and the auto-sorting of stacked BarChart
    works.
    :param _df: DataFrame after _slice_months function
    :return: DataFrame with same amount of rows per player
    """

    out_df = _df.copy()

    months = _df['month'].unique()
    players = _df['Name'].unique()

    cols = _df.columns

    for player in players:
        played_months = _df.loc[_df['Name'] == player, 'month']
        if len(played_months) != len(months):
            missed_months = [missed for missed in months
                             if missed not in played_months.values]
            for missed_month in missed_months:
                fill_df = pd.DataFrame(np.nan, index=[0], columns=cols)
                fill_df[['Name', 'month', 'Tore']] = \
                    player, missed_month, 0
                out_df = pd.concat([out_df, fill_df], axis=0)

    return out_df


wins_df = StatsGetter(file_name='Tore und Siege kicken.xlsx',
                      list_of_sheets=['October-2022', 'November-2022',
                                      'December-2022'],
                      list_of_columns=[*['A, B, E, AF'], *['A, B, E, AR, AF'],
                                       *['A, B, E, AR, AF']],
                      list_of_endrows=[11, 8, 9]).output

app = Dash(__name__)


title_style = {'title_font_family': 'Simplifica, Arial, sans-serif',
               'title_font_size': 25
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


app.layout = html.Div(className='background-blue',
                      children=[
                        html.Div(className='flexbox flex-center '
                                           'flex-space-between',
                                 children=[
                            html.Img(src=r'assets/images/tsg_logo.jpg',
                                     alt='image',
                                     style={'width': '220px',
                                            'height': 'auto',
                                            'visibility': 'hidden'
                                            }
                                     ),
                            html.H1('TSG Muenster 1b',
                                    className='white-font center-text'),
                            html.Img(src=r'assets/images/tsg_logo.jpg', alt='image',
                                     style={'width': '220px',
                                            'height': 'auto',
                                            }
                                     ),
                            ]
                        ),
                        html.Div('Fußball Statistik',
                                 className='white-font center-text italic-text',
                                 style={'fontStyle': 'italic'}),
                        html.Br(),
                        html.Div([html.P('Please select your months of '
                                         'interest!',
                                         className='white-font center-text'),
                                  html.P('\'Overall\' represents the '
                                         'complete available timeline',
                                         className='white-font center-text'),
                                  dcc.Dropdown(id='month_selector',
                                               className='center-text',
                                               options=['Overall'] + wins_df[
                                                  'month'].unique().tolist(),
                                               value='Overall',
                                               multi=True
                                               ),
                                  ]
                                 ),
                        dcc.Graph('soccer_bar'),
                        html.Br(),
                        dcc.RadioItems(id='robin_selector',
                                       className='white-font center-text',
                                       options=[
                                          'Inklusive Robin', 'Exklusive Robin'
                                       ],
                                       value='Inklusive Robin'),
                        dcc.Graph('sub_pie_charts'),

                        html.Div(id='robin_section')
                      ]
                      )


def _slice_months(_df, selected_dates):
    sliced_df = _df.copy()
    if 'Overall' in selected_dates:
        sliced_df = sliced_df
    else:
        sliced_df = sliced_df.loc[sliced_df['month'].isin(selected_dates), :]
    return sliced_df


def separate_robin(_df):
    """
    Split the date sliced input dataframe in two dataframes.
    One represents only the dates where Robin was not there.
    The other represents solely Robin's stats when he was participating.
    :param _df:
    :return:
    """
    no_robin_df = _df.loc[_df['Robin'].isnull(), :]
    robin_df = _df.loc[~_df['Robin'].isnull(), :]

    return no_robin_df, robin_df


@app.callback(
    Output('soccer_bar', 'figure'),
    Input('month_selector', 'value')
)
def update_bar_charts(selected_dates):
    bar_df = _slice_months(df, selected_dates)
    bar_df = backfill_missing_months(bar_df)
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
    Output('robin_section', 'style'),
    Output('robin_section', 'children'),
    Input('month_selector', 'value'),
    Input('robin_selector', 'value')
)
def update_pie_charts(selected_dates, robin):
    pie_df = _slice_months(wins_df, selected_dates)
    no_robin_df, robin_df = separate_robin(pie_df)
    robin_pie = go.Figure(data=go.Pie(values=[1, 2, 3], labels=['1', '2',
                                                                '3']
                                      )
                          )

    robin_section_style = {'display': 'none'}
    robin_section_children = []

    def set_legend_colors(series):
        legend_colors = {'Alt': '#636EFA', 'Jung': '#EF553B',
                         'Unentschieden': '#00CC96'}

        return series.map(legend_colors)

    def equal_players_selector():
        return not_na['Gleichzahl'] == 1

    def without_robin() -> bool:
        if robin == 'Exklusive Robin':
            return True
        return False

    if without_robin():
        pie_df = no_robin_df

        robin_section_style = {'display': 'flex',
                               'alignItems': 'center',
                               'justifyContent': 'space-between',
                               # 'maxWidth': '1200px',
                               # 'width': '100%',
                               'maxHeight': '450px',
                               'height': '100%'
                               }
        robin_fig = go.Figure(data=go.Pie(values=robin_df['Games'],
                                          labels=robin_df['Winner'],
                                          marker_colors=set_legend_colors(
                                              robin_df['Winner'])),
                              layout=go.Layout(title=go.layout.Title(
                                  text="Robin's Statistik"
                                        )
                                    )
                              )
        update_layout(robin_fig)

        robin_happy = html.Img(id='robin_happy',
                               className='flex-robin-images',
                               src=r'assets/images/robin_happy.jpeg',
                               alt='image'
                               )

        robin_pie = dcc.Graph(id='robin_pie',
                              className='flex-robin-graph',
                              figure=robin_fig
                              )

        robin_sick = html.Img(id='robin_sick',
                              className='flex-robin-images',
                              src=r'assets/images/robin_sick.jpeg', alt='image'
                              )

        robin_section_children.append(robin_happy)
        robin_section_children.append(robin_pie)
        robin_section_children.append(robin_sick)

    overall_games = pie_df.shape[0]
    na_games = len(pie_df['Gleichzahl'].isnull())
    not_na = pie_df.loc[~pie_df['Gleichzahl'].isnull(), :]
    equal_df = not_na.loc[equal_players_selector(), :]
    unequal_df = not_na.loc[~equal_players_selector(), :]

    sub_pie_fig = make_subplots(rows=1, cols=3, subplot_titles=
                                ['Alle Spiele', 'Gleichzahl', 'Alt Überzahl'],
                                specs=[[{'type': 'domain'}, {'type': 'domain'},
                                        {'type': 'domain'}
                                        ]]
                                )

    sub_pie_fig.add_trace(go.Pie(values=pie_df['Games'],
                                 labels=pie_df['Winner'],
                                 marker_colors=set_legend_colors(pie_df[
                                                                     'Winner'])
                                 ),
                          row=1, col=1
                          )

    sub_pie_fig.add_trace(go.Pie(values=equal_df['Games'],
                                 labels=equal_df['Winner'],
                                 marker_colors=set_legend_colors(equal_df[
                                                                     'Winner'])
                                 ),
                          row=1, col=2
                          )

    sub_pie_fig.add_trace(go.Pie(values=unequal_df['Games'],
                                 labels=unequal_df['Winner'],
                                 marker_colors=set_legend_colors(unequal_df[
                                                                     'Winner'])
                                 ),
                          row=1, col=3
                          )

    update_layout(sub_pie_fig)
    sub_pie_fig.update_layout(title_text=f'Win and Loss Distribution, '
                                         f'Dates: {selected_dates}')

    return sub_pie_fig, robin_section_style, robin_section_children

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