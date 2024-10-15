from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *



def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('logo', image_name, file_object, file_object.size)
        return f"http://localhost:9000/logo/{image_name}"  # Возвращаем URL как строку
    except Exception as e:
        return {"error": str(e)}


def add_url(new_stock, url):
    
    client = Minio(           
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{new_stock.id}.png"  # Имя объекта для загрузки
    
    
    if not url:
        return {"error": "Нет файла для изображения логотипа."}
    
    result = process_file_upload(url, client, img_obj_name)

    if 'error' in result:
        return result  # Возвращаем словарь с ошибкой, если она есть
    
    
    # Сохраняем URL в объекте
    new_stock.url = result  # URL, который вернулся из process_file_upload
    new_stock.save()
    print(result)
    return result  # Возвращаем строку URL



def delete_file_from_minio(file_url):
    minio_client = Minio(
    endpoint=settings.AWS_S3_ENDPOINT_URL,
    access_key=settings.AWS_ACCESS_KEY_ID,
    secret_key=settings.AWS_SECRET_ACCESS_KEY,
    secure=settings.MINIO_USE_SSL
    )
    bucket_name = "logo"  # замените на имя вашего бакета
    file_name = file_url.split('/')[-1]  # Получаем имя файла из URL
    minio_client.remove_object(bucket_name, file_name)