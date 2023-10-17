#!/usr/bin/env python3

import json
import screensaver
import datetime
import traceback
from options import Options


def main():
    options_file = "options.json"
    try:
        with open(options_file, "r") as f:
            options = Options(json.load(f))
    except FileNotFoundError:
        options = Options()
    try:
        screensaver.main(
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
