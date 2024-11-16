from .bes_gdml import BesGDML_2_8_1
from .bes_geant4 import BesGeant4_10_7_2
from .bes_dim import BesDIM_v20r20
from .cernlib import Cernlib_2406120
from .gaudi import Gaudi_v38r2
from .bes_alist import BesAlist

releases = {
    'local720': {
        'tobuild': {
            'besalist': BesAlist,
            'besgdml': BesGDML_2_8_1,
            'besgeant4': BesGeant4_10_7_2,
            'besdim': BesDIM_v20r20,
            'cernlib': Cernlib_2406120,
            'gaudi': Gaudi_v38r2
        },

        'depends': {
            'besgdml': ['besgeant4']
        }
    }
}
