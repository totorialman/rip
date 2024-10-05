from django.db import models
from django.contrib.auth.models import User

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'



class Vmachine_Service(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Название виртуальной машины")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    description = models.TextField(verbose_name="Описание")
    description_tech = models.TextField(verbose_name="Техническое описание")
    vcpu = models.CharField(max_length=50, verbose_name="vCPU")
    ram = models.CharField(max_length=50, verbose_name="ОЗУ")
    ssd = models.CharField(max_length=50, verbose_name="SSD")
    url = models.URLField(verbose_name="Изображение")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Статус")

    class Meta:
        db_table = 'vmachine_service'
        verbose_name = "Услуга виртуальной машины"
        verbose_name_plural = "Услуги виртуальных машин"


class Vmachine_Request(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('deleted', 'Deleted'),
        ('formed', 'Formed'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    formed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата формирования")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Создатель")
    moderator = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='moderator_requests', verbose_name="Модератор")

    class Meta:
        db_table = 'vmachine_request'
        verbose_name = "Заявка на виртуальную машину"
        verbose_name_plural = "Заявки на виртуальные машины"


class Vmachine_Request_Service(models.Model):
    request = models.ForeignKey(Vmachine_Request, on_delete=models.CASCADE, verbose_name="Заявка")
    service = models.ForeignKey(Vmachine_Service, on_delete=models.CASCADE, verbose_name="Услуга")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    is_main = models.BooleanField(default=False, verbose_name="Основная услуга")
    order = models.IntegerField(null=True, blank=True, verbose_name="Порядок")

    class Meta:
        unique_together = (('request', 'service'),)
        db_table = 'vmachine_request_service'
        verbose_name = "Связь заявки и услуги"
        verbose_name_plural = "Связи заявок и услуг"