import pandas as pd
import numpy as np

DEFINITION_FILE = r"Z:\Shared\WillowstickFiles\Data and Software Documentation\Definitions\Gen9 Data Storage Tables NEW.xlsx"
DEFINITION_SHEETS = ['Gen8 Data Table', 'ROVING', '2021-Data', 'RapidReadNew']
DEFINTION_SHEET_LOCS = {'Gen8 Data Table': (2, 11),
              'ROVING': (1, 10),
              '2021-Data': (2, 10),
              'RapidReadNew': {"SDcard": (1, 27),
                               "Cloud": (4, 10)}
              }
def main():

    excel_file = pd.ExcelFile(DEFINITION_FILE)
    sheets_in_file = excel_file.sheet_names

    cols = {}

    for sheet in sheets_in_file:
        df = pd.read_excel(DEFINITION_FILE, sheet_name=sheet, header=None)
ju
        if sheet == 'RapidReadNew':
            cols["SDcard"] = df.iloc[DEFINTION_SHEET_LOCS[sheet]["SDcard"][1]:, DEFINTION_SHEET_LOCS[sheet]["SDcard"][0]].tolist()
            cols["Cloud"] = df.iloc[DEFINTION_SHEET_LOCS[sheet]["Cloud"][1]:, DEFINTION_SHEET_LOCS[sheet]["Cloud"][0]].tolist()
        else:
            cols[sheet] = df.iloc[DEFINTION_SHEET_LOCS[sheet][1]:, DEFINTION_SHEET_LOCS[sheet][0]].tolist()

def remainder(x, y):

    remains = set(x).difference(set(y))
    N_missing = len(remains)

    return remains, N_missing


if __name__ == "__main__":

    main()