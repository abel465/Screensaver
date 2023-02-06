import json
import screensaver
from options import Options


def main():
    options_file = "options.json"
    try:
        with open(options_file, "r") as f:
            options = Options(json.load(f))
    except FileNotFoundError:
        options = Options()
    screensaver.main(
        options.paths,
        options.image_time,
        options.randomize,
        options.no_video,
        options.no_gif,
        options.mute)


if __name__ == "__main__":
    main()
