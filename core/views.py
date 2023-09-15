from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .forms import ProfileForm
from .models import Profile, Movie

# Create your views here.


class Home(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:profile_list")
        return render(request, "index.html")


@method_decorator(login_required, name="dispatch")
class ProfileList(View):
    def get(self, request, *args, **kwargs):
        profiles = request.user.profiles.all()
        return render(
            request,
            "profileList.html",
            {
                "profiles": profiles,
            },
        )


@method_decorator(login_required, name="dispatch")
class ProfileCreate(View):
    def get(self, request, *args, **kwargs):
        form = ProfileForm()

        return render(
            request,
            "profileCreate.html",
            {"form": form},
        )

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST or None)

        if form.is_valid():
            profile = Profile.objects.create(**form.cleaned_data)
            if profile:
                request.user.profiles.add(profile)
                return redirect("core:profile_list")

        return render(request, "profileCreate.html", {"form": form})


@method_decorator(login_required, name="dispatch")
class Watch(View):
    def get(self, request, profile_id, *args, **kwargs):
        try:
            profile = Profile.objects.get(uuid=profile_id)

            movies = Movie.objects.filter(age_limit=profile.age_limit)

            try:
                showcase = movies[0]
            except:
                showcase = None

            if profile not in request.user.profiles.all():
                return redirect(to="core:profile_list")
            return render(
                request, "movieList.html", {"movies": movies, "show_case": showcase}
            )
        except Profile.DoesNotExist:
            return redirect(to="core:profile_list")


@method_decorator(login_required, name="dispatch")
class ShowMovieDetail(View):
    def get(self, request, movie_id, *args, **kwargs):
        try:
            movie = Movie.objects.get(uuid=movie_id)
            return render(request, "movieDetail.html", {"movie": movie})
        except Movie.DoesNotExist:
            return redirect("core:profile_list")


# @method_decorator(login_required, name="dispatch")
# class ShowMovie(View):
#     def get(self, request, movie_id, *args, **kwargs):
#         try:
#             movie = Movie.objects.get(uuid=movie_id)
#             movie = movie.videos.values()

#             return render(
#                 request,
#                 "showMovie.html",
#                 {"movie": list(movie)},
#             )

#         except Movie.DoesNotExist:
#             return redirect("core:profile_list")


def stream_file_with_range(file, start=0, end=None, block_size=8192):
    file_size = os.fstat(file.fileno()).st_size
    if end is None:
        end = file_size
    if start >= file_size:
        # If the requested range starts beyond the end of the file, return an empty stream
        yield b""
    else:
        file.seek(start)
        while start < end:
            data = file.read(min(end - start, block_size))
            if not data:
                break
            start += len(data)
            yield data


from django.http import StreamingHttpResponse, FileResponse, Http404
import os
import re
import mimetypes


@method_decorator(login_required, name="dispatch")
class ShowMovie(View):
    def get(self, request, movie_id, *args, **kwargs):
        try:
            movie = Movie.objects.get(uuid=movie_id)
            video = movie.videos.first()  # get the first video related to the movie

            video_path = video.file.path
            range_header = request.META.get("HTTP_RANGE", "").strip()
            range_match = re.compile(r"bytes\s*=\s*(\d+)-(\d*)", re.I).match(
                range_header
            )
            size = os.path.getsize(video_path)
            content_type, encoding = mimetypes.guess_type(video_path)
            content_type = content_type or "application/octet-stream"
            if range_match:
                first_byte, last_byte = range_match.groups()
                first_byte = int(first_byte) if first_byte else 0
                last_byte = int(last_byte) if last_byte else size - 1
                if last_byte >= size:
                    last_byte = size - 1
                length = last_byte - first_byte + 1
                resp = StreamingHttpResponse(
                    stream_file_with_range(
                        open(video_path, "rb"), first_byte, last_byte
                    ),
                    content_type=content_type,
                    status=206,
                )
                resp["Content-Length"] = str(length)
                resp["Content-Range"] = "bytes %s-%s/%s" % (first_byte, last_byte, size)
            else:
                resp = FileResponse(open(video_path, "rb"), content_type=content_type)
                resp["Content-Length"] = str(size)
            resp["Accept-Ranges"] = "bytes"
            return resp

        except Movie.DoesNotExist:
            return redirect("core:profile_list")
