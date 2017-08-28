import time
from optparse import OptionParser
from pyro.game import Game
import better_exceptions


def main():
    parser = OptionParser()
    parser.add_option('--seed', '-s')
    parser.add_option('--width', '-W', type=int, default=80)
    parser.add_option('--height', '-H', type=int, default=60)
    parser.add_option('--debug')
    (opts, _) = parser.parse_args()
    if opts.seed is None:
        seed = int(time.time())
    else:
        seed = int(opts.seed)

    game = Game(seed, opts.width, opts.height)
    game.init_game()

    if opts.debug:
        game.DEBUG = True

    game.game_loop()


if __name__ == '__main__':
    main()
