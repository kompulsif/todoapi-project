from celery import Task
from database import db_session


class DBActionTask(Task):
    """
    Tasklerin icinde veritabani islemlerinin otomatize
    edilmesi icin yazilmis base sinif

    Kullanildigi her taske bir db session acar
    """

    def __init__(self):
        self.sessions = {}

    def before_start(self, task_id, args, kwargs):
        self.sessions[task_id] = db_session()
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def session(self):
        return self.sessions[self.request.id]
