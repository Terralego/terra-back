import factory
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class TerraUserFactory(factory.DjangoModelFactory):

    class Meta:
        model = UserModel

    email = factory.Faker('email')
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        kwargs.update({'password': kwargs.get('password', '123456')})
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
