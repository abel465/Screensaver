import json
import screensaver
import datetime
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
    except Exception as e:
        t = datetime.datetime.now()
        with open(f"screensaver_crash_log_{t.date()}_{t.time()}", "w") as f:
            f.write(t)
            f.write("\n")
            f.write(e)


if __name__ == "__main__":
    main()
