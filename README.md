# django-bunny

A bunny.net storage for Django. It was created as a replacement for [django-bunny-storage](https://github.com/willmeyers/django-bunny-storage).


## Installation

You can install the library using `pip`:

```bash
pip install django-bunny
```


## Configuration

First, add `django_bunny` to your `INSTALLED_APPS`:

```py
INSTALLED_APPS = [
    ...,
    "django_bunny",
    ...
]
```

Now, create the following variables inside your `settings.py` file. These are required if you are using Django < `4.2`. Otherwise, you can use `OPTIONS` in the `STORAGES` setting.

```py
# These can be found in your storage's dashboard under `FTP & API Access`
BUNNY_USERNAME = "my-storage-name"
BUNNY_PASSWORD = "my-storage-password"

# This is the storage region's code. E.g. Los Angeles is `la`, Singapore is
# `sg`, etc. The default is `ny` (New York).
BUNNY_REGION = "my-storage-region"

# Optional. For example, `https://myzone.b-cdn.net/`. `MEDIA_URL` will be used
# if this is not set.
BUNNY_HOSTNAME = "my-pullzone-hostname"


# Optional. For example, `static/`. If not set, files will be stored in the
# storage's root dir.
BUNNY_BASE_DIR = "my-storage-base-dir-where-i-want-my-files-stored/"
```

Finally, depending on which version of Django you are using you'll need to create one of these variables:

```py
# Django < 4.2
DEFAULT_FILE_STORAGE = 'django_bunny.storage.BunnyStorage'

# Django >= 4.2. Set `BunnyStorage` where you want to use bunny.net's storage.
{
    "default": {
        "BACKEND": "django_bunny.storage.BunnyStorage",

        # Add this if you did not create the BUNNY_* settings before. They are
        # the same as BUNNY_* variables.
        "OPTIONS": {
            "username": "my-storage-name",
            "password": "my-storage-password",
            
            # Optional. Defaults to `ny`
            "region": "my-storage-region",
            
            # Optional. `MEDIA_URL` will be used if it is not set
            "hostname": "my-pullzone-hostname",

            # Optional. `BUNNY_BASE_DIR` will be used if it is not set.
            "base_dir": "my-storage-base-dir-where-i-want-my-files-stored/"
        }
    },
}
```

In Django >= 4.2 you can set different credentials for the different storages. This allows you to, for example, use a separate storage for static files.


## Using in templates

In templates, you can use `{{ instance.file.url }}` directly. For example:

```html
<img src="{{ instance.file.url }}" />
```
