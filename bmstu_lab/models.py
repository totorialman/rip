from django.db import models

class Order(models.Model):
    title = models.CharField(max_length=100)  # Название заказа
    description = models.TextField()  # Описание заказа

    def __str__(self):
        return self.title