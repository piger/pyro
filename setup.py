from setuptools import setup, find_packages

setup(
    name='pyro',
    version='0.1',
    description='Roguelike game',
    author='Daniel Kertesz',
    author_email='daniel@spatof.org',
    # install_requires=[
    #     'tdl==4.1.0',
    #     'noise==1.2.2',
    #     'click==6.7',
    #     'enum34==1.1.6',
    #     'better_exceptions',
    # ],
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pyro = pyro.main:main',
            'char-finder = pyro.char_finder:char_finder',
        ]
    }
)
