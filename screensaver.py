#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError

import screensaver_raw
import screensaver_from_config
import screensaver_options_gui
import os

def positive_int(string):
    message = f"'{string}' is not a positive non zero integer"
    if not string.isdigit():
        raise ArgumentTypeError(message)
    x = int(string)
    if x <= 0:
        raise ArgumentTypeError(message)
    return x


if __name__ == "__main__":
    parser = ArgumentParser(description="Screensaver program that supports video (with audio) and animated gifs")
    subparsers = parser.add_subparsers(help='Description',dest="command")
    raw_parser = subparsers.add_parser('raw');
    set_config_parser = subparsers.add_parser('set-config');
    from_config_parser = subparsers.add_parser('from-config');
    raw_parser.add_argument("-t", "--image_time", type=positive_int, help="The time in milliseconds that each image will persist")
    raw_parser.add_argument("--randomize", help="Randomize viewing order", action="store_true")
    raw_parser.add_argument("--no-video", help="Skip over videos", action="store_true")
    raw_parser.add_argument("--no-gif", help="Skip over gifs", action="store_true")
    raw_parser.add_argument("--mute", help="Disable video audio", action="store_true")
    raw_parser.add_argument("paths", nargs="*", help="A path for the screensaver to show media of")
    args = parser.parse_args()
    match args.command:
        case "from-config": screensaver_from_config.main()
        case "set-config": screensaver_options_gui.main()
        case "raw": 
            paths = args.paths or [os.getcwd()]
            screensaver_raw.main(paths, args.image_time, args.randomize, args.no_video, args.no_gif, args.mute)

