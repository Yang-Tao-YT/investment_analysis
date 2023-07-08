
from openpyxl import Workbook, load_workbook





worbok = load_workbook(f'../finance_data/options.xlsx', data_only=True)

worbok = load_workbook(f'../finance_data/options.xlsx')
worbok.sheetnames
len(worbok['净值']["B:B"])
worbok['净值']['B52'].value = 1
worbok.save(f'../finance_data/options.xlsx') 
for cell_rows in worbok['净值']["B:B"]:
	# for cell_columns in cell_rows:
		print(cell_rows.value)
