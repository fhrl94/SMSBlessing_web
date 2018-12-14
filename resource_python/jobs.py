from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job

from auto.views import auto_job, receive

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")


@register_job(scheduler, "cron", hour=8, minute=0, id="auto_send", replace_existing=True, misfire_grace_time=60*1)
def test_job():
    auto_job()

@register_job(scheduler, "cron", hour=8, minute=30, id="auto_receive_check", replace_existing=True, misfire_grace_time=60*1)
def receive_check_job():
    receive()


register_events(scheduler)

scheduler.start()
print("Scheduler started!")

# 下面这句加在定时任务模块的末尾...判断是否运行在 uWSGI模式下, 然后阻塞mule主线程(猜测).
try:
    import uwsgi
    while True:
        sig = uwsgi.signal_wait()
        print(sig)
except Exception as err:
    pass
