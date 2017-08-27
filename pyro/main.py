import time
from optparse import OptionParser
from pyro.game import Game


def main():
    parser = OptionParser()
    parser.add_option('--seed', '-s')
    opts, args = parser.parse_args()
    if opts.seed is None:
        seed = int(time.time())
    else:
        seed = opts.seed

    game = Game(seed)
    game.init_game()
    game.game_loop()


if __name__ == '__main__':
    main()
