import datetime
import json
from urllib.parse import quote

import sys

import requests
from chinese_calendar import is_workday
from django.core.mail import EmailMultiAlternatives
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
    time = time + datetime.timedelta(days=days)
    question = Q(birth_date__endswith=time.strftime('-%m-%d'))
    if time.strftime('-%m-%d') == '-02-28':
        try:
            datetime.date(time.year, 2, 29)
        except ValueError:
            question = Q(birth_date__endswith=time.strftime('-02-29')) | Q(
                birth_date__endswith=time.strftime('-%m-%d'))
    result = EmployeeInfo.objects.filter(question).order_by('birth_date')
    birth_list = []
    for index, one in enumerate(result):
        # print(one)
        birth_ins = Birthlist()
        # 处理后缀数值
        try:
            int(one.name[len(one.name) - 1])
            birth_ins.name = one.name[:len(one.name) - 1]
        except ValueError:
            birth_ins.name = one.name
        birth_ins.code = one.code
        birth_ins.birth_date = one.birth_date
        birth_ins.tel = one.tel
        birth_ins.plan_date = time.date()
        birth_ins.flag_num = birth_ins.plan_date.month
        birth_ins.status = False
        birth_ins.send_time = time
        birth_ins.emp_pk = one
        birth_ins.uid = datetime.date.today().strftime('%Y%m%d') + '01' + '01{index:0>4}'.format(index=index)
        # 可能会出现重复值
        birth_list.append(birth_ins)
    Birthlist.objects.bulk_create(birth_list)
    question = Q(enter_date__endswith=time.strftime('-%m-%d'))
    if time.strftime('-%m-%d') == '-02-28':
        try:
            datetime.date(time.year, 2, 29)
        except ValueError:
            question = Q(enter_date__endswith=time.strftime('-02-29')) | Q(
                enter_date__endswith=time.strftime('-%m-%d'))
    result = EmployeeInfo.objects.filter(question).order_by('enter_date')
    division_list = []
    for index, one in enumerate(result):
        # print(one)
        division_ins = Divisionlist()
        # 处理后缀数值
        try:
            int(one.name[len(one.name) - 1])
            division_ins.name = one.name[:len(one.name) - 1]
        except ValueError:
            division_ins.name = one.name
        division_ins.code = one.code
        division_ins.reality_enter_date = one.enter_date
        division_ins.tel = one.tel
        division_ins.plan_date = time.date()
        division_ins.flag_num = division_ins.plan_date.year - one.enter_date.year
        division_ins.status = False
        division_ins.send_time = time
        division_ins.emp_pk = one
        division_ins.uid = datetime.date.today().strftime('%Y%m%d') + '02' + '01{index:0>4}'.format(index=index)
        division_list.append(division_ins)
    Divisionlist.objects.bulk_create(division_list)
    pass

def _get_birth_employee_info(today, days):
    """
    获取生日表中满足以下条件的人员数据
    plan_date >= today && plan_date <= today + datetime.timedelta(days=days)
    :param today: 基准日期
    :param days: 从今天开始到之后几天
    :return:
    """
    query_list = Q(plan_date__gte=today) & Q(plan_date__lte=today + datetime.timedelta(days=days)) & Q(status=False)
    return Birthlist.objects.filter(query_list).order_by('plan_date').all()
    pass

def _get_division_employee_info(today, days):
    """
    获取司龄表中满足以下条件的人员数据
    plan_date >= today && plan_date <= today + datetime.timedelta(days=days)
    :param today: 基准日期
    :param days: 从今天开始到之后几天
    :return:
    """
    query_list = Q(plan_date__gte=today) & Q(plan_date__lte=today + datetime.timedelta(days=days)) & Q(status=False)
    return Divisionlist.objects.filter(query_list).order_by('plan_date').all()
    pass

# 单条数据用不上
def _sms_send_quote(array):
    data_str = []
    for one in array:
        data_str.append(quote(one))
    return data_str
    pass

def _sms_send_new(today):
    """
    发送当天的短信
    :param today:
    :return:
    """
    #  新的数据获取方式和发送(单条发送)
    sms_log_ins_list = []
    for birth_ins in _get_birth_employee_info(today=today, days=0):
        #  短信发送
        param = {yc.MOBILE: birth_ins.tel,
                 yc.TEXT: birth[str(birth_ins.plan_date.strftime("%Y-%m"))].format(
                     Name=birth_ins.name, Day=today.strftime("%Y{year}%m{month}%d{day}").format(
                         year='年', month='月', day='日')),
                 yc.UID: birth_ins.uid}
        clnt.sms().single_send(param)
        sms_log_ins_list.append(_sms_log_ins_get(birth_ins))
        # TODO 异常处理
    for division_ins in _get_division_employee_info(today=today, days=0):
        #  短信发送
        param = {yc.MOBILE: division_ins.tel,
                 yc.TEXT: siling[str(division_ins.flag_num)].format(
                     Name=division_ins.name, Day=today.strftime("%Y{year}%m{month}%d{day}").format(
                         year='年', month='月', day='日')),
                 yc.UID: division_ins.uid}
        clnt.sms().single_send(param)
        sms_log_ins_list.append(_sms_log_ins_get(division_ins))
        # TODO 异常处理
    # 短信发送记录存储
    # TODO 重复记录发送, 待重新设计
    _sms_log_ins_list_save(sms_log_ins_list)
    pass


