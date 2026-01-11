import pytest
from app.utils.tracklist_utils import *

example_artist_second = """
@22:10 Make it Pump - Culture Shock, Grafix
@59:33 The Days (Notion Remix)(1991 Bootleg) - Chrystal
"""

example_mixed_tracklist = """
0:12 Sub Focus - Ecuador
1:50 Marlon Hoffstadt - It's That Time (Dimension Remix)
45:57 Fred again.., Skepta, PlaqueBoyMax - Victory Lap (Sudley Bootleg)
3. 07:47– Adapter & FRANCO BA – Malfunktion
4. 10:10 – CamelPhat ft. Ali Love – Spektrum (Tharat Remix)
26:08 ID
31:14 Soichi Terada - Untitled (¥ record)
59:19 Gold Panda - Untitled1000
31:40 Spooky (Quinten 909 Extended Remix) - Dusty Springfield
34:10 - Babert - Time After Time (Extended Mix)
57:48 Fourward - How (Instrumental)
59:50 Wilkinson - Wash Away
1:01:20 Wilkinson & Sub Focus - Take It Up
 
12:20 : Tony Romera - 2009
15:00 to 18:00 : KH - Only Human samples
1:07:55 : ⣎⡇ꉺლ༽இ•̛)ྀ◞ ༎ຶ ༽ৣৢ؞ৢ؞ؖ ꉺლ - ཬɷԾㅍ ꉺლ༽༼இ•̛)ྀ◞ ༎ຶ ლ༽இ•̛)ྀ◞☼⃝◞⊖◟☼⃝ ◉፨∷▲∵⣎⡇ ⃝͢ oOo▲༎ຶ ༽ৣৢ؞ৢ؞ؙؖ⁽⁾ا⦁⁾⁽ؙۜؖء؞ૣ࿆˜☼⃝◞⊖◟☼⃝ ◉፨∷▲∵⣎⡇ ⃝͢ oOo▲
1:45:00 : Four Tet, Mala, Neneh Cherry - ID (unreleased) (thanks @tudor.incupa)
20:00 : Brandy & Monica - The Boy Is Mine + Fred Again - Hannah (the sun) (mixed)
[01:45] A Little Sound - Override [MINISTRY OF SOUND]
w/ Moko - Your Love (Culture Shock Remix) [MTA]
00:00 Sub Focus & Metrik – Trip (VIP) [Intro Edit]
22:50 John Summit & Sub Focus ft. Julia Church – Go Back (YDG Remix)
1:25:00 Sub Focus ft. AR/CO – Vibration (One More Time) (VIP)
•	00:10 - Avicii - Levels (1991 Remix)
•	w/ Benny L - Memories
•	35:16 - John Summit & HAYLA - Shiver (Cassian Remix / Andromedik Edit)
•	52:49 - ID - ID
43:37 - Sub Focus & Dimension - Desire w/ Subsonic - Ascend
"""

