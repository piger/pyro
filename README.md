# PyRo

A prototype roguelike in Python, using libtcod.

This is an experiment aimed to practice a Entity-Component-System.

## Install

``` shell
brew install libtcod
virtualenv venv
. ./venv/bin/activate
python setup.py install
```

Then run `pyro`.

### pyenv

to avoid reinstalling python3:

``` shell
ln -fs /usr/local/opt/python/libexec ~/.pyenv/versions/3.7.1
```
