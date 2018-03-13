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