example_prefix_pairs = [
    # Simple timestamp (M:SS)
    ("0:12 Sub Focus - Ecuador", "Sub Focus - Ecuador"),
    # Simple timestamp (MM:SS)
    ("45:57 Fred again.., Skepta, PlaqueBoyMax - Victory Lap (Sudley Bootleg)", "Fred again.., Skepta, PlaqueBoyMax - Victory Lap (Sudley Bootleg)"),
    # Timestamp with dash after
    ("34:10 - Babert - Time After Time (Extended Mix)", "Babert - Time After Time (Extended Mix)"),
    # Timestamp with colon separator
    ("12:20 : Tony Romera - 2009", "Tony Romera - 2009"),
    # Long timestamp (H:MM:SS)
    ("1:01:20 Wilkinson & Sub Focus - Take It Up", "Wilkinson & Sub Focus - Take It Up"),
    # Long timestamp with colon separator
    ("1:45:00 : Four Tet, Mala, Neneh Cherry - ID (unreleased) (thanks @tudor.incupa)", "Four Tet, Mala, Neneh Cherry - ID (unreleased) (thanks @tudor.incupa)"),
    # Numbered list + timestamp
    ("3. 07:47- Adapter & FRANCO BA - Malfunktion", "Adapter & FRANCO BA - Malfunktion"),
    # Numbered list + timestamp + dash
    ("4. 10:10 - CamelPhat ft. Ali Love - Spektrum (Tharat Remix)", "CamelPhat ft. Ali Love - Spektrum (Tharat Remix)"),
    # Time range
    ("15:00 to 18:00 : KH - Only Human samples", "KH - Only Human samples"),
    # Bracketed timestamp
    ("[01:45] A Little Sound - Override [MINISTRY OF SOUND]", "A Little Sound - Override [MINISTRY OF SOUND]"),
    # Bullet + timestamp
    ("• 00:10 - Avicii - Levels (1991 Remix)", "Avicii - Levels (1991 Remix)"),
    # Bullet + w/
    ("• w/ Benny L - Memories", "w/ Benny L - Memories"),
    # Leading w/
    ("w/ Moko - Your Love (Culture Shock Remix) [MTA]", "w/ Moko - Your Love (Culture Shock Remix) [MTA]"),
    # Timestamp only, no artist yet
    ("26:08 ID", "ID"),
]

example_artist_track_pairs = [
    ("Sub Focus - Ecuador", "Sub Focus", "Ecuador"),
    ("Marlon Hoffstadt - It's That Time (Dimension Remix)", "Marlon Hoffstadt", "It's That Time (Dimension Remix)"),
    ("Fred again.., Skepta, PlaqueBoyMax - Victory Lap (Sudley Bootleg)", "Fred again.., Skepta, PlaqueBoyMax", "Victory Lap (Sudley Bootleg)"),
    ("Adapter & FRANCO BA - Malfunktion", "Adapter & FRANCO BA", "Malfunktion"),
    ("CamelPhat ft. Ali Love - Spektrum (Tharat Remix)", "CamelPhat ft. Ali Love", "Spektrum (Tharat Remix)"),
    ("ID", "ID", ""), # Edge case: no track name
    ("Soichi Terada - Untitled ( record)", "Soichi Terada", "Untitled ( record)"),
    ("Gold Panda - Untitled1000", "Gold Panda", "Untitled1000"),
    ("Spooky (Quinten 909 Extended Remix) - Dusty Springfield", "Spooky (Quinten 909 Extended Remix)", "Dusty Springfield"),
    ("Babert - Time After Time (Extended Mix)", "Babert", "Time After Time (Extended Mix)"),
    ("Fourward - How (Instrumental)", "Fourward", "How (Instrumental)"),
    ("Wilkinson - Wash Away", "Wilkinson", "Wash Away"),
    ("Wilkinson & Sub Focus - Take It Up", "Wilkinson & Sub Focus", "Take It Up"),
    ("Tony Romera - 2009", "Tony Romera", "2009"),
    ("KH - Only Human samples", "KH", "Only Human samples"),
    ("Four Tet, Mala, Neneh Cherry - ID (unreleased) (thanks @tudor.incupa)", "Four Tet, Mala, Neneh Cherry", "ID (unreleased) (thanks @tudor.incupa)"),
    ("Brandy & Monica - The Boy Is Mine + Fred Again - Hannah (the sun) (mixed)", "Brandy & Monica", "The Boy Is Mine + Fred Again - Hannah (the sun) (mixed)"), # Complex edge case, todo: come back to this
    ("A Little Sound - Override [MINISTRY OF SOUND]", "A Little Sound", "Override [MINISTRY OF SOUND]"),
    ("Moko - Your Love (Culture Shock Remix) [MTA]", "Moko", "Your Love (Culture Shock Remix) [MTA]"),
    ("Sub Focus & Metrik - Trip (VIP) [Intro Edit]", "Sub Focus & Metrik", "Trip (VIP) [Intro Edit]"),
    ("John Summit & Sub Focus ft. Julia Church - Go Back (YDG Remix)", "John Summit & Sub Focus ft. Julia Church", "Go Back (YDG Remix)"),
    ("Sub Focus ft. AR/CO - Vibration (One More Time) (VIP)", "Sub Focus ft. AR/CO", "Vibration (One More Time) (VIP)"),
    ("Avicii - Levels (1991 Remix)", "Avicii", "Levels (1991 Remix)"),
    ("", "", ""),
    ("Benny L - Memories", "Benny L", "Memories"),
    ("John Summit & HAYLA - Shiver (Cassian Remix / Andromedik Edit)", "John Summit & HAYLA", "Shiver (Cassian Remix / Andromedik Edit)"),
    ("ID - ID", "ID", "ID"),
    ("Sub Focus & Dimension - Desire", "Sub Focus & Dimension", "Desire"),
    ("Subsonic - Ascend", "Subsonic", "Ascend")
]


