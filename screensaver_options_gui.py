#!/usr/bin/env python3

import tkinter as tk
import tkinter.filedialog as tk_filedialog
import os
import json
import datetime
import traceback
import screensaver_raw
from subprocess import call, getoutput, DEVNULL
from options import Options


def enable_autodisplay():
    display_type = getoutput('loginctl show-session $(loginctl | grep "$USER" | awk \'{print $1}\') -p Type')[5:]
    return (display_type == 'x11' and call('which systemctl xwininfo xprintidle', stdout=DEVNULL, shell=True) == 0) \
        or (display_type == 'wayland' and call('which systemctl swayidle', stdout=DEVNULL, shell=True) == 0)


class ScreensaverOptionsGUI(tk.Tk):
    def __init__(self, options):
        super().__init__()
        self.title("Screensaver Options")
        self.options = options
        self.finished = False
        self.no_video = tk.BooleanVar(value=options.no_video)
        self.no_gif = tk.BooleanVar(value=options.no_gif)
        self.randomize = tk.BooleanVar(value=options.randomize)
        self.mute = tk.BooleanVar(value=options.mute)
        self.autodisplay = tk.BooleanVar(value=options.autodisplay)
        self.image_time = tk.IntVar(value=options.image_time)
        self.folder_name = tk.StringVar(value=options.paths[0])

        frame = tk.Frame(self, borderwidth=20)
        frame.grid(row=0, column=0)

        tk.Button(frame, text="choose folder", command=self.choose_folder) \
            .grid(row=0, column=0, padx=5)
        tk.Entry(frame, textvariable=self.folder_name) \
            .grid(row=0, column=1)

        slider_frame = tk.Frame(frame)
        slider_frame.grid(row=1, column=0, columnspan=2, pady=10)
        tk.Label(slider_frame, text="image time (ms):") \
            .grid(row=0, column=0)
        tk.Label(slider_frame, textvariable=self.image_time, width=5) \
            .grid(row=0, column=1)
        tk.Scale(slider_frame, from_=200, to=10000, variable=self.image_time, orient=tk.HORIZONTAL, showvalue=False, resolution=100) \
            .grid(row=0, column=2)

        checkbox_frame = tk.Frame(frame)
        checkbox_frame.grid(row=2, column=0)
        tk.Checkbutton(checkbox_frame, text="disable video", variable=self.no_video, anchor=tk.W) \
            .grid(row=0, column=0)
        tk.Checkbutton(checkbox_frame, text="disable gif", variable=self.no_gif, anchor=tk.W) \
            .grid(row=1, column=0)
        tk.Checkbutton(checkbox_frame, text="randomize", variable=self.randomize, anchor=tk.W) \
            .grid(row=2, column=0)
        tk.Checkbutton(checkbox_frame, text="mute", variable=self.mute, anchor=tk.W) \
            .grid(row=3, column=0)
        tk.Checkbutton(checkbox_frame, text="autodisplay", variable=self.autodisplay, command=self.on_autodisplay, state="normal" if enable_autodisplay() else "disable") \
            .grid(row=4, column=0, columnspan=2)

        tk.Button(frame, text="go", command=self.done, anchor=tk.SE) \
            .grid(row=5, column=1)

    def choose_folder(self):
        self.folder_name.set(
            tk_filedialog.askdirectory(initialdir=self.folder_name.get()))

    def on_autodisplay(self):
        if self.autodisplay.get():
            if not os.path.isfile('~/.config/systemd/user/screensaver.service'):
                call('mkdir -p ~/.config/systemd/user/', shell=True)
                with open('screensaver.service', 'r') as file:
                    data = file.read()
                dir = os.path.dirname(os.path.realpath(__file__))
                data = data.replace("{dir}", dir)
                with open(f'{os.path.expanduser("~")}/.config/systemd/user/screensaver.service', 'w') as file:
                    file.write(data)
            call('systemctl start --user screensaver.service', shell=True)
            call('systemctl enable --user screensaver.service', shell=True)
        else:
            call('systemctl stop --user screensaver.service', shell=True)
            call('systemctl disable --user screensaver.service', shell=True)
        call('systemctl status --user screensaver.service', shell=True)

    def done(self):
        self.options.paths = (self.folder_name.get(),)
        self.options.image_time = self.image_time.get()
        self.options.randomize = self.randomize.get()
        self.options.no_video = self.no_video.get()
        self.options.no_gif = self.no_gif.get()
        self.options.mute = self.mute.get()
        self.options.autodisplay = self.autodisplay.get()
        self.finished = True
        self.destroy()


def main():
    options_file = "options.json"
    try:
        with open(options_file, "r") as f:
            options = Options(json.load(f))
    except FileNotFoundError:
        options = Options()
    options_gui = ScreensaverOptionsGUI(options)
    options_gui.mainloop()
    if options_gui.finished:
        with open(options_file, "w") as f:
            json.dump(options, f, default=lambda x: x.__dict__)
        try:
            screensaver_raw.main(
                options.paths,
                options.image_time,
                options.randomize,
                options.no_video,
                options.no_gif,
                options.mute)
        except Exception:
            t = datetime.datetime.now()
            with open(f"screensaver_crash_log_{t.date()}_{t.time()}", "w") as f:
                f.write(traceback.format_exc())


if __name__ == "__main__":
    main()
