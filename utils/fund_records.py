
from openpyxl import Workbook, load_workbook
import re
from itertools import groupby
import datetime

worbok = load_workbook(f'../finance_data/options.xlsx')
worbok.sheetnames

def plus1(func):
	func = [''.join(list(g)) for k,g in groupby(func, lambda x: x.isdigit())]
	result = []
	for count, i in enumerate(func):
		if count == 0:# 第一个直接加
			result += [i]
			continue
			
		if i.isdigit() and func[count - 1][-1].isalpha() :# 如果为数字检查上一个尾是否为字母，若是则i是单元格位置
			if func[count - 1][-2] != '$': #判断是不是固定单元格
				result += [str(int(i) + 1)]
			else:
				result += [i]
			continue


		result += [i]

	func = ''.join(result)
	return func

def pulldown(row, columns):
	worbok['净值'][f'{columns}{row}'].value = plus1(worbok['净值'][f'{columns}{row-1}'].value)
	worbok['净值'][f'{columns}{row}'].number_format = plus1(worbok['净值'][f'{columns}{row-1}'].value).number_format

# worbok['净值']['C52'].value = 1
str_= len(worbok['净值']["C:C"]) + 1
worbok['净值'][f'A{str_}'].value = worbok['净值'][f'A{str_ - 1}'].value + datetime.timedelta(1)
worbok['净值'][f'A{str_}'].number_format = worbok['净值'][f'A{str_ - 1}'].number_format
worbok['净值'][f'B{str_}'].value = 20000
worbok['净值'][f'D{str_}'].value = 0
worbok['净值'][f'B{str_}'].number_format = worbok['净值'][f'B{str_ - 1}'].number_format


for ix in ['E', 'F' , 'C', 'G']:
	pulldown(str_, ix)

plus1('=B89-B88-$D$89')

worbok['净值'][f'E{str_}'].number_format = '0.00%'
worbok.save(f'../finance_data/options.xlsx') 