def test_clean_track_pipeline():
    split_track_list = split_tracks(example_mixed_tracklist)
    unicode_cleaned_tracks = [clean_track_unicode(track) for track in split_track_list]
    prefix_cleaned_tracks = [clean_track_prefix(track) for track in unicode_cleaned_tracks]
    print(prefix_cleaned_tracks)

def test_split_tracks():
    """ Text tracklist splitting of all cases. 
    - not including split lines for now
    - include "• " from "• w/ .." for now
    """
    split_tracklist = split_tracks(example_mixed_tracklist)
    print(split_tracklist)
    assert len(split_tracklist) == 30 

def test_split_tracks_when_multiple_in_line():
    """ Test splitting when multiple tracks are in one line. """
    examples_multiple_track_lines = "43:37 - Sub Focus & Dimension - Desire w/ Subsonic - Ascend"
    split_tracklist = split_tracks(examples_multiple_track_lines)
    assert len(split_tracklist) == 2 

def test_split_tracks_when_wslash_in_line():
    """ Test splitting when edgecase tracks in one line. """
    examples_single_track_lines = "•	w/ Benny L - Memories"
    split_tracklist = split_tracks(examples_single_track_lines)
    assert len(split_tracklist) == 1


def test_clean_track_prefix():
    """ Test removing timestamps and any other formatting data"""
    for prefix, expected in example_prefix_pairs:
        result = clean_track_prefix(prefix)
        assert result == expected, f"Failed on {prefix}: got {result}, expected {expected}"


def test_clean_track_unicode():
    """ Test cleaning unicode and mojibake """
    assert clean_track_unicode("Sub Focüs - Ecüador") == "Sub Focus - Ecuador"
    assert clean_track_unicode("Marlon Höffstadt - It's That Time") == "Marlon Hoffstadt - It's That Time"
    assert clean_track_unicode("3. 07:47– Adapter & FRANCO BA – Malfunktion") == "3. 07:47- Adapter & FRANCO BA - Malfunktion"
    assert clean_track_unicode("• w/ Benny L - Memories") == "w/ Benny L - Memories"


def test_is_unidentified_track():
    """ Test identifying unidentified tracks """
    assert is_unidentified_track("ID") == True
    assert is_unidentified_track("ID - ID") == True
    assert is_unidentified_track("Artistname1 - ID") == True
    assert is_unidentified_track("Artistname1 - ID plz help identify") == True
    assert is_unidentified_track("Four Tet, Mala, Neneh Cherry - ID (unreleased)") == True
    # assert is_unidentified_track("Four Tet, Mala - ID (ID Remix)") == True


    assert is_unidentified_track("Artistname2 - Untitled") == False
    assert is_unidentified_track("Artistname3 - Track 01") == False
    assert is_unidentified_track("Artistname4 - Song Name") == False
    assert is_unidentified_track("ArtistName5 - songname (ID remix)") == False
    assert is_unidentified_track("Untitled1000ID") == False