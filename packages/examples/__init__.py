from .fmt import Fmt_10_2_1, Fmt_11_0_2
from .catch2 import Catch2_v3_5_4, Catch2_v3_7_1

releases = {
    'releaseA': {
        'tobuild': {
            'fmt': Fmt_10_2_1,
            'catch2': Catch2_v3_5_4},
        'depends': {
            'fmt': ['catch2'],  # if fmt depends on catch2, add it here
            'catch2': []
        }
    },

    'releaseB': {
        'fmt': Fmt_11_0_2,
        'catch2': Catch2_v3_7_1
    },

    'releaseC': {
        'fmt': Fmt_11_0_2,
        'catch2': Catch2_v3_5_4
    }
}
