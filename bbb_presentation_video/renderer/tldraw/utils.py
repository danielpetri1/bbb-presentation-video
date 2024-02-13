# SPDX-FileCopyrightText: 2022 BigBlueButton Inc. and by respective authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import math
from enum import Enum
from math import floor, hypot, pi, sqrt, tau
from typing import Dict, List, Sequence, Tuple, TypeVar, Union

import attr
import cairo
import perfect_freehand

from bbb_presentation_video.events.helpers import Color, Position, Size, color_blend
from bbb_presentation_video.events.tldraw import StyleData
from bbb_presentation_video.renderer.tldraw import vec

DrawPoints = List[Union[Tuple[float, float], Tuple[float, float, float]]]

CANVAS: Color = Color.from_int(0xFAFAFA)

STICKY_TEXT_COLOR: Color = Color.from_int(0x0D0D0D)
STICKY_PADDING: float = 16.0


class SizeStyle(Enum):
    SMALL: str = "small"
    S: str = "s"
    MEDIUM: str = "medium"
    M: str = "m"
    LARGE: str = "large"
    L: str = "l"
    XL: str = "xl"


STROKE_WIDTHS: Dict[SizeStyle, float] = {
    SizeStyle.SMALL: 2.0,
    SizeStyle.S: 2.0,
    SizeStyle.MEDIUM: 3.5,
    SizeStyle.M: 3.5,
    SizeStyle.LARGE: 5.0,
    SizeStyle.L: 5.0,
    SizeStyle.XL: 6.5,
}

FONT_SIZES: Dict[SizeStyle, float] = {
    SizeStyle.SMALL: 28,
    SizeStyle.S: 26,
    SizeStyle.MEDIUM: 48,
    SizeStyle.M: 36,
    SizeStyle.LARGE: 96,
    SizeStyle.L: 54,
    SizeStyle.XL: 64,
}

STICKY_FONT_SIZES: Dict[SizeStyle, float] = {
    SizeStyle.SMALL: 24,
    SizeStyle.S: 24,
    SizeStyle.MEDIUM: 36,
    SizeStyle.M: 36,
    SizeStyle.LARGE: 48,
    SizeStyle.L: 48,
    SizeStyle.XL: 60,
}

LETTER_SPACING: float = -0.03  # em


class ColorStyle(Enum):
    WHITE: str = "white"
    LIGHT_GRAY: str = "lightGray"
    GRAY: str = "gray"
    GREY: str = "grey"
    BLACK: str = "black"
    GREEN: str = "green"
    LIGHT_GREEN: str = "light-green"
    CYAN: str = "cyan"
    BLUE: str = "blue"
    LIGHT_BLUE: str = "light-blue"
    INDIGO: str = "indigo"
    VIOLET: str = "violet"
    LIGHT_VIOLET: str = "light-violet"
    RED: str = "red"
    LIGHT_RED: str = "light-red"
    ORANGE: str = "orange"
    YELLOW: str = "yellow"
    SEMI: str = "semi"


COLORS: Dict[ColorStyle, Color] = {
    ColorStyle.WHITE: Color.from_int(0x1D1D1D),
    ColorStyle.LIGHT_GRAY: Color.from_int(0xC6CBD1),
    ColorStyle.GRAY: Color.from_int(0x788492),
    ColorStyle.GREY: Color.from_int(0x9EA6B0),
    ColorStyle.BLACK: Color.from_int(0x1D1D1D),
    ColorStyle.GREEN: Color.from_int(0x36B24D),
    ColorStyle.LIGHT_GREEN: Color.from_int(0x38B845),
    ColorStyle.CYAN: Color.from_int(0x0E98AD),
    ColorStyle.BLUE: Color.from_int(0x1C7ED6),
    ColorStyle.LIGHT_BLUE: Color.from_int(0x4099F5),
    ColorStyle.INDIGO: Color.from_int(0x4263EB),
    ColorStyle.VIOLET: Color.from_int(0x7746F1),
    ColorStyle.LIGHT_VIOLET: Color.from_int(0x9C1FBE),
    ColorStyle.RED: Color.from_int(0xFF2133),
    ColorStyle.LIGHT_RED: Color.from_int(0xFC7075),
    ColorStyle.ORANGE: Color.from_int(0xFF9433),
    ColorStyle.YELLOW: Color.from_int(0xFFC936),
    ColorStyle.SEMI: Color.from_int(0xF5F9F7),
}

