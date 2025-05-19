import pandas as pd

file_path = 'DB/2324List.csv'
df = pd.read_csv(file_path)

df['년'] = df['년'].astype(str).str.replace('FY', '', regex=False)
df['월'] = df['월'].astype(str).str.zfill(2)
df['입찰일시'] = df['년'] + '-' + df['월'] + '-01 00:00:00'

columns = ['입찰일시'] + [col for col in df.columns if col != '입찰일시']
df = df[columns]

df.drop(columns=['년', '월'], inplace=True)

df.to_csv(file_path, index=False)