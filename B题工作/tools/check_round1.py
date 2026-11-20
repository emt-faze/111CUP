"""Reproduce the first-round mathematical checks on synthetic cases only."""

from fractions import Fraction as F
from itertools import product
import math


def cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def convex_hull(points):
    ordered = sorted(set(points))

    def half(sequence):
        chain = []
        for point in sequence:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], point) <= 0:
                chain.pop()
            chain.append(point)
        return chain[:-1]

    return half(ordered) + half(reversed(ordered))


def segment_hits_box(camera, target, bounds):
    lo, hi = F(0), F(1)
    for start, end, (left, right) in zip(camera, target, bounds, strict=True):
        direction = end - start
        if direction == 0:
            if not left <= start <= right:
                return False
            continue
        times = sorted((F(left - start) / direction, F(right - start) / direction))
        lo, hi = max(lo, times[0]), min(hi, times[1])
        if lo > hi:
            return False
    return True


def check_shadows():
    corners = tuple(product((2, 4), (1, 3)))
    bounds = ((2, 4), (1, 3), (0, 4))
    camera_z, target_z = 2, 8
    scale = F(target_z - camera_z, target_z - bounds[2][1])
    samples = [F(k, 2) for k in range(-8, 17)]
    comparisons = 0
    for ux, uy in ((8, 6), (3, 2), (2, 1)):
        extended = [(ux + scale * (x - ux), uy + scale * (y - uy)) for x, y in corners]
        hull = convex_hull([*corners, *extended])
        edges = list(zip(hull, hull[1:] + hull[:1]))
        for point in product(samples, repeat=2):
            planar = all(cross(a, b, point) >= 0 for a, b in edges)
            spatial = segment_hits_box((*point, camera_z), (ux, uy, target_z), bounds)
            assert planar == spatial, (point, ux, uy)
            comparisons += 1
    return comparisons


def check_boundary_examples():
    camera, target = (0, 0, 2), (10, 0, 12)
    assert segment_hits_box(camera, target, ((5, 6), (-1, 1), (0, 7)))
    assert not segment_hits_box(camera, target, ((5, 6), (-1, 1), (0, 6)))
    assert not segment_hits_box(camera, target, ((11, 12), (-1, 1), (0, 100)))
    assert 2 * F(5, 4) ** 2 > F(3, 2) ** 2  # Legal round corner inside the square offset.


def check_information():
    r1, r2, angle = 7.0, 11.0, math.radians(37)
    row1 = (0, 1 / r1)
    row2 = (-math.sin(angle) / r2, math.cos(angle) / r2)
    a = row1[0] ** 2 + row2[0] ** 2
    b = row1[0] * row1[1] + row2[0] * row2[1]
    c = row1[1] ** 2 + row2[1] ** 2
    trace_inverse = (a + c) / (a * c - b * b)
    expected = (r1 * r1 + r2 * r2) / math.sin(angle) ** 2
    assert math.isclose(trace_inverse, expected)


def check_clock_and_score():
    arrival, slew = (2, 5), (4, 1)
    start = max(a + g for a, g in zip(arrival, slew))
    end = start + 5
    assert (start, end, [end + g for g in slew]) == (6, 11, [15, 12])
    assert max(arrival) + max(slew) > start
    assert [s < 5 for s in (4.9, 5.0)] == [True, False]

    def score(starts):
        on_time = [s for s in starts if s is not None and 0 <= s <= 60]
        last = max(on_time) if len(on_time) == len(starts) else 60
        return F(len(on_time), len(starts)), last

    assert score([12, 25, None]) == (F(2, 3), 60)
    assert score([12, 25, 60]) == (F(1), 60)


def check_angle_wrap():
    def wrap(a):
        return (a + math.pi) % (2 * math.pi) - math.pi

    def bearing_error(a):
        # Rotate both the true line of sight and one fixed position-error sample.
        tx, ty = 10 * math.cos(a), 10 * math.sin(a)
        ex = 0.3 * math.cos(a) + 0.7 * math.sin(a)
        ey = 0.3 * math.sin(a) - 0.7 * math.cos(a)
        return wrap(math.atan2(ty - ey, tx - ex) - math.atan2(ty, tx))

    assert math.isclose(bearing_error(0), bearing_error(math.radians(179)), abs_tol=1e-14)
    assert wrap(math.pi) == -math.pi


if __name__ == "__main__":
    count = check_shadows()
    check_boundary_examples()
    check_information()
    check_clock_and_score()
    check_angle_wrap()
    print(f"{count} exact shadow comparisons passed")
    print("Boundary, precision, timing, scoring and angle checks passed")
