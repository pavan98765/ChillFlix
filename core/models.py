import os
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

AGE_CHOICES = (
    ("All", "All"),
    ("kids", "kids"),
)

MOVIE_CHOICES = (
    ("seasonal", "seasonal"),
    ("single", "single"),
)


def get_upload_path(instance, filename):
    return os.path.join("movies", filename)


def get_flyer_upload_path(instance, filename):
    return os.path.join("flyers", filename)


# Create your models here.
class CustomUser(AbstractUser):
    profiles = models.ManyToManyField("Profile", blank=True)


class Profile(models.Model):
    name = models.CharField(max_length=225)
    age_limit = models.CharField(max_length=10, choices=AGE_CHOICES)
    uuid = models.UUIDField(default=uuid.uuid4)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=225, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4)
    type = models.CharField(max_length=10, choices=MOVIE_CHOICES)
    videos = models.ManyToManyField("Video")
    flyer = models.ImageField(upload_to=get_flyer_upload_path, null=True, blank=True)
    age_limit = models.CharField(
        max_length=10, choices=AGE_CHOICES, null=True, blank=True
    )

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        # Delete the associated flyer file
        if self.flyer:
            os.remove(self.flyer.path)
        super().delete(*args, **kwargs)


class Video(models.Model):
    title = models.CharField(max_length=225, blank=True, null=True)
    file = models.FileField(upload_to=get_upload_path)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        # Delete the associated video file
        if self.file:
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
