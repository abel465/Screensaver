#!/usr/bin/env python3

from tkinter import Tk, Label
from argparse import ArgumentParser, ArgumentTypeError
import PIL.ImageTk, PIL.ImageFile, PIL.Image
from functools import partial
import mimetypes
import itertools
import bisect
import random
import time
import sys
import vlc
import os

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

HISTORY_LENGTH = 50
DEFAULT_TIME = 2000

_isWindows = sys.platform.startswith('win')


def positive_int(string):
    message = f"'{string}' is not a positive non zero integer"
    if not string.isdigit():
        raise ArgumentTypeError(message)
    x = int(string)
    if x <= 0:
        raise ArgumentTypeError(message)
    return x


class RandomMediaPathProvider:
    def __init__(self, it, after, media_walk):
        def populate(it, after):
            def add(count, value):
                self.keys.append(self.count)
                self.values.append(value)
                self.indices.extend(range(self.count, self.count + count))
                self.count += count
            try:
                root, dirs, files = next(it)
            except StopIteration:
                return
            random.shuffle(dirs)
            count = sum(1 for _ in files)
            if count:
                add(count, root)
                after(42, populate, it, after)
            else:
                populate(it, after)
        self.keys = []
        self.values = []
        self.indices = []
        self.count = 0
        self.media_walk = media_walk
        populate(it, after)

    def __iter__(self):
        def get_random():
            i = random.randrange(self.count)
            self.count -= 1
            self.indices[i], self.indices[-1] = self.indices[-1], self.indices[i]
            n = self.indices.pop() + 1
            key = bisect.bisect(self.keys, n - 1) - 1
            return n - self.keys[key], self.values[key]
        while self.count:
            target, path = get_random()
            _, dirs, files = next(self.media_walk(path))
            yield from itertools.islice(files, target - 1, target)


