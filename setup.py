import os
from setuptools import setup, find_packages

install_requires = [
    'Django>=3.0',
    'django-rq',
    'rq-scheduler',
    'psutil',
    'jsonpatch',
    'setproctitle',
    'mce-django-app@git+https://github.com/multi-cloud-explorer/mce-django-app.git@master#egg=mce_django_app',
    'mce-lib-azure@git+https://github.com/multi-cloud-explorer/mce-lib-azure.git@master#egg=mce_lib_azure',
]

tests_requires = [
    'psycopg2-binary',
    'pytest>=5.4.1',
    'pytest-django-rq',
    'pytest-cov',
    'pytest-pep8',
    'pytest-django',
    'pytest-timeout',
    'django-dynamic-fixture',
    'pytest-instafail',
    'curlify',
    'factory-boy',
    'bandit',
    'flake8',
    'coverage',
    'responses',
    'freezegun',
    'django-environ',
    'django-filter',
    'django-select2',
    'django-redis',
    'django-daterangefilter',
]

dev_requires = [
    'pylint',
    'ipython',
    'autopep8',
    'black',
    'wheel',
]

extras_requires = {
    'tests': tests_requires,
    'dev': dev_requires,
}

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mce-tasks-rq',
    version="0.1.0",
    description='Django RQ Tasks for Multi Cloud Explorer',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/multi-cloud-explorer/mce-tasks-rq.git',
    license='GPLv3+',
    packages=find_packages(exclude=("tests",)),
    include_package_data=False, 
    tests_require=tests_requires,
    install_requires=install_requires,
    extras_require=extras_requires,
    test_suite='tests',
    zip_safe=False,
    author='Stephane RAULT',
    author_email="stephane.rault@radicalspam.org",
    python_requires='>=3.7',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
)
