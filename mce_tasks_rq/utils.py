import logging

from rq import get_current_job

class CurrentJobFilter(logging.Filter):
    def filter(self, record):
        current_job = get_current_job()

        record.job_id = current_job.id if current_job else ""
        record.job_func_name = current_job.func_name if current_job else ""

        return True

def get_job_logger(name):
    logger = logging.getLogger("rq.job." + name)

    handler = logging.StreamHandler()
    format = "[%(asctime)s][PID:%(process)d][%(levelname)s][%(name)s] job.func_name=%(job_func_name)s job.id=%(job_id)s %(message)s"
    handler.formatter = logging.Formatter(format)
    #handler.formatter = logging.Formatter(settings.RQ_WORKER_JOB_LOG_FORMAT)
    handler.addFilter(CurrentJobFilter())

    logger.addHandler(handler)
    logger.propagate = False

    return logger
