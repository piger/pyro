import time
import logging
import pdb
import sys
import traceback
import click
from .game import Game


logger = logging.getLogger()


def validate_size(ctx, param, value):
    try:
        w, h = list(map(int, value.split("x", 1)))
        return (w, h)
    except ValueError:
        raise click.BadParameter("Size must be in format WxH (e.g. 100x40)")


@click.command()
@click.option("--seed", "-s", type=click.INT, help="Specify random seed")
@click.option(
    "--window",
    metavar="SIZE",
    default="100x40",
    callback=validate_size,
    help="Specify window size",
    show_default=True,
)
@click.option(
    "--size",
    "-S",
    metavar="SIZE",
    default="80x60",
    callback=validate_size,
    help="Specify map size",
    show_default=True,
)
@click.option("--debug", "-D", is_flag=True, help="Enable DEBUG features")
@click.option(
    "--font", "-f", default="mononoki_16-19.png", help="Specify a custom font", show_default=True
)
@click.option("--log-level", "log_level", default="INFO")
@click.option(
    "--algo",
    "-a",
    type=click.Choice(["bsp", "tunneling"]),
    default="bsp",
    help="Specify the dungeon generation algorithm",
    show_default=True,
)
def main(seed, size, window, debug, font, log_level, algo):
    if seed is None:
        seed = int(time.time())

    width, height = size
    win_width, win_height = window
    game = Game(seed, width, height, font, win_width, win_height)
    game.dungeon_algorithm = algo
    game.init_game()

    logging.basicConfig(
        format="[%(levelname)s] %(asctime)s (%(module)s.%(funcName)s:%(lineno)d) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_level == "INFO":
        logger.setLevel(logging.INFO)
    elif log_level == "DEBUG":
        logger.setLevel(logging.DEBUG)

    if debug:
        game.DEBUG = True
        logger.setLevel(logging.DEBUG)

    game.game_loop()


def run():
    try:
        main()
    except Exception as ex:
        extype, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
