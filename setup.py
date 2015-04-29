# from distutils.core import setup
from setuptools import setup

setup(
    name='vk-music',
    version='1.2.1',
    packages=['vk_music'],
    install_requires=[
        "progressbar==2.3",
        "six==1.9.0",
    ],
    entry_points={
        'console_scripts': [
            'vk_music = vk_music.__main__:main',
        ]
    },
    url='https://github.com/sashasimkin/vk_music',
    license='MIT',
    author='Alex Simkin',
    author_email='sashasimkin@gmail.com',
    description='Synchronize music with vk.com',

    keywords=['vk.com', 'downloading', 'script'],
    classifiers=[]
)
