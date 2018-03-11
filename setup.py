from setuptools import setup, find_packages
from os.path import join, dirname

from channels_presence2 import __version__ as version

setup(
	name='django-channels-presence2',
	version=version,
	packages=find_packages(),
	author='acrius',
	author_email='acrius@mail.ru',
	url='https://github.com/acrius/django-channels-presence2',
	description='Simple presence boilerplate for django-channels 2 and channel redis backend.',
	license='MIT',
	keywords='',
	long_description=open(join(dirname(__file__), 'README.MD')).read(),
	include_package_data=True,
	include_packages_data=True,
	install_requires=[]
)