HIGHLIGHT_COLORS: Dict[ColorStyle, Color] = {
    ColorStyle.BLACK: Color.from_int(0xFFF4A1),
    ColorStyle.GREY: Color.from_int(0xEDF7FA),
    ColorStyle.LIGHT_VIOLET: Color.from_int(0xFFD7FF),
    ColorStyle.VIOLET: Color.from_int(0xECD3FF),
    ColorStyle.BLUE: Color.from_int(0xB4E2FF),
    ColorStyle.LIGHT_BLUE: Color.from_int(0xA2FCFF),
    ColorStyle.YELLOW: Color.from_int(0xFFF4A1),
    ColorStyle.ORANGE: Color.from_int(0xFFE2B5),
    ColorStyle.GREEN: Color.from_int(0xA2FFEC),
    ColorStyle.LIGHT_GREEN: Color.from_int(0xCCFCC1),
    ColorStyle.LIGHT_RED: Color.from_int(0xFFD3DF),
    ColorStyle.RED: Color.from_int(0xFFCACD),
}


STICKY_FILLS: Dict[ColorStyle, Color] = dict(
    [
        (
            k,
            (
                Color.from_int(0xFFFFFF)
                if k is ColorStyle.WHITE
                else (
                    Color.from_int(0x3D3D3D)
                    if k is ColorStyle.BLACK
                    else color_blend(v, CANVAS, 0.45)
                )
            ),
        )
        for k, v in COLORS.items()
    ]
)

STROKES: Dict[ColorStyle, Color] = dict(
    [
        (k, Color.from_int(0x1D1D1D) if k is ColorStyle.WHITE else v)
        for k, v in COLORS.items()
    ]
)

FILLS: Dict[ColorStyle, Color] = dict(
    [
        (
            k,
            (
                Color.from_int(0xFEFEFE)
                if k is ColorStyle.WHITE
                else color_blend(v, CANVAS, 0.82)
            ),
        )
        for k, v in COLORS.items()
    ]
)


class DashStyle(Enum):
    DRAW: str = "draw"
    SOLID: str = "solid"
    DASHED: str = "dashed"
    DOTTED: str = "dotted"


class FontStyle(Enum):
    SCRIPT: str = "script"
    SANS: str = "sans"
    ERIF: str = "erif"  # Old tldraw versions had this spelling mistake
    SERIF: str = "serif"
    MONO: str = "mono"
    DRAW: str = "draw"


FONT_FACES: Dict[FontStyle, str] = {
    FontStyle.SCRIPT: "Caveat Brush",
    FontStyle.SANS: "Source Sans Pro",
    FontStyle.ERIF: "Crimson Pro",
    FontStyle.SERIF: "Crimson Pro",
    FontStyle.MONO: "Source Code Pro",
    FontStyle.DRAW: "Caveat Brush",
}


class AlignStyle(Enum):
    START: str = "start"
    MIDDLE: str = "middle"
    END: str = "end"
    JUSTIFY: str = "justify"


class FillStyle(Enum):
    NONE: str = "none"
    SEMI: str = "semi"
    SOLID: str = "solid"
    PATTERN: str = "pattern"


@attr.s(order=False, slots=True, auto_attribs=True)
class Style:
    color: ColorStyle = ColorStyle.BLACK
    size: SizeStyle = SizeStyle.SMALL
    dash: DashStyle = DashStyle.DRAW
    isFilled: bool = False
    isClosed: bool = False
    scale: float = 1
    font: FontStyle = FontStyle.SCRIPT
    textAlign: AlignStyle = AlignStyle.MIDDLE
    opacity: float = 1
    fill: FillStyle = FillStyle.NONE

    def update_from_data(self, data: StyleData) -> None:
        if "color" in data:
            self.color = ColorStyle(data["color"])
        if "size" in data:
            self.size = SizeStyle(data["size"])
        if "dash" in data:
            self.dash = DashStyle(data["dash"])
        if "isFilled" in data:
            self.isFilled = data["isFilled"]
        if "scale" in data:
            self.scale = data["scale"]
        if "font" in data:
            self.font = FontStyle(data["font"])
        if "textAlign" in data:
            self.textAlign = AlignStyle(data["textAlign"])
        if "opacity" in data:
            self.opacity = data["opacity"]

        # Tldraw v2 style props not present in v1
        if "isClosed" in data:
            self.isClosed = data["isClosed"]
        if "fill" in data:
            self.fill = FillStyle(data["fill"])
            if self.fill is not FillStyle.NONE:
                self.isFilled = True


