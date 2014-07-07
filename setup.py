from distutils.core import setup

setup(
    name='vk-music',
    version='1.0.0',
    packages=['vk_music'],
    install_requires=[
        "progressbar",
    ],
    entry_points={
        'console_scripts': [
            'vk_music = vk_music.main:main',
        ]
    },
    url='https://github.com/sashasimkin/vk_music',
    license='MIT',
    author='sashasimkin',
    author_email='sashasimkin@gmail.com',
    description='Synchronize music with vk.com',

    keywords=['vk.com', 'downloading', 'script'],
    classifiers=[]
)
