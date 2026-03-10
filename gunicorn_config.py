import multiprocessing

# For I/O-bound Django apps, use (2 x cores) + 1 workers
# but override with threads for async I/O efficiency
workers          = (2 * multiprocessing.cpu_count()) + 1  # dynamic
threads          = 8      # up from 4 — I/O bound workload supports this
worker_class     = 'gthread'
bind             = '0.0.0.0:8000'
timeout          = 120    # up from 30 — prevent premature worker kills
graceful_timeout = 30     # give workers time to finish on restart
keepalive        = 5
max_requests     = 1000
max_requests_jitter = 100
worker_tmp_dir   = '/dev/shm'
backlog          = 2048   # queue up to 2048 pending connections
