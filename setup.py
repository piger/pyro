from setuptools import setup, find_packages

setup(
    name='pyro',
    version='0.1',
    description='Roguelike game',
    author='Daniel Kertesz',
    author_email='daniel@spatof.org',
    install_requires=[
        'tdl==4.1.0',
    ],
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pyro = pyro.main:main',
        ]
    }
)
