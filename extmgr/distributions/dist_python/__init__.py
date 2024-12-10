from . import boss_externals
from . import examples
from extmgr.core import Executor

distributions = [
    # lcg-externals
    {
        'name': 'local-lcg',
        'packages': [('AIDA', '3.2.1'),
                     ('Boost', '1.85.0'),
                     ('Catch2', '2.13.9'),
                     ('CLHEP', '2.4.7.1'),
                     ('cppgsl', '3.1.0'),
                     ('HepPDT', '2.06.01'),
                     ('vdt', '0.4.4'),
                     ('root', 'v6.32.02'),
                     ('rangev3', '0.11.0')],
        'dependencies': {'AIDA': ['Boost'],
                         'CLHEP': ['cppgsl'],
                         'root': ['AIDA', 'CLHEP', 'HepPDT', 'vdt', 'Boost', 'rangev3']}

    },

    # local720
    {
        'name': 'local720',
        'packages': [('BesAlist', '2024.12.08'),
                     ('BesDIM', 'v20r20'),
                     ('BesGDML', '2.8.1'),
                     ('BesGeant4', 'v10.7.2'),
                     ('CERNLIB', '2024.06.12.0'),
                     ('Gaudi', 'v38r2')],
        'dependencies': {'BesGDML': ['BesGeant4']}
    },

    # releaseA
    {
        'name': 'releaseA',
        'packages': [('fmt', '11.0.2'),
                     ('Catch2', 'v3.7.1')]
    },

    # releaseB
    {
        'name': 'releaseB',
        'packages': [('fmt', '10.2.1'),
                     ('Catch2', 'v3.5.4')],
        'dependencies': {'fmt': ['Catch2']}
    }
]

dist_executor = Executor()
# dist_executor.update_packages()


for dist in distributions:
    dist_executor.register_distribution(**dist)
