# gunicorn_config.py
workers = 3                    # (2 × cores) + 1
threads = 4                    # threads per worker
worker_class = "gthread"       # async threads, best for I/O-bound Django
bind = "0.0.0.0:8000"
timeout = 60                   # down from 120 — fail fast
keepalive = 5
max_requests = 1000            # restart workers after 1000 requests (prevents memory leaks)
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"    # use RAM for temp files — big speed boost