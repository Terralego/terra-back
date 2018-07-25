from django.db import models


class NotificationManager(models.Manager):

    def read_all(self):
        return self.update(read=True)

    def unread(self):
        return self.filter(read=False)