def _sms_log_ins_get(ins):
    assert isinstance(ins, Birthlist) or isinstance(ins, Divisionlist), "调用错误, 必须是 Birthlist/Divisionlist 实例"
    sms_log_ins = SMSLog()
    sms_log_ins.name = ins.name
    sms_log_ins.code = ins.code
    sms_log_ins.enter_date = ins.emp_pk.enter_date
    sms_log_ins.birth_date = ins.emp_pk.birth_date
    sms_log_ins.tel = ins.tel
    sms_log_ins.leave_status = ins.emp_pk.leave_status
    sms_log_ins.sms_type = 'birth' if isinstance(ins, Birthlist) else 'siling'
    sms_log_ins.flag_num = ins.flag_num
    sms_log_ins.log_date = ins.send_time.now()
    sms_log_ins.uid = ins.uid
    sms_log_ins.user_receive_time = None
    sms_log_ins.error_msg = None
    sms_log_ins.report_status = None
    return sms_log_ins

def _sms_log_ins_list_save(ins_list):
    if len(ins_list):
        assert isinstance(ins_list[0], SMSLog), "调用错误, 必须是 SMSLog 实例"
        SMSLog.objects.bulk_create(ins_list)
    pass

# 发送短信
def sms_send(time, days=0):
    # 删除上次获取的数据
    _data_delete()
    _transform(time, days)
    #  测试不发送短信
    if settings.conf.get(section='SMS', option='status') == 'online':
        # 短信发送
        _sms_send_new(time)

def _email_build_and_send(subject, body, to, cc=None):
    from_email = settings.DEFAULT_FROM_EMAIL
    msg = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=to, cc=cc)
    msg.content_subtype = "html"
    # 添加附件（可选）
    # msg.attach_file('./xxx.pdf')
    # 发送
    msg.send()
    pass

# 发送邮件
def email(time, days):
    # 删除上次获取的数据
    _data_delete()
    for day in range(days + 1):
        _transform(time, day)
    content = render(None, template_name='auto/blessing.html', context={
        'birth_result': _get_birth_employee_info(time, days),
        'siling_result': _get_division_employee_info(time, days), }).getvalue().decode("utf-8")
    if settings.conf.get(section='email', option='cc_addr', fallback=None):
        cc = settings.conf.get(section='email', option='cc_addr').split(',')
    else:
        cc = None
    _email_build_and_send(subject="祝福短信{today}".format(today=time.date()),
                          body=content, to=settings.conf.get(section='email', option='to_addr').split(','),
                          cc=cc)

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
    assert isinstance(today, datetime.datetime)
    while True:
        # print(is_workday(march_first))  # False
        # print(is_holiday(march_first))  # True
        march_first = today + datetime.timedelta(days=days)
        if is_workday(march_first.date()):
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
    update_empinfo_init()
except UserWarning:
    update_empinfo(sys.path[0] + '/auto/temp/祝福短信人员2018-02-28.xls')


def receive_date():
    """
    获取短信发送情况
    :return: json<list[{dict},]>
    """
    params = {'apikey': settings.conf.get(section="SMSServer", option="apikey"), 'page_size': '100'}
    # print(params)
    url = 'https://sms.yunpian.com/v2/sms/pull_status.json'
    req = requests.post(url, data=params)
    # print(req.url)
    # print(req.text)
    return req.text


def sms_receive_build(sms_receive_json):
    """
    将数据存储到数据库, 并去重
    :param sms_receive_json: json<list[{dict},]>
    :return:
    """
    error_list = []
    for one in json.loads(sms_receive_json):
        if one['report_status'] == 'SUCCESS':
            one['report_status'] = True
        elif one['report_status'] == 'FAIL':
            one['report_status'] = False
        else:
            # 意外情况
            error_list.append(one)
            continue
        if SMSLog.objects.filter(uid=one['uid']).exists():
            sms_log_ins = SMSLog.objects.filter(uid=one['uid']).get()
            sms_log_ins.user_receive_time = one['user_receive_time']
            sms_log_ins.error_msg = one['error_msg']
            sms_log_ins.report_status = one['report_status']
            sms_log_ins.save()
        else:
            error_list.append(one)
            pass
    # 处理意外情况
    # TODO 异常抛出
    return error_list
    pass


def receive():
    error_list = []
    while True:
        rec = receive_date()
        print(rec)
        if rec == '[]':
            break
        error_ins_list = sms_receive_build(rec)
        if len(error_ins_list):
            error_list += error_ins_list
    if len(error_list):
        _email_build_and_send(subject='短信检测异常数据{today}'.format(today=datetime.date.today()),
                              body='\n'.join(error_list),
                              to=settings.conf.get(section='email', option='error_to_addr').split(','),
                              )
    sms_not_receive()
    pass

def sms_not_receive():
    sms_log_result = SMSLog.objects.filter(Q(log_date=datetime.date.today()) & ~Q(report_status=True)).all()
    if len(sms_log_result):
        content = render(None, template_name='auto/sms_receive.html',
                         context={'sms_log_result': sms_log_result, }).getvalue().decode("utf-8")
        _email_build_and_send(subject="祝福短信未发送成功(含待返回){today}".format(today=datetime.date.today()),
                              body=content, to=settings.conf.get(section='email', option='receive_addr').split(','),)
    pass
