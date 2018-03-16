import glob

import sys

import os

import datetime

import re

import win32api

import win32con
import xlrd
import xlwt


def read_excel(excel_file, ws, j):
    workbook = xlrd.open_workbook(filename=excel_file)
    for sheet, one in enumerate(workbook.sheet_names()):
        temp = 3
        if j == 0:
            ws.write(0, 0, '工号')
            ws.write(0, 1, '姓名')
            ws.write(0, 2, '虚拟入职日期')
            ws.write(0, 3, '生日日期')
            ws.write(0, 4, '电话号码')
            j += 1
        print(one)
        if '离职' not in one and '司龄补回表' not in one:
            for i in range(temp, workbook.sheet_by_name(one).nrows):
                sheet = workbook.sheet_by_name(one)
                try:
                    if workbook.sheet_by_name(one).cell_value(i, 8) != "":
                        excel_write(ws, j, 0, sheet, i, 8 - 1, 'code')
                        excel_write(ws, j, 1, sheet, i, 9 - 1, 'name')
                        excel_write(ws, j, 2, sheet, i, 53 - 1, 'date')
                        excel_write(ws, j, 3, sheet, i, 20 - 1, 'date')
                        excel_write(ws, j, 4, sheet, i, 22 - 1, 'tel')
                        j += 1
                except UserWarning as err:
                    # print(err)
                    # print(err.args)
                    win32api.MessageBox(0, '{type},{excel_file} 中{sheet}的{row}行{col}列数据有问题，请检查'.format(
                        type=err.args[0], excel_file=os.path.split(excel_file)[1], sheet=one, row=err.args[1], col=err.args[2]
                    ), "祝福短信源文件生成", win32con.MB_OK)
                    exit(0)
                    pass
    return j

def availability_write(value, type):
    type_dict = {'code':r'^[\d]?[\d]{9}$', 'tel':r'^[\d]{11}$', 'date':'', 'name':str}
    for k, v in type_dict.items():
        if k == type:
            if k == 'date':
                try:
                    return datetime.datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    return None
            if k == 'name':
                return isinstance(value, v)
            if k == 'code' or k == 'tel':
                return re.match(v, str(int(value)))
    print("没有此类型")
    raise UserWarning("没有此类型")

def excel_write(write_ws_ins, row, col, read_sheet_ins, r, c, type):
    if availability_write(read_sheet_ins.cell_value(r, c), type) == None:
        # print("数据错误 {r},{c}, {data}".format(r=r + 1, c=c + 1, data=read_sheet_ins.cell_value(r, c)))
        raise UserWarning("数据错误", r + 1, c + 1, read_sheet_ins.cell_value(r, c))
    write_ws_ins.write(row, col, read_sheet_ins.cell_value(r, c))

win32api.MessageBox(0, '请将所有花名册放到当前文件夹', "祝福短信源文件生成", win32con.MB_OK)
# 防止因为打包为 exe 文件，路径定位错误
path = sys.path[0]
if os.path.isfile(sys.path[0]):
    path = os.path.dirname(sys.path[0])
files = glob.glob(path + os.sep + '*.xlsx')
if len(files) == 0:
    win32api.MessageBox(0, '当前文件夹无任何花名册,正在退出', "祝福短信源文件生成", win32con.MB_OK)
    exit(0)
# print(files)
sheet = xlwt.Workbook()
ws = sheet.add_sheet('人员名单')
j = 0
for file in files:
    print(file)
    j = read_excel(file, ws, j)
sheet.save('祝福短信人员.xls')