class Decoration(Enum):
    ARROW: str = "arrow"
    BAR: str = "bar"
    DIAMOND: str = "diamond"
    DOT: str = "dot"
    INVERTED: str = "inverted"
    NONE: str = "none"
    SQUARE: str = "square"
    TRIANGLE: str = "triangle"


class SplineType(Enum):
    CUBIC: str = "cubic"
    LINE: str = "line"
    NONE: str = "none"


def perimeter_of_ellipse(rx: float, ry: float) -> float:
    """Find the approximate perimeter of an ellipse."""

    # Handle degenerate case where the "ellipse" is actually a line or a point
    if rx == 0:
        return 2 * ry
    elif ry == 0:
        return 2 * rx

    h = (rx - ry) ** 2 / (rx + ry) ** 2
    return pi * (rx + ry) * (1 + (3 * h) / (10 + sqrt(4 - 3 * h)))


def circle_from_three_points(
    A: Sequence[float], B: Sequence[float], C: Sequence[float]
) -> Tuple[Position, float]:
    """Get a circle from three points."""
    (x1, y1) = A
    (x2, y2) = B
    (x3, y3) = C

    a = x1 * (y2 - y3) - y1 * (x2 - x3) + x2 * y3 - x3 * y2

    b = (
        (x1 * x1 + y1 * y1) * (y3 - y2)
        + (x2 * x2 + y2 * y2) * (y1 - y3)
        + (x3 * x3 + y3 * y3) * (y2 - y1)
    )

    c = (
        (x1 * x1 + y1 * y1) * (x2 - x3)
        + (x2 * x2 + y2 * y2) * (x3 - x1)
        + (x3 * x3 + y3 * y3) * (x1 - x2)
    )

    x = -b / (2 * a)

    y = -c / (2 * a)

    return (Position(x, y), hypot(x - x1, y - y1))


def short_angle_dist(a0: float, a1: float) -> float:
    """Get the short angle distance between two angles."""
    max = math.pi * 2
    da = (a1 - a0) % max
    return ((2 * da) % max) - da


def lerp_angles(a0: float, a1: float, t: float) -> float:
    """Interpolate an angle between two angles."""
    return a0 + short_angle_dist(a0, a1) * t


def get_sweep(C: Sequence[float], A: Sequence[float], B: Sequence[float]) -> float:
    """Get the "sweep" or short distance between two points on a circle's perimeter."""
    return short_angle_dist(vec.angle(C, A), vec.angle(C, B))


def draw_stroke_points(
    points: DrawPoints, stroke_width: float, is_complete: bool
) -> List[perfect_freehand.types.StrokePoint]:
    return perfect_freehand.get_stroke_points(
        points,
        size=1 + stroke_width * 1.5,
        streamline=0.65,
        last=is_complete,
    )


def get_perfect_dash_props(
    length: float,
    stroke_width: float,
    style: DashStyle,
    snap: int = 1,
    outset: bool = True,
    length_ratio: float = 2,
) -> Tuple[List[float], float]:
    if style is DashStyle.DASHED:
        dash_length = stroke_width * length_ratio
        ratio = 1
        offset = dash_length / 2 if outset else 0
    elif style is DashStyle.DOTTED:
        dash_length = stroke_width / 100
        ratio = 100
        offset = 0
    else:
        return ([], 0)

    dashes = floor(length / dash_length / (2 * ratio))
    dashes -= dashes % snap
    dashes = max(dashes, 4)

    gap_length = max(
        dash_length,
        (length - dashes * dash_length) / (dashes if outset else dashes - 1),
    )

    return ([dash_length, gap_length], offset)


