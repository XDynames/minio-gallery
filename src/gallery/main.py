import os
from typing import Dict, Generator, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from minio import Minio

app = FastAPI()

templates = Jinja2Templates(directory="templates")


MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")

minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
)


@app.get("/images/{_:path}")
def get_gallery(request: Request) -> HTMLResponse:
    images = get_images(request)
    context = get_render_context(images, request)
    return templates.TemplateResponse("gallery.html", context)


def get_images(request: Request) -> List[Dict]:
    bucket_name = get_bucket_name(request)
    prefix = get_prefix(request)
    objects = list_objects(bucket_name, prefix)
    return get_image_urls(bucket_name, objects)


def get_bucket_name(request: Request) -> str:
    return request.url.path[1:].split("/")[1]


def get_prefix(request: Request) -> str:
    return "/".join(request.url.path[1:].split("/")[2:])


def list_objects(bucket: str, prefix: str) -> Generator:
    return minio_client.list_objects(bucket_name=bucket, prefix=prefix)


def get_image_urls(bucket: str, objects: Generator) -> List[Dict]:
    image_urls = []
    for obj in objects:
        if is_object_image(bucket, obj.object_name):
            image_url = {"url": f"/{bucket}/{obj.object_name}"}
            image_urls.append(image_url)
    return image_urls


def is_object_image(bucket: str, prefix: str) -> bool:
    obj_info = minio_client.stat_object(bucket, prefix)
    return "image" in obj_info.content_type


def get_render_context(image_urls: List[Dict], request: Request) -> Dict:
    context = {
        "images": image_urls,
        "minio_host": MINIO_ENDPOINT,
        "protocol": "https://",
        "request": request,
    }
    return context
