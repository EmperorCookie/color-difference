from pprint import pformat
import argparse
import logging
import sys
import time

from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import sRGBColor, LabColor, HSVColor
from colormath.color_conversions import convert_color

# Discord colors
DISCORD_LIGHT_COLORS = \
[
    "000000", # Light mode text color
    "FFFFFF", # Light mode chat area
    "F2F3F5", # Light mode user bar
]
DISCORD_DARK_COLORS = \
[
    "DCDDDE", # Dark mode text color
    "36393F", # Dark mode chat area
    "2F3136", # Dark mode user bar
]

# Default roles colors
DISCORD_ROLE_COLORS = \
[
    "99AAB5", # Default role color
    "00C09A", # Light blueish green
    "008369", # Dark blueish green
    "00D166", # Light green
    "008E44", # Dark green
    "0099E1", # Light blue
    "006798", # Dark blue
    "A652BB", # Light purple
    "7A2F8F", # Dark purple
    "FD0061", # Light pink
    "BC0057", # Dark pink
    "F8C300", # Light yellow
    "CC7900", # Dark yellow
    "F93A2F", # Light red
    "A62019", # Dark red
    "91A6A6", # Light blueish gray
    "969C9F", # Gray
    "597E8D", # Medium blueish gray
    "4E6F7B", # Dark blueish gray
]

# Color utils
def rgb_to_lab(r, g, b, upscaled = True):
    return convert_color(sRGBColor(r, g, b, upscaled), LabColor)

def hex_to_lab(hex):
    return convert_color(sRGBColor.new_from_rgb_hex(hex), LabColor)

def hex_to_hsv(hex):
    return convert_color(sRGBColor.new_from_rgb_hex(hex), HSVColor)

def lab_to_hex(lab):
    return convert_color(lab, sRGBColor).get_rgb_hex()[1:].upper()

def main(args):
    
    # Setup logging
    logger = logging.getLogger(__name__)
    logger.setLevel(args.verbosity)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(args.verbosity)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Construct list of colors to avoid
    avoids = [] if args.avoid is None else args.avoid
    if args.discordLightModeColors:
        avoids.extend(DISCORD_LIGHT_COLORS)
    if args.discordDarkModeColors:
        avoids.extend(DISCORD_DARK_COLORS)
    if args.discordRoleColors:
        avoids.extend(DISCORD_ROLE_COLORS)
    logger.debug(f"Final avoids: {avoids}")

    # Brute force color diff
    r = 255
    g = 255
    b = 255
    colors = []
    colorCount = -(-255 // args.step) ** 3
    logger.info(f"Looping through {colorCount} colors.")
    colorsChecked = 0
    t = time.time() + 1
    while True:

        # Construct color
        colorRgb = sRGBColor(r, g, b, True)
        colorHex = colorRgb.get_rgb_hex()[1:].upper()
        colorLab = convert_color(colorRgb, LabColor)

        # Check color
        logger.debug(f"Checking color {colorHex}")
        far = True
        for avoidHex in avoids:
            avoidLab = hex_to_lab(avoidHex)
            diff = delta_e_cie2000(colorLab, avoidLab)
            if diff < args.gap:
                logger.debug(f"Collides with color {avoidHex}")
                far = False
                break
        
        # Add far colors to list
        if far:
            logger.info(f"Valid color found {colorHex}")
            avoids.append(colorHex)
            colors.append(colorHex)

        b -= args.step
        if b < 0:
            b = 255
            g -= args.step
            if g < 0:
                g = 255
                r -= args.step
                if r < 0:
                    break
        colorsChecked += 1
        nt = time.time()
        if nt >= t:
            logger.info(f"Checked {colorsChecked}/{colorCount} colors")
            t = nt + 1

    colorString = "\n".join(sorted(colors, key = lambda x: hex_to_hsv(x).hsv_h))
    logger.info(f"Valid colors:\n{colorString}")

def parse_args(argv):

    # Log levels
    logLevels = \
    {
        "notset": logging.NOTSET,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }

    # Argument parser
    parser = argparse.ArgumentParser(
        description = "Finds a set of maximally dissimilar colors given a set of colors to avoid."
    )

    # Add arguments
    parser.add_argument(
        "-v", "--verbosity",
        help = "Sets the verbosity.",
        choices = logLevels.keys(),
        type = str,
        default = "info"
    )
    parser.add_argument(
        "-l", "--discordLightModeColors",
        help = "Avoids the Discord base background and text colors for light mode.",
        action = "store_true"
    )
    parser.add_argument(
        "-d", "--discordDarkModeColors",
        help = "Avoids the Discord base background and text colors for dark mode.",
        action = "store_true"
    )
    parser.add_argument(
        "-r", "--discordRoleColors",
        help = "Avoids the Discord base roles colors.",
        action = "store_true"
    )
    parser.add_argument(
        "-s", "--step",
        help = "RGB increment between each color. Default 4.",
        type = int,
        default = 4
    )
    parser.add_argument(
        "-a", "--avoid",
        help = "List of colors (hex values) to avoid.",
        type = str,
        nargs = "+"
    )
    parser.add_argument(
        "-g", "--gap",
        help = "A value from 0 to 100, where 100 means colors have to be completely dissimilar in order to match. Default 15.",
        type = float,
        default = "15"
    )

    # Parse arguments
    args = parser.parse_args(argv)
    args.verbosity = logLevels[args.verbosity]

    # Validate range
    if args.step < 1 or args.step > 255:
        raise ValueError(f"Step must be between 1 and 255.")

    # Validate avoid colors
    if args.avoid:
        for color in args.avoid:
            if len(color) != 6 or not all([c in "0123456789ABCDEF" for c in color.upper()]):
                raise ValueError(f"Invalid color hex '{color}'.")

    # Done
    return args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    sys.exit(main(args))
