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
        try:
            username = (
                kwargs["username"] if "username" in kwargs else settings.BUNNY_USERNAME
            )
        except AttributeError:
            raise ImproperlyConfigured(
                "Setting BUNNY_USERNAME or `username` option is required."
            )
        
        try:
            password = (
                kwargs["password"] if "password" in kwargs else settings.BUNNY_PASSWORD
            )
        except AttributeError:
            raise ImproperlyConfigured(
                "Setting BUNNY_PASSWORD or `password` option is required."
            )
        
        region = (
            kwargs["region"]
            if "region" in kwargs
            else settings.BUNNY_REGION
            if hasattr(settings, 'BUNNY_REGION')
            else "ny"
        )
        
        try:
            hostname = (
                kwargs["hostname"]
                if "hostname" in kwargs
                else settings.BUNNY_HOSTNAME
                if hasattr(settings, 'BUNNY_HOSTNAME')
                else settings.MEDIA_URL
            )
        except AttributeError:
            raise ImproperlyConfigured(
                "Neither `BUNNY_HOSTNAME` or `MEDIA_URL` are configured. django-bunny requires one of them to work."
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
        self.base_dir = kwargs['base_dir'] if "base_dir" in kwargs else settings.BUNNY_BASE_DIR if hasattr(settings, 'BUNNY_BASE_DIR') else ""
        self.headers = {"AccessKey": password, "Accept": "*/*"}

        try:
            self.base_url += self.base_dir
        except:
            pass

    def _full_path(self, name) -> str:
        if name == "/":
            name = ""
        return self.base_url + name.replace("\\", "/")

    def _save(self, name, content) -> str:
        r = requests.put(
            self.base_url + name.replace("\\", "/"), data=content, headers=self.headers
        )
        return name

    def _open(self, name, mode="rb"):
        r = requests.get(self.base_url + name.replace("\\", "/"), headers=self.headers)
        r.raise_for_status()

        return r.raw

    def delete(self, name) -> str:
        r = requests.delete(self.base_url + name, headers=self.headers)

        return name

    def exists(self, name) -> bool:
        r = requests.get(self.base_url + name.replace("\\", "/"), headers=self.headers, stream=True)
        r.close()

        if r.status_code == 404:
            return False

        r.raise_for_status()

        return True

    def url(self, name: str) -> str:
        return self.hostname + self.base_dir + name.replace("\\", "/")

    def size(self, name: str) -> int:
        r = requests.get(self.url(name), stream=True)
        r.close()

        r.raise_for_status()

        file_size = r.headers.get("Content-Length", 0)

        return int(file_size)

    def listdir(self, path) -> tuple:
        r = requests.get(self.base_url + path.replace("\\", "/"), headers=self.headers)
        r.raise_for_status()

        objects = r.json()

        return (
            [item["ObjectName"] for item in objects if item["IsDirectory"]],
            [item["ObjectName"] for item in objects if not item["IsDirectory"]],
        )

    def get_created_time(self, name) -> datetime.datetime:
        r = requests.get(
            self.base_url + name.replace("\\", "/").rsplit("/", 1)[0], headers=self.headers
        )
        r.raise_for_status()

        iso_date = None

        for item in r.json():
            try:
                if item["ObjectName"] == name.rsplit("/", 1)[len(name.rsplit("/", 1) - 1)]:
                    iso_date = item["DateCreated"]
                    break
            except:
                # Error fetching creation date for this file. A
                # NotImplementedError is raised as specified by the Django
                # documentation.
                raise NotImplementedError()

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
            self.base_url + name.replace("\\", "/").rsplit("/", 1)[0], headers=self.headers
        )
        r.raise_for_status()

        iso_date = None

        for item in r.json():
            try:
                if item["ObjectName"] == name.rsplit("/", 1)[len(name.rsplit("/", 1) - 1)]:
                    iso_date = item["LastChanged"]
                    break
            except:
                # Error fetching last modification date for this file. A
                # NotImplementedError is raised as specified by the Django
                # documentation.
                raise NotImplementedError()

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
