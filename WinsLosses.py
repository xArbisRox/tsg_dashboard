import os
import pandas as pd
from dataclasses import dataclass
from FileMerger import FileMerger


@dataclass
class StatsGetter(FileMerger):
    """
    Class to draw Wins and Losses for Alt vs. Jung Fußball Stats.
    Access the desired output via class.output getter.
    """
    file: pd.ExcelFile
    _dict_of_dfs: dict
    _dict_of_dfs_with_months: dict

    def __init__(self, file_name, list_of_sheets, list_of_columns,
                 list_of_endrows):
        self.file = pd.ExcelFile(os.path.join(self.input_path, file_name))
        self._dict_of_dfs = {sheet: pd.read_excel(self.file,
                                                  sheet_name=sheet,
                                                  usecols=cols,
                                                  nrows=end_row) for
                                 sheet, cols, end_row in zip(
                list_of_sheets, list_of_columns, list_of_endrows)}
        self._dict_of_dfs_with_months = dict()
        self.include_month_col()
        self._output = self.clean_data()

    def include_month_col(self):
        for key, df in self._dict_of_dfs.items():
            df['month'] = key
            AltCounter, JungCounter, Einheit = 0, 0, 0
            df['AltCounter'], df['JungCounter'], df['Einheit'] =\
                [AltCounter] * len(df.index),\
                [JungCounter] * len(df.index),\
                [Einheit] * len(df.index)

            for idx, series in df.iterrows():
                if series['Alt'] == 1:
                    AltCounter += 1
                    series['AltCounter'] = AltCounter
                    series['JungCounter'] = JungCounter
                elif series['Alt'] == -1:
                    JungCounter += 1
                    series['JungCounter'] = JungCounter
                    series['AltCounter'] = AltCounter
                else:
                    series['JungCounter'] = JungCounter
                    series['AltCounter'] = AltCounter
                Einheit += 1
                series['Einheit'] = Einheit
                df.loc[idx, :] = series
            self._dict_of_dfs_with_months[key] = df

    def concat_dfs(self) -> pd.DataFrame:
        out_df = pd.DataFrame(dict())
        for idx, items in enumerate(self._dict_of_dfs_with_months.items()):
            if idx == 0:
                out_df = items[1]
            else:
                out_df = pd.concat([out_df, items[1]], axis=0,
                                   ignore_index=True)
        return out_df

    def clean_data(self):
        _df = self.concat_dfs()
        _df['Games'] = _df.apply(lambda x: 1, axis=1)
        _df['Winner'] = _df.apply(lambda x: 'Alt' if x['Alt'] == 1 else (
            'Jung' if x['Alt'] == -1 else 'Unentschieden'), axis=1)
        return _df

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, value):
        self._output = value


if __name__ == '__main__':
    obj = StatsGetter(file_name='Tore und Siege kicken.xlsx',
                      list_of_sheets=['October-2022', 'November-2022'],
                      list_of_columns=[*['A, B, E'], *['A, B, E, AR']],
                      list_of_endrows=[11, 8])
    df = obj.clean_data()

    print('test')

