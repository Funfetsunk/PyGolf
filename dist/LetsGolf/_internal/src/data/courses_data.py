"""
Course data — Greenfields Golf Club, Par 72.

Grid: 48 cols × 36 rows. 1 tile = 10 yards.
Par 3 × 4: H3, H7, H11, H15
Par 4 × 10: H1, H4, H5, H8, H9, H10, H13, H14, H16, H18
Par 5 × 4: H2, H6, H12, H17
"""

from src.course.course import Course
from src.data._hole_factory import build_hole


def _h(number, par, yardage, tee, pin, fw, feats=None):
    return build_hole(number, par, yardage, tee, pin, fw, feats)


def make_greenfields_course() -> Course:
    """Greenfields Golf Club — Par 72, 5,900 yds. Parkland intro. Dominant hazard: bunkers."""
    holes = [
        # H1 — NS, P4, 310 — wide fairway, two bunker pairs flanking approach
        _h(1, 4, 300, (23,33), (23,4), [(5,32,18,27)],
           [('bunker',7,10,13,17), ('bunker',7,10,28,32),
            ('bunker',18,21,13,17), ('bunker',18,21,28,32)]),

        # H2 — DR dogleg right, P5, 380 — trees and bunker at bend
        _h(2, 5, 450, (10,33), (36,4), [(18,32,6,15),(5,20,30,42)],
           [('trees',18,32,16,20), ('bunker',16,21,16,20), ('bunker',6,9,33,37)]),

        # H3 — NS, P3, 155 — bunker-ringed green, no water
        _h(3, 3, 150, (23,27), (23,7), [(9,26,19,27)],
           [('bunker',4,10,13,18), ('bunker',4,10,28,33), ('bunker',10,13,19,27)]),

        # H4 — NSo offset (tee left, pin right), P4, 315 — diagonal fairway
        _h(4, 4, 305, (15,33), (30,4), [(5,20,18,28),(19,32,10,23)],
           [('bunker',6,9,29,34), ('bunker',20,24,10,14)]),

        # H5 — NS, P4, 330 — water crosses full fairway mid-hole
        _h(5, 4, 320, (23,33), (23,4), [(5,17,18,27),(19,32,18,27)],
           [('water',17,19,10,37), ('bunker',6,9,13,17), ('bunker',6,9,28,32)]),

        # H6 — DL dogleg left, P5, 370 — water at corner
        _h(6, 5, 450, (36,33), (10,4), [(18,32,30,40),(5,20,7,32)],
           [('water',14,20,27,33), ('bunker',13,17,27,32), ('bunker',6,9,4,8)]),

        # H7 — NE diagonal, P3, 160 — island green, water both sides (no fairway)
        _h(7, 3, 150, (8,28), (38,7), [],
           [('water',3,26,2,34), ('water',3,26,40,45)]),

        # H8 — NS, P4, 335 — bunker gauntlet (three pairs)
        _h(8, 4, 325, (23,33), (23,4), [(5,32,19,27)],
           [('bunker',7,11,14,18), ('bunker',7,11,28,32),
            ('bunker',14,18,14,18), ('bunker',14,18,28,32),
            ('bunker',21,25,14,18), ('bunker',21,25,28,32)]),

        # H9 — NW diagonal, P4, 355 — water hugs left, deep rough right
        _h(9, 4, 345, (38,33), (10,4), [(19,32,32,41),(5,20,7,34)],
           [('water',3,22,2,5), ('deep_rough',3,26,38,42), ('bunker',6,9,4,8)]),

        # H10 — NSo (tee left, pin offset), P4, 320 — water right, trees left
        _h(10, 4, 315, (18,33), (18,4), [(5,32,14,23)],
           [('water',4,32,27,45), ('bunker',5,9,9,13)]),

        # H11 — NS compact, P3, 145 — three bunkers, smallest green
        _h(11, 3, 150, (23,24), (23,8), [(9,23,20,26)],
           [('bunker',5,11,14,19), ('bunker',5,11,27,32), ('bunker',3,7,20,26)]),

        # H12 — NE diagonal, P5, 405 — three-segment fairway, central bunker splits
        _h(12, 5, 450, (8,33), (40,4), [(20,32,5,16),(10,22,14,30),(4,12,28,44)],
           [('bunker',17,23,19,25), ('bunker',5,9,41,45), ('trees',5,9,2,4)]),

        # H13 — DR dogleg right, P4, 330 — trees at bend, water right of green
        _h(13, 4, 325, (10,33), (36,4), [(18,32,6,15),(5,20,28,42)],
           [('trees',18,32,16,20), ('bunker',14,20,16,22),
            ('water',3,8,33,45), ('bunker',5,9,29,33)]),

        # H14 — NS narrow, P4, 325 — deep rough squeezes mid-fairway
        _h(14, 4, 320, (23,33), (23,4), [(5,32,20,26)],
           [('deep_rough',5,32,17,19), ('deep_rough',5,32,27,29),
            ('bunker',6,9,14,19), ('bunker',6,9,27,32)]),

        # H15 — NS long, P3, 185 — wide corridor, bunkers flank green
        _h(15, 3, 175, (23,30), (23,6), [(8,29,18,28)],
           [('bunker',3,9,13,17), ('bunker',3,9,29,33)]),

        # H16 — NSo (tee right), P4, 345 — water left of green, bunker right
        _h(16, 4, 340, (30,33), (16,4), [(5,32,12,22),(5,32,27,33)],
           [('water',3,10,2,11), ('bunker',6,9,23,28), ('bunker',16,19,8,12)]),

        # H17 — NW diagonal, P5, 400 — three-segment sweeping par 5
        _h(17, 5, 450, (40,33), (8,4), [(22,32,34,43),(8,24,16,36),(4,10,4,18)],
           [('bunker',19,24,24,30), ('bunker',3,9,5,9), ('water',3,8,40,45)]),

        # H18 — NS closing, P4, 385 — water both sides of green approach
        _h(18, 4, 380, (23,33), (23,4), [(5,32,18,27)],
           [('water',2,9,2,15), ('water',2,9,30,45),
            ('bunker',10,14,14,17), ('bunker',10,14,28,31)]),
    ]
    return Course(name="Greenfields Golf Club", holes=holes)
