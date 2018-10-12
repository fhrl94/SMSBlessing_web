import sys
from django.contrib import admin

# Register your models here.
from auto.models import EmployeeInfo, UploadHistory, SMSLog
from auto.views import update_empinfo, auto_job, update_empinfo_init


class EmployeeInfoAdmin(admin.ModelAdmin):

    list_filter = ('leave_status', 'leave_send_status', )
    list_display = ('name', 'code', 'enter_date', 'birth_date', 'tel', 'leave_status', 'leave_send_status', )
    actions = ['admin_auto', ]
    # list_editable = ('leave_status', 'leave_send_status', )
    search_fields = ('name', 'code', 'tel', )
    ordering = ('code', )
    list_per_page = 50

    def admin_auto(self, request, queryset):
        # update_empinfo(sys.path[0] + '/auto/temp/祝福短信人员2018-02-28.xls')
        # 发送短信和邮件
        auto_job()
        pass
    pass

    admin_auto.short_description = '发送短信'

class UploadHistoryAdmin(admin.ModelAdmin):

    list_display = ('id', 'path_name', 'upload_time',)
    exclude = []
    actions = ['admin_loading_init', ]

    def admin_loading_init(self, request, queryset):
        # 数据初始化
        update_empinfo_init()
        print("人员信息更新操作")
        pass
    pass

    admin_loading_init.short_description = '读取数据'

class SMS_LogAdmin(admin.ModelAdmin):

    list_display = ('name', 'code', 'enter_date', 'birth_date', 'tel', 'leave_status', 'sms_type', 'flag_num', 'log_date', 'result')
    exclude = []
    search_fields = ('name', 'code', 'tel',)
    list_filter = ('sms_type', 'result', 'leave_status', )
    ordering = ('-code',)
    date_hierarchy = 'log_date'
    pass

admin.site.register(EmployeeInfo, EmployeeInfoAdmin)
admin.site.register(UploadHistory, UploadHistoryAdmin)
admin.site.register(SMSLog, SMS_LogAdmin)
# 设置站点标题
admin.site.site_header = '自动发送短信平台'
admin.site.site_title = '自动发送短信'  # 数据导出（分原始表单（HTML）、原始数据导出（excel））