import os
from setuptools import setup, find_namespace_packages

def get_version():
    """Get version from __version__.py"""
    version_file = os.path.join(os.path.dirname(__file__), 'endabyss', '__version__.py')
    version = {}
    with open(version_file, 'r', encoding='utf-8') as f:
        exec(f.read(), version)
    return version['__version__']

setup(
    name="endabyss",
    version=get_version(),
    description="Red Teaming and Web Bug Bounty Fast Endpoint Discovery Tool",
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type="text/markdown",
    author="arrester",
    author_email="arresterloyal@gmail.com",
    url="https://github.com/arrester/endabyss",
    packages=find_namespace_packages(include=['endabyss*']),
    package_data={
        'endabyss': ['core/config/*.yaml'],
    },
    include_package_data=True,
    install_requires=[
        'rich>=13.7.0',
        'aiohttp>=3.9.1',
        'beautifulsoup4>=4.12.2',
        'dnspython>=2.4.2',
        'pyyaml>=6.0.1',
        'jsbeautifier>=1.14.0',
        'playwright>=1.40.0',
        'requests>=2.32.0',
        'setuptools>=78.1.1'
    ],
    entry_points={
        'console_scripts': [
            'endabyss=endabyss.__main__:run_main',
        ],
    },
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Topic :: Security',
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.13',
        'Operating System :: OS Independent',
    ],
    keywords='security, endpoint discovery, bug bounty, red team, web security, crawling',
    project_urls={
        'Bug Reports': 'https://github.com/arrester/endabyss/issues',
        'Source': 'https://github.com/arrester/endabyss',
        'Documentation': 'https://github.com/arrester/endabyss#readme',
    },
)

