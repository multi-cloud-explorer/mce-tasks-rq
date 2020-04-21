from redis.exceptions import LockError

from rq.decorators import job as _rq_job
from rq.connections import get_current_connection

from django.conf import settings

from django_rq.queues import get_queue

"""
import time
try:
    current_conn = get_current_connection()
    print('!!! current_conn : ', current_conn, type(current_conn))
    with current_conn.lock('my-lock-key', blocking_timeout=5) as lock:
        print('!!! lock...', lock)
        time.sleep(2)
except LockError:
    print('!!! lock error')

"""

def mce_job(func_or_queue, connection=None, *args, **kwargs):
    """
    The same as RQ's job decorator, but it automatically works out
    the ``connection`` argument from RQ_QUEUES.

    And also, it allows simplified ``@job`` syntax to put job into
    default queue.

    If RQ.DEFAULT_RESULT_TTL setting is set, it is used as default
    for ``result_ttl`` kwarg.
    """
    if callable(func_or_queue):
        func = func_or_queue
        queue = 'default'
    else:
        func = None
        queue = func_or_queue

    if isinstance(queue, str):
        try:
            queue = get_queue(queue)
            if connection is None:
                connection = queue.connection
        except KeyError:
            pass

    RQ = getattr(settings, 'RQ', {})
    default_result_ttl = RQ.get('DEFAULT_RESULT_TTL')
    if default_result_ttl:
        kwargs.setdefault('result_ttl', default_result_ttl)

    # renvoi une instance de la class rq.decorators.job
    decorator = _rq_job(queue, connection=connection, *args, **kwargs)
    if func:
        # appel le __call__ qui renvoi la fonction delay()
        return decorator(func)
    return decorator

