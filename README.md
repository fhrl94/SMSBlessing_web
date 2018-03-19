# 短信自动发送——线上化

- [更新](#更新)

- [bug](#bug)

- [使用说明](#使用说明)

- [文件说明](#文件说明)

- [背景介绍](#背景介绍)

## 更新

- 2018.3.16 修复发送的邮件内容错误（发送多天的邮件时，没有循环调用 _transform() ）

## bug

1. 发送多天的邮件内容错误（只有最后一天的）

## 使用说明

安装 uWSGI

`pip3.6 install uWSGI`

安装 Nginx

`yum install epel-release`

`yum install python-devel nginx`

后续 Linux 操作
```
需要是使用 Django 命令进行收集
在setting.py 文件中增加 
            STATIC_URL = '/static/'
            STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')
            
python manage.py collectstatic

使用软连接命令 
ln -s 【research_nginx.conf】的绝对路径 /etc/nginx/conf.d/XXX.conf

Nginx 操作命令
/bin/systemctl restart  nginx.service     重启 Nginx 服务 对配置进行更改后需要重启
/bin/systemctl start  nginx.service       启动 Nginx 服务
systemctl status nginx.service -l          查看 Nginx 错误信息

```
## 文件说明

- resource_python/constants.py 短信发送的模板

- resource_python/data_pull.py 祝福短信源生成脚本，可以使用 py2exe 来生成 exe 文件

- resource_python/jobs.py 定时任务 需要 `pip install django-apscheduler`

- resource_python/SMSBlessing_web.conf 个性化配置

```
[email]
smtp_server = smtp.qiye.163.com
smtp_port = 465
from_addr = hr@xxx.com
from_addr_str = 祝福管理站 <hr@xxx.com>
password = password
to_addr = hr1@xxx.com,hr2@xxx.com,hr3@xxx.com

[SMSServer]
apikey = apikeyXXX

[SMS]
# status = test #此行为测试，不发送短信
status = online
```

## 背景介绍

1. 祝福短信自动发送，节约人工发送的时间、精力成本，保证准点发送。

2. 人员超过1000+时，每天能节约15min。

3. 使用的平台是[云片](https://www.yunpian.com)

4. 记录每天发送人员，方便后期汇总

5. 数据源可以通过 [resource_python/data_pull.py](https://github.com/fhrl94/SMSBlessing_web/blob/master/resource_python/data_pull.py) 自动生成

5. 通过网页（web）更新数据源，保证信息源准确
