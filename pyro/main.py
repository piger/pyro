import click
import time
from pyro.game import Game
import better_exceptions


@click.command()
@click.option('--seed', '-s', type=click.INT, help="Specify random seed")
@click.option('--size', '-S', default='80x60', help="Specify map size (i.e. 80x100)")
@click.option('--debug', '-D', is_flag=True)
@click.option('--font', '-f', default='consolas10x10_gs_tc.png', help="Specify the font")
def main(seed, size, debug, font):
    if seed is None:
        seed = int(time.time())

    width, height = [int(x) for x in size.split("x")]
    game = Game(seed, width, height, font)
    game.init_game()

    if debug:
        game.DEBUG = True

    game.game_loop()