def bezier_quad_to_cube(
    qp0: Tuple[float, float], qp1: Tuple[float, float], qp2: Tuple[float, float]
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    return (
        vec.add(qp0, vec.mul(vec.sub(qp1, qp0), 2 / 3)),
        vec.add(qp2, vec.mul(vec.sub(qp1, qp2), 2 / 3)),
    )


def bezier_length(
    start: Position, control: Position, end: Position, num_segments: int = 10
) -> float:
    """Approximate the length of a cubic Bézier curve."""
    length = 0.0
    t_values = [i / num_segments for i in range(num_segments + 1)]
    last_point = start

    for t in t_values[1:]:
        # Calculate the next point on the curve
        x = (
            (1 - t) ** 3 * start.x
            + 3 * (1 - t) ** 2 * t * control.x
            + 3 * (1 - t) * t**2 * control.x
            + t**3 * end.x
        )
        y = (
            (1 - t) ** 3 * start.y
            + 3 * (1 - t) ** 2 * t * control.y
            + 3 * (1 - t) * t**2 * control.y
            + t**3 * end.y
        )
        next_point = Position(x, y)

        # Add the distance from the last point to the current point
        length += vec.dist(last_point, next_point)
        last_point = next_point

    return length


CairoSomeSurface = TypeVar("CairoSomeSurface", bound=cairo.Surface)


def rounded_rect(
    ctx: cairo.Context[CairoSomeSurface], size: Size, radius: float
) -> None:
    ctx.new_sub_path()
    ctx.arc(size.width - radius, radius, radius, -tau / 4, 0)
    ctx.arc(size.width - radius, size.height - radius, radius, 0, tau / 4)
    ctx.arc(radius, size.height - radius, radius, tau / 4, tau / 2)
    ctx.arc(radius, radius, radius, tau / 2, -tau / 4)
    ctx.close_path()


def draw_smooth_path(
    ctx: cairo.Context[CairoSomeSurface],
    points: Sequence[Tuple[float, float]],
    closed: bool = True,
) -> None:
    """Turn an array of points into a path of quadratic curves."""

    if len(points) < 1:
        return

    prev_point = points[0]
    if closed:
        prev_mid = vec.med(points[-1], prev_point)
    else:
        prev_mid = prev_point
    ctx.move_to(prev_mid[0], prev_mid[1])
    for point in points[1:]:
        mid = vec.med(prev_point, point)

        # Cairo can't render quadratic curves directly, need to convert to cubic curves.
        cp1, cp2 = bezier_quad_to_cube(prev_mid, prev_point, mid)
        ctx.curve_to(cp1[0], cp1[1], cp2[0], cp2[1], mid[0], mid[1])
        prev_point = point
        prev_mid = mid

    if closed:
        point = points[0]
        mid = vec.med(prev_point, point)
    else:
        point = points[-1]
        mid = point

    cp1, cp2 = bezier_quad_to_cube(prev_mid, prev_point, mid)
    ctx.curve_to(cp1[0], cp1[1], cp2[0], cp2[1], mid[0], mid[1])

    if closed:
        ctx.close_path()


def draw_smooth_stroke_point_path(
    ctx: cairo.Context[CairoSomeSurface],
    points: Sequence[perfect_freehand.types.StrokePoint],
    closed: bool = True,
) -> None:
    outline_points = list(map(lambda p: p["point"], points))
    draw_smooth_path(ctx, outline_points, closed)


def pattern_fill(fill: Color, opacity: float = 1) -> cairo.SurfacePattern:
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 8, 8)
    ctx = cairo.Context(surface)

    # Draw the hash pattern
    ctx.rectangle(0, 0, 8, 8)

    # Set the background to white
    ctx.set_source_rgba(1, 1, 1, opacity)
    ctx.fill_preserve()

    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    # Set the pattern fill color
    ctx.set_source_rgba(fill.r, fill.g, fill.b, opacity)

    # Draw the hash lines
    ctx.move_to(0.66, 2)
    ctx.line_to(2, 0.66)
    ctx.move_to(3.33, 4.66)
    ctx.line_to(4.66, 3.33)
    ctx.move_to(6, 7.33)
    ctx.line_to(7.33, 6)

    ctx.set_line_width(1)
    ctx.stroke()

    pattern = cairo.SurfacePattern(surface)
    pattern.set_extend(cairo.EXTEND_REPEAT)

    return pattern


def get_arc_length(C: Position, r: float, A: Position, B: Position) -> float:
    sweep = get_sweep(C, A, B)
    return r * tau * (sweep / tau)


def apply_geo_fill(
    ctx: cairo.Context[CairoSomeSurface], style: Style, opacity: float
) -> None:
    fill = FILLS[style.color]

    if style.fill is FillStyle.SEMI:
        fill = COLORS[ColorStyle.SEMI]
        ctx.set_source_rgba(fill.r, fill.g, fill.b, opacity)

    elif style.fill is FillStyle.PATTERN:
        fill = FILLS[style.color]
        pattern = pattern_fill(fill, opacity)
        ctx.set_source(pattern)
    else:
        ctx.set_source_rgba(fill.r, fill.g, fill.b, opacity)

    ctx.fill()
