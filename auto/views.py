import datetime
from urllib.parse import quote

import sys

from chinese_calendar import is_workday, is_holiday
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect
from yunpian_python_sdk.model import constant as yc
from yunpian_python_sdk.ypclient import YunpianClient

import xlrd
from django.db.models import Q
from SMSBlessing_web import settings
from django.shortcuts import render

# Create your views here.
from auto.models import EmployeeInfo, Birthlist, Divisionlist, UploadHistory, SMSLog
from resource_python.constants import siling, birth



def _create_data(path):

    def _one_or_none(obj):
        if obj == '':
            return None
        else:
            return obj

    EmployeeInfo.objects.all().delete()
    workbook = xlrd.open_workbook(path)
    cols = ['code', 'name', 'enter_date', 'birth_date', 'tel', ]
    empinfo_list = []
    for count, one in enumerate(workbook.sheet_names()):
        for i in range(1, workbook.sheet_by_name(one).nrows):
            if workbook.sheet_by_name(one).ncols > 7:
                print('错误')
                break
            empinfo = EmployeeInfo()
            # print(i)
            for j, col in enumerate(cols):
                # print(j)
                if col == 'enter_date' or col == 'birth_date':
                    if _one_or_none(workbook.sheet_by_name(one).cell_value(i, j)):
                        setattr(empinfo, col,
                                datetime.datetime.strptime(workbook.sheet_by_name(one).cell_value(i, j), '%Y-%m-%d'))
                    else:
                        setattr(empinfo, col, None)
                elif col == 'code' or col == 'tel':
                    # 0开始的工号处理
                    if len(str(int(_one_or_none(workbook.sheet_by_name(one).cell_value(i, j))))) < 10 and col == 'code':
                        setattr(empinfo, col,
                                '0' + str(int(_one_or_none(workbook.sheet_by_name(one).cell_value(i, j)))))
                    else:
                        setattr(empinfo, col, int(_one_or_none(workbook.sheet_by_name(one).cell_value(i, j))))
                elif col == 'name':
                    setattr(empinfo, col, _one_or_none(workbook.sheet_by_name(one).cell_value(i, j)))
            # print(empinfo.__dict__)
            # print(type(empinfo))
            # 设置主键
            empinfo.pk = i
            empinfo.leave_status = False
            empinfo.leave_send_status = False
            empinfo_list.append(empinfo)
        EmployeeInfo.objects.bulk_create(empinfo_list)
    pass

def _data_delete():
    Birthlist.objects.all().delete()
    Divisionlist.objects.all().delete()
    pass

def _get_sms_template():
    """
    获取模板,因list第一个是从0开始，所有空置第一个元素
    所有的模板均是文本格式，参数有2个 Name 、 Day
    :return:
    """
    # return siling, brith
    global siling_templates
    global birth_templates
    siling_templates = siling
    birth_templates = birth

# email 模板使用 blessing.html render 进行渲染

def update_empinfo(path):
    _data_delete()
    _create_data(path)
    # _transform(days=1)

# 短信和邮件共享
def _transform(time, days):
    """
    在 EmployeeInfo 根据起始日期、距起始日期天数，获取起始日期之后 days 天的人员名单(生日、司龄)
    可以对这个过程抽象，但是意义不大
    :param days:距起始日期天数
    :param time:开始时间
    :return:
    """
    # 删除上次获取的数据
    _data_delete()
    time = time + datetime.timedelta(days=days)
    question = Q(birth_date__endswith=time.strftime('-%m-%d'))
    if time.strftime('-%m-%d') == '-02-28':
        try:
            datetime.date(time.year, 2, 29)
        except ValueError:
            question = Q(birth_date__endswith=time.strftime('-02-29')) | Q(
                birth_date__endswith=time.strftime('-%m-%d'))
    result = EmployeeInfo.objects.filter(question)
    # result=stone.query(EmployeeInfo).filter(text("id=(':value')")).params(value=224)
    # print(result.one())
    birth_list = []
    for one in result:
        # print(one)
        birth = Birthlist()
        # 处理后缀数值
        try:
            int(one.name[len(one.name) - 1])
            birth.name = one.name[:len(one.name) - 1]
        except ValueError:
            birth.name = one.name
        birth.code = one.code
        birth.birth_date = one.birth_date
        birth.tel = one.tel
        birth.plan_date = time
        birth.flag_num = birth.plan_date.month
        birth.status = False
        birth.send_time = time.now()
        birth.emp_pk = one
        # 可能会出现重复值
        birth_list.append(birth)
    Birthlist.objects.bulk_create(birth_list)
    # print('_________')
    question = Q(enter_date__endswith=time.strftime('-%m-%d'))
    if time.strftime('-%m-%d') == '-02-28':
        try:
            datetime.date(time.year, 2, 29)
        except ValueError:
            question = Q(enter_date__endswith=time.strftime('-02-29')) | Q(
                enter_date__endswith=time.strftime('-%m-%d'))
    result = EmployeeInfo.objects.filter(question)
    division_list = []
    for one in result:
        # print(one)
        division = Divisionlist()
        # 处理后缀数值
        try:
            int(one.name[len(one.name) - 1])
            division.name = one.name[:len(one.name) - 1]
        except ValueError:
            division.name = one.name
        division.code = one.code
        division.reality_enter_date = one.enter_date
        division.tel = one.tel
        division.plan_date = time
        division.flag_num = division.plan_date.year - one.enter_date.year
        division.status = False
        division.send_time = time.now()
        division.emp_pk = one
        division_list.append(division)
    Divisionlist.objects.bulk_create(division_list)
    pass

