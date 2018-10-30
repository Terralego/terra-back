from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

UserModel = get_user_model()


def users_of_group(group_name):
    return [
        {
            'email': user.email,
            'properties': user.properties,
        }
        for user in Group.objects.get(name=group_name)
    ]


def get_user_from_pk(pk):
    try:
        user = UserModel.objects.get(pk=pk)
        return {
            'email': user.email,
            'properties': user.properties,
        }
    except UserModel.DoesNotExist:
        return