class Screensaver(Tk):
    def __init__(self, paths, image_time, randomize, no_video, no_gif, mute):
        super().__init__()
        self.history = []
        self.index = 0
        self.image_time = image_time
        self.no_video = no_video
        self.no_gif = no_gif
        self.width, self.height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.bind("<Key>", lambda e: e.widget.quit())
        self.bind("<Left>", lambda e: self.previous_media())
        self.bind("<Right>", lambda e: self.next_media())
        self.attributes("-fullscreen", True)
        self.geometry(f"{self.width}x{self.height}")
        self.configure(background="black")
        self.panel = Label(self, border=0, background="black", width=self.width, height=self.height)
        self.panel.pack(expand=True)
        self.path_iter = self.get_path_iter(paths, randomize)
        if not self.no_video:
            self.video_player = vlc.MediaPlayer(vlc.Instance("--aout=adummy" if mute else ""))
            self.video_player.set_fullscreen(True)
            if _isWindows:
                self.video_player.set_hwnd(self.panel.winfo_id())
            else:
                self.video_player.set_xwindow(self.panel.winfo_id())
        self.display_media()

    def next_media(self):
        self.after_cancel(self.schedule_id)
        if not self.no_video:
            self.video_player.stop()
        self.display_media()

    def previous_media(self):
        self.index = max(0, self.index - 2)
        self.after_cancel(self.schedule_id)
        if not self.no_video:
            self.video_player.stop()
        self.display_media()

    def play_video(self, path):
        media = vlc.Media(path)
        self.video_player.set_media(media)
        self.video_player.play()
        return self.monitor_video()

    def monitor_video(self):
        if self.video_player.get_state() != vlc.State.Ended:
            self.schedule_id = self.after(42, self.monitor_video)
            return self.schedule_id
        self.video_player.stop()
        self.display_media()

    def media_walk(self, path):
        def onerror(e):
            raise e
        for root, dirs, files in os.walk(path, onerror=onerror):
            yield root, dirs, filter(self.is_valid_media, map(partial(os.path.join, root), files))

    def is_valid_media(self, path):
        match mimetypes.guess_type(path)[0]:
            case None:
                return False
            case "image/gif":
                return not self.no_gif
            case image if image.startswith("image/"):
                return True
            case video if video.startswith("video/"):
                return not self.no_video
            case _:
                return False

    def get_path_iter(self, paths, randomize):
        if randomize:
            random.shuffle(paths)
            it = itertools.chain.from_iterable(map(self.media_walk, paths))
            return iter(RandomMediaPathProvider(it, self.after, self.media_walk))
        else:
            def ordered_media_paths(it):
                for _, dirs, files in it:
                    dirs.sort()
                    yield from sorted(files)
            it = itertools.chain.from_iterable(map(self.media_walk, paths))
            return ordered_media_paths(it)

    def display_image(self, image):
        self.panel.configure(image=image)
        return self.after(self.image_time, self.display_media)

    def display_animated_gif(self, frames, delays):
        return self._display_animated_gif(frames, delays, time.perf_counter_ns(), 0)

    def _display_animated_gif(self, frames, delays, begin_time, i):
        if i == len(frames):
            if (time.perf_counter_ns() - begin_time) // 1_000_000 >= self.image_time:
                self.display_media()
                return
            else:
                i = 0
        self.panel.configure(image=frames[i])
        self.schedule_id = self.after(delays[i], self._display_animated_gif, frames, delays, begin_time, i+1)
        return self.schedule_id

    def create_image_callable(self, path):
        img = PIL.Image.open(path)
        w, h = img.size
        ratio = min(self.width/w, self.height/h)
        size = (int(ratio*w), int(ratio*h))
        img = PIL.ImageTk.PhotoImage(img.resize(size, PIL.Image.Resampling.LANCZOS))
        return partial(self.display_image, img)

    def create_gif_callable(self, path):
        img = PIL.Image.open(path)
        w, h = img.size
        ratio = min(self.width/w, self.height/h)
        size = (int(ratio*w), int(ratio*h))
        frames = []
        delays = []
        try:
            for i in itertools.count(1):
                frames.append(PIL.ImageTk.PhotoImage(img.resize(size, PIL.Image.Resampling.LANCZOS)))
                delays.append(img.info["duration"])
                img.seek(i)
        except EOFError:
            if len(frames) == 1:
                return partial(self.display_image, frames[0])
            else:
                return partial(self.display_animated_gif, frames, delays)

    def get_media_callable(self, path):
        match mimetypes.guess_type(path)[0]:
            case "image/gif":
                return self.create_gif_callable(path)
            case image if image.startswith("image/"):
                return self.create_image_callable(path)
            case video if video.startswith("video/"):
                return partial(self.play_video, path)

    def display_media(self):
        if self.index < len(self.history):
            media_callable = self.history[self.index]
            self.index += 1
        else:
            try:
                path = next(self.path_iter)
            except StopIteration:
                self.destroy()
                return
            media_callable = self.get_media_callable(path)
            self.history.append(media_callable)
            if len(self.history) > HISTORY_LENGTH:
                del self.history[0]
            else:
                self.index += 1
        self.schedule_id = media_callable()


def main(paths, image_time, randomize, no_video, no_gif, mute):
    screensaver = Screensaver(paths, image_time, randomize, no_video, no_gif, mute)
    screensaver.mainloop()


if __name__ == "__main__":
    parser = ArgumentParser(description="Screensaver program that supports video (with audio) and animated gifs")
    parser.add_argument("-t", "--image_time", type=positive_int, help="The time in milliseconds that each image will persist")
    parser.add_argument("--randomize", help="Randomize viewing order", action="store_true")
    parser.add_argument("--no-video", help="Skip over videos", action="store_true")
    parser.add_argument("--no-gif", help="Skip over gifs", action="store_true")
    parser.add_argument("--mute", help="Disable video audio", action="store_true")
    parser.add_argument("paths", nargs="+", help="A path for the screensaver to show media of")
    args = parser.parse_args()

    main(args.paths, args.image_time or DEFAULT_TIME, args.randomize, args.no_video, args.no_gif, args.mute)
