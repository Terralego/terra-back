from django.contrib.auth import get_user_model

UserModel = get_user_model()


def users_of_group(group_name):
    return [
        {
            'email': user.email,
            'properties': user.properties,
        }
        for user in UserModel.objects.filter(groups__name=group_name)
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
