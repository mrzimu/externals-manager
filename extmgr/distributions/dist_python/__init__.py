from . import boss_externals
from . import examples
from extmgr.core import Executor

distributions = [
    {  # local720
        'name': 'local720',
        'packages': [('BesAlist', '2024.12.08'),
                     ('BesDIM', 'v20r20'),
                     ('BesGDML', '2.8.1'),
                     ('BesGeant4', 'v10.7.2'),
                     ('CERNLIB', '2024.06.12.0'),
                     ('Gaudi', 'v38r2')],
        'dependencies': {'BesGDML': ['BesGeant4']}
    },

    {  # releaseA
        'name': 'releaseA',
        'packages': [('fmt', '11.0.2'),
                     ('Catch2', 'v3.7.1')]
    },

    {  # releaseB
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
