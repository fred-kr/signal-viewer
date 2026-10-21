"""
Names of the columns the data layer adds to every section frame, and the combo box sentinel for "no selection".

`RESERVED_COLUMN_NAMES` are refused as signal or info column because they would collide with those added columns.
"""

COMBO_BOX_NO_SELECTION = "<No Selection>"
INDEX_COL = "index"
SECTION_INDEX_COL = "section_index"
IS_PEAK_COL = "is_peak"
IS_MANUAL_COL = "is_manual"
RESERVED_COLUMN_NAMES = frozenset([COMBO_BOX_NO_SELECTION, INDEX_COL, SECTION_INDEX_COL, IS_PEAK_COL, IS_MANUAL_COL])
