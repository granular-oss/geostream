from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip
from setuptools import find_packages, setup

__build__ = 0
__version__ = f'1.2.0.{__build__}'


pfile = Project(chdir=False).parsed_pipfile


setup(
    name='geostream',
    author='Donna Okazaki',
    author_email='donnaokazaki@granular.ag',
    version=__version__,
    python_requires='~=3.6',
    package_data={'geostream': ['py.typed']},
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=convert_deps_to_pip(pfile['packages'], r=False),
    tests_require=convert_deps_to_pip(pfile['dev-packages'], r=False),
    entry_points=dict(
        console_scripts=[
            'unpack_gjz = geostream.cli:cli'
        ]
    )
)
