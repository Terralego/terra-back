from django.contrib.auth.models import Group


def users_of_group(group_name):
    return [
        {
            'email': user.email,
            'properties': user.properties,
        }
        for user in Group.objects.get(name=group_name)
    ]
