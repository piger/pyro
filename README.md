# PyRo

A prototype roguelike in Python, using libtcod.

This is an experiment aimed to practice a Entity-Component-System.

## Install

First install [poetry](https://github.com/sdispater/poetry); the installer for poetry is smart
enough to install it in a non-system wide location.

Then:

``` shell
brew install libtcod
cd pyro
poetry install
```

Then run `poetry run pyro`.

### pyenv

NOTE: this is relevant only if you use pyenv.

To avoid reinstalling python3:

``` shell
ln -fs /usr/local/opt/python/libexec ~/.pyenv/versions/3.7.1
```

## Credits

Monster descriptions come from [d20PFSRD](http://www.d20pfsrd.com/).
