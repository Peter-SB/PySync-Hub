from app.services.setlist_import_service import SetlistImportService


def test_parse_setlist_extracts_artist_track():
    raw_text = (
        "\t\u2022\t11:26 - Wilkinson & Sub Focus ft. Tom Cane - Illuminate\n"
        "28:30 Sub Focus \u2013 X-Ray (Metrik Remix) \n"
        "[24:45] Barbatuques - Baian\u00e1 (ID Remix) [MR BONGO] "
    )
    expected = [
        {"artist": "Wilkinson & Sub Focus ft. Tom Cane", "track": "Illuminate"},
        {"artist": "Sub Focus", "track": "X-Ray (Metrik Remix)"},
        {"artist": "Barbatuques", "track": "Baian\u00e1 (ID Remix) [MR BONGO]"},
    ]

    assert SetlistImportService.parse_setlist(raw_text) == expected