# 短信和邮件共享
def _get_data(today, days):
    # 相对于【邮件发送】，【短信发送】只需要考虑当天发送，具体实现方式在 【_sms_send】 中体现
    # self.logger.debug("开始获取短信数据")
    table_dict = {'birth_result': Birthlist, 'siling_result': Divisionlist}
    # 使用list 相加的功能，形成不嵌套的list
    global birth_result
    global siling_result
    birth_result = []
    siling_result = []
    result_dict = {'birth_result': birth_result, 'siling_result': siling_result}
    for key, value in table_dict.items():
        for i in range(days + 1):
            result = value.objects.filter(Q(plan_date=today + datetime.timedelta(days=i)) & Q(status=False)).all()
            if len(result):
                result_dict[key] += result
    # self.logger.debug("短信数据获取完成")
    pass

def _sms_send_quote(array):
    data_str = []
    for one in array:
        data_str.append(quote(one))
    return data_str
    pass

def _sms_send(today):
    """
    根据发送日期，获取数据后填充至模板，并对发送的模板进行编码。
    :param today: 发送日期
    :return:
    """
    # self.logger.debug("开始发送短信")
    _get_data(today=today, days=1)
    tel = []
    data_str = []
    sms_result_dict = {'siling': siling_result, 'brith': birth_result}
    sms_templates_dict = {'siling': siling_templates, 'brith': birth_templates}
    for key, value in sms_result_dict.items():
        if len(value):
            for one in value:
                tel.append(one.tel)
                if key == 'siling':
                    data_str.append(sms_templates_dict[key][str(one.flag_num)].format(
                        Name=one.name, Day=today.strftime(
                            "%Y{year}%m{month}%d{day}").format(year='年', month='月', day='日')))
                elif key == 'brith':
                    data_str.append(
                        sms_templates_dict[key][one.plan_date.strftime("%Y-%m")].format(Name=one.name,
                        Day=today.strftime("%Y{year}%m{month}%d{day}").format(year='年', month='月', day='日')))
    # pprint(data_str)
    if len(tel) and len(data_str):
        param = {yc.MOBILE: ','.join(tel), yc.TEXT: (','.join(_sms_send_quote(data_str)))}
        # r = self.clnt.sms().multi_send(param)
        clnt.sms().multi_send(param)
    # self.logger.debug("短信发送完成")
    pass

def _sms_log():
    sms_type = {'birth':birth_result, 'siling':siling_result, }
    sms_log_list = []
    for key, value in sms_type.items():
        for one in value:
            sms_log = SMSLog()
            sms_log.name = one.name
            sms_log.code = one.code
            sms_log.enter_date = one.emp_pk.enter_date
            sms_log.birth_date = one.emp_pk.birth_date
            sms_log.tel = one.tel
            sms_log.leave_status = one.emp_pk.leave_status
            sms_log.sms_type = key
            sms_log.flag_num = one.flag_num
            sms_log.log_date = one.send_time.now()
            sms_log_list.append(sms_log)
    SMSLog.objects.bulk_create(sms_log_list)

    pass

# 发送短信
def sms_send(time, days=0):
    _transform(time, days)
    _get_data(time.date(), days)
    _sms_log()
    #  测试不发送短信
    _sms_send(time)

# 发送邮件
def email(time, days):
    _transform(time, days)
    _get_data(time.date(), days)
    from_email = settings.DEFAULT_FROM_EMAIL
    content = render(None, template_name='auto/blessing.html',
                  context={'birth_result':birth_result, 'siling_result':siling_result, }).getvalue().decode("utf-8")
    msg = EmailMultiAlternatives("祝福短信{today}".format(today=time.date()), content, from_email,
                                 settings.conf.get(section='email', option='to_addr').split(','))
    msg.content_subtype = "html"
    # 添加附件（可选）
    # msg.attach_file('./xxx.pdf')
    # 发送
    # print(birth_result, siling_result)
    # print(content)
    msg.send()

def _workexec(today):
    """
    功能 ： 判断明天是不是工作日
    :param today:开始日期
    :return: 0 为工作日， ！0 为距离下个工作日还有几天
    """
    # march_first = datetime.date.today()
    # i=0
    days = 0
    # march_first = today
    while True:
        # print(is_workday(march_first))  # False
        # print(is_holiday(march_first))  # True
        march_first = today + datetime.timedelta(days=days)
        if is_workday(march_first):
            break
        days = days + 1
    return days

def auto_job():
    time = datetime.datetime.today()
    days = _workexec(time)
    # 工作日发送邮件
    if days == 0:
        tomorrow_days = _workexec(time + datetime.timedelta(days=1))
        # 如果明天是节假日，则按节假日的天数处理
        if tomorrow_days != 0:
            email(time, tomorrow_days)
        # 否则就按照工作日发送
        else:
            email(time, days)
    sms_send(time)

def update_empinfo_init():
    try:
        path_finally_time_result = UploadHistory.objects.order_by('-upload_time').all()[0]
        # 转换为字符
        update_empinfo(str(path_finally_time_result.path_name))
    except IndexError:
        print("最近一次人员信息初始化失败")
        raise UserWarning("人员信息初始化失败")
# 资源预加载

# 加载 云片
clnt = YunpianClient(settings.conf.get(section='SMSServer', option='apikey'))
# 获取短信模板，邮件模板用 Django 的 render 去读取模板
# 启动时更新人员信息
try:
    _get_sms_template()
    update_empinfo_init()
except UserWarning:
    update_empinfo(sys.path[0] + '/auto/temp/祝福短信人员2018-02-28.xls')