from django.db import models


class CharacterData(models.Model):
    profile = models.ForeignKey(
        to='ugc.Profile',
        verbose_name='Profile',
        on_delete=models.PROTECT,
    )
    first_name = models.TextField(
        verbose_name='First name',
    )
    last_name = models.TextField(
        verbose_name='Last name',
    )
    phone_number = models.TextField(
        verbose_name='Phone number',
    )
    email = models.TextField(
        verbose_name='E-mail',
    )

    def __str__(self):
        return f'{self.profile} data'

    class Meta:
        verbose_name = 'User data'
        verbose_name_plural = 'Users Data'


class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='ID',
        unique=True,
    )
    name = models.TextField(
        verbose_name='User name',
    )
    statement = models.BooleanField(
        verbose_name='Form process status',
        default=False,
    )

    def __str__(self):
        return f'#{self.external_id} {self.name}'

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'


class Message(models.Model):
    profile = models.ForeignKey(
        to='ugc.Profile',
        verbose_name='Profile',
        on_delete=models.PROTECT,
    )
    text = models.TextField(
        verbose_name='Text',
    )
    created_at = models.DateTimeField(
        verbose_name='Date Time of creation',
        auto_now_add=True,
    )

    def __str__(self):
        return f'Message {self.pk} from {self.profile}'

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
