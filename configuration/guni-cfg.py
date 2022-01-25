from multiprocessing import cpu_count
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
gun_log_dir = os.path.join(current_dir, "gunicorn_log")
os.makedirs(gun_log_dir, exist_ok=True, mode=0o775)

# gunicorn --worker-class=gevent API.wsgi:application --reload --bind 127.0.0.1:8001
# gunicorn -c guni-cfg.py API.wsgi:application

bind = ["127.0.0.1:8001"]
daemon = True  # 是否开启守护进程模式
workers = 8  # 工作进程数量
threads = 2  # 每个工作者的线程数
worker_class = "gevent"  # 指定一个异步处理的库
worker_connections = 65535  # 单个进程的最大连接数
keepalive = 60  # 服务器保持连接的时间，能够避免频繁的三次握手过程
timeout = 30  # 一个请求的超时时间
graceful_timeout = 10  # 重启时限
capture_output = True  # 是否捕获输出
loglevel = "debug"  # 日志级别
pidfile = os.path.join(gun_log_dir, 'gunicorn.pid')  # 保存gunicorn的进程pid的文件
accesslog = os.path.join(gun_log_dir, 'acess.log')  # 访问日志存储路径
errorlog = os.path.join(gun_log_dir, 'error.log')  # 错误日志存储路径

