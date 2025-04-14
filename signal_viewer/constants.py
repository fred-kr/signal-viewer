from typing import Final

COMBO_BOX_NO_SELECTION: Final = "<No Selection>"
INDEX_COL: Final = "index"
SECTION_INDEX_COL: Final = "section_index"
IS_PEAK_COL: Final = "is_peak"
IS_MANUAL_COL: Final = "is_manual"
RESERVED_COLUMN_NAMES: Final = frozenset(
    [COMBO_BOX_NO_SELECTION, INDEX_COL, SECTION_INDEX_COL, IS_PEAK_COL, IS_MANUAL_COL]
)
