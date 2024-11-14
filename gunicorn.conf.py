import multiprocessing

bind = '0.0.0.0:8000'
backlog = 2048
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
threads = 1
worker_connections = 1000
timeout = 30
graceful_timeout = 30
keepalive = 2
max_requests = 0
max_requests_jitter = 0
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
reload = False
preload_app = False
daemon = False
user = 1000
group = 1000
umask = 0
tmp_upload_dir = None
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on',
}
forwarded_allow_ips = '0.0.0.0'
