import typing as t

COMBO_BOX_NO_SELECTION: t.Final = "<Not Set>"
INDEX_COL: t.Final = "index"
SECTION_INDEX_COL: t.Final = "section_index"
IS_PEAK_COL: t.Final = "is_peak"
IS_MANUAL_COL: t.Final = "is_manual"
RESERVED_COLUMN_NAMES: t.Final = frozenset(
    [COMBO_BOX_NO_SELECTION, INDEX_COL, SECTION_INDEX_COL, IS_PEAK_COL, IS_MANUAL_COL]
)
