import io
import datetime

from django.conf import settings
from django.utils._os import safe_join
from django.core.files.storage import Storage
from django.core.exceptions import ImproperlyConfigured

from dateutil import parser, tz

import requests


class BunnyStorage(Storage):
    """
    Implementation of Django's storage module using Bunny.net.
    """

    username = None
    password = None
    region = None
    hostname = None

    base_url = None
    headers = None

    def __init__(self, **kwargs):
        username = (
            kwargs["username"] if "username" in kwargs else settings.BUNNY_USERNAME
        )
        password = (
            kwargs["password"] if "password" in kwargs else settings.BUNNY_PASSWORD
        )
        region = (
            kwargs["region"]
            if "region" in kwargs
            else settings.BUNNY_REGION
            if settings.BUNNY_REGION
            else "ny"
        )
        hostname = (
            kwargs["hostname"]
            if "hostname" in kwargs
            else settings.BUNNY_HOSTNAME
            if settings.BUNNY_HOSTNAME
            else settings.MEDIA_URL
        )

        if not username:
            raise ImproperlyConfigured(
                "Setting BUNNY_USERNAME or `username` option is required."
            )

        if not password:
            raise ImproperlyConfigured(
                "Setting BUNNY_PASSWORD or `password` option is required."
            )

        self.base_url = ""

        if region == "de":
            self.base_url += "https://storage.bunnycdn.com/"
        else:
            self.base_url += f"https://{region}.storage.bunnycdn.com/"

        self.username = username
        self.password = password
        self.region = region
        self.hostname = hostname

        self.base_url += f"{username}/"
        self.headers = {"AccessKey": password}

    def _full_path(self, name) -> str:
        if name == "/":
            name = ""
        return safe_join(self.base_url, name).replace("\\", "/")

    def _save(self, name, content) -> str:
        r = requests.put(
            safe_join(self.base_url, name), data=content, headers=self.headers
        )
        return name

    def _open(self, name, mode="rb"):
        r = requests.get(safe_join(self.base_url, name), headers=self.headers)
        r.raise_for_status()

        return r.raw

    def delete(self, name) -> str:
        r = requests.delete(safe_join(self.base_url, name), headers=self.headers)

        return name

    def exists(self, name) -> bool:
        r = requests.head(safe_join(self.base_url, name), headers=self.headers)

        if r.status_code == 404:
            return False

        r.raise_for_status()

        return True

    def url(self, name: str) -> str:
        return self.hostname + name

    def size(self, name: str) -> int:
        r = requests.head(self.url(name))
        r.raise_for_status()

        file_size = r.headers.get("Content-Length", 0)

        return int(file_size)

    def listdir(self, path) -> tuple:
        r = requests.get(safe_join(self.base_url, path), headers=self.headers)
        r.raise_for_status()

        objects = r.json()

        return (
            [item["ObjectName"] for item in objects if item["IsDirectory"]],
            [item["ObjectName"] for item in objects if not item["IsDirectory"]],
        )

    def get_created_time(self, name) -> datetime.datetime:
        r = requests.get(
            safe_join(self.base_url, name.rsplit("/", 1)[0]), headers=self.headers
        )
        r.raise_for_status()

        iso_date = None

        for item in r.json():
            if item["ObjectName"] == name:
                iso_date = item["DateCreated"]
                break

        if iso_date is None:
            raise ValueError(f"File '{name}' does not exist.")

        if settings.USE_TZ == True:
            parsed_date = parser.parse(iso_date)
            parsed_date.replace(tzinfo=datetime.timezone.utc)
            return parsed_date
        else:
            parsed_date = parser.parse(iso_date)
            parsed_date.replace(tzinfo=datetime.timezone.utc)
            parsed_date.astimezone()
            parsed_date.replace(tzinfo=None)
            return parsed_date

    def get_modified_time(self, name) -> datetime.datetime:
        r = requests.get(
            safe_join(self.base_url, name.rsplit("/", 1)[0]), headers=self.headers
        )
        r.raise_for_status()

        iso_date = None

        for item in r.json():
            if item["ObjectName"] == name.rsplit("/", 1)[1]:
                iso_date = item["LastChanged"]
                break

        if iso_date is None:
            raise ValueError(f"File '{name}' does not exist.")

        if settings.USE_TZ == True:
            parsed_date = parser.parse(iso_date)
            parsed_date.replace(tzinfo=datetime.timezone.utc)
            return parsed_date
        else:
            parsed_date = parser.parse(iso_date)
            parsed_date.replace(tzinfo=datetime.timezone.utc)
            parsed_date.astimezone()
            parsed_date.replace(tzinfo=None)
            return parsed_date
