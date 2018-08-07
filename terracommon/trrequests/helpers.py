import datetime
import os


def rename_comment_attachment(instance, filename):
    ur = instance.userrequest
    ur_year = ur.created_at.year
    ur_month = ur.created_at.month
    return os.path.join(f'userrequests/{ur_year}/{ur_month:02d}/{ur.pk}',
                        f'comment_{datetime.date.today():%d}')
