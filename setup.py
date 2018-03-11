from distutils.core import setup

from .channels_presence2 import __version__

setup(
	name='django-channels-presence2',
	packages=['channel_presence2'],
	version=__version__,
	description='Simple presence boilerplate for django-channels 2 and channel redis backend.',
	author='acrius',
	author_email='acrius@mail.ru',
	url='https://github.com/acrius/django-channels-presence2',
	keywords=['django', 'channels', 'presence'],  # arbitrary keywords
	classifiers=[],
)
