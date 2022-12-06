import os
import pandas as pd
from datetime import datetime


class FileMerger:
    input_path = os.path.join(os.getcwd(), 'input_data')

    def __init__(self):
        self.datetime = datetime.now().date()
        self.date_str = datetime.strftime(self.datetime, '%Y-%m')
        self.file_list = [x for x in os.listdir(self.input_path) if
                          x.startswith('Kicken') and x.endswith('.xlsx')]
        self.file_paths = [os.path.join(self.input_path, file) for file in
                           self.file_list]

    def read_files(self):
        return [pd.read_excel(x) for x in self.file_paths]

    def include_month_col(self):
        dict_with_months = {}
        dfs = self.read_files()
        for file, df in zip(self.file_list, dfs):
            month_white_space = file.find(' ')
            year_white_space = file.rfind(' ')
            file_type_white_space = file.find('.xlsx')
            month = file[month_white_space+1:year_white_space]
            year = file[year_white_space+1:file_type_white_space]
            month_year = f'{month}-{year}'
            df['date'] = datetime.strptime(month_year, '%B-%Y')
            df['month'] = month_year
            dict_with_months[month] = df
        return dict_with_months

    def merge_dfs(self):
        dfs = self.include_month_col()
        out_df = pd.DataFrame(dict())
        for idx, items in enumerate(dfs.items()):
            if idx == 0:
                out_df = items[1]
            else:
                out_df = pd.concat([out_df, items[1]], axis=0,
                                   ignore_index=True)

        return out_df


if __name__ == '__main__':
    obj = FileMerger()
    df = obj.merge_dfs()


