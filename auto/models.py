import sys

import datetime
from django.core.validators import RegexValidator
from django.db import models

# Create your models here.
# 定义User对象:
class EmployeeInfo(models.Model):

    # 表的结构:
    name = models.CharField('姓名', max_length=10)
    code = models.CharField('工号', max_length=10, validators=[RegexValidator(r'^[\d]{10}')], unique=True)
    enter_date = models.DateField('虚拟入职日期', )
    birth_date = models.DateField('出生日期', )
    tel = models.CharField('手机号码', max_length=11, validators=[RegexValidator(r'^[\d]{11}')], unique=True)
    leave_status = models.BooleanField('是否离职', )
    leave_send_status = models.BooleanField('是否发送离职短信', )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '员工信息'
        verbose_name_plural = '员工信息'

class Birthlist(models.Model):

    # 表的结构:
    name = models.CharField('姓名', max_length=10)
    code = models.CharField('工号', max_length=10, validators=[RegexValidator(r'^[\d]{10}')], )
    birth_date = models.DateField('出生日期', )
    tel = models.CharField('手机号码', max_length=11, validators=[RegexValidator(r'^[\d]{11}')], )
    plan_date = models.DateField('预计发送日期', )
    flag_num = models.PositiveIntegerField('月份', )
    status = models.BooleanField('是否投递',)
    send_time = models.DateTimeField('投递时间', )

    class Meta:
        unique_together = ('code', 'plan_date')
        verbose_name = '生日发送列表'
        verbose_name_plural = '生日发送列表'

    def __str__(self):
        return self.name

class Divisionlist(models.Model):

    # 表的结构:
    name = models.CharField('姓名', max_length=10)
    code = models.CharField('工号', max_length=10, validators=[RegexValidator(r'^[\d]{10}')], )
    reality_enter_date = models.DateField('虚拟入职日期', )
    tel = models.CharField('手机号码', max_length=11, validators=[RegexValidator(r'^[\d]{11}')], )
    plan_date = models.DateField('发送日期', )
    flag_num = models.PositiveIntegerField('司龄长度', )
    status = models.BooleanField('是否投递',)
    send_time = models.DateTimeField('投递时间', )

    class Meta:
        unique_together = ('code', 'plan_date')
        verbose_name = '司龄发送列表'
        verbose_name_plural = '司龄发送列表'

    def __str__(self):
        return self.name

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return '{upload_to}/{filename}_{time}'.format(upload_to=sys.path[0] + '/upload/', filename=filename,
                                                  time=datetime.datetime.today().strftime('%Y_%m_%d_%H_%M_%S'))

class UploadHistory(models.Model):
    # 表的结构:
    # path_name = models.FileField('文件名称', upload_to=sys.path[0] + '/upload/%Y_%m_%d/%H', )
    path_name = models.FileField('文件名称', upload_to=user_directory_path, )
    # TODO 获取现在的时间
    upload_time = models.DateTimeField('上传时间', )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = '员工信息文件上传'
        verbose_name_plural = '员工信息文件上传'

# class Run_Log(models.Model):
#     log_datetime = models.DateTimeField('投递时间', )
#     result = models.CharField('运行结果', max_length=200)
#     pass