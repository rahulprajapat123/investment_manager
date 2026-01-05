import pandas as pd

df = pd.read_excel(r'reports\C001_portfolio_report.xlsx', sheet_name='Calculations')

indices = [i for i in range(len(df)) if df.iloc[i]['client_id'] == 'client_id']
print('Rows where client_id == "client_id":', indices)
