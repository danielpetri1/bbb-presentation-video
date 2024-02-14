# SPDX-FileCopyrightText: 2022 BigBlueButton Inc. and by respective authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from math import hypot
from random import Random
from typing import List, TypeVar

import cairo
import perfect_freehand
from perfect_freehand.types import StrokePoint

from bbb_presentation_video.events.helpers import Position, Size
from bbb_presentation_video.renderer.tldraw import vec
from bbb_presentation_video.renderer.tldraw.shape import (
    Hexagon,
)
from bbb_presentation_video.renderer.tldraw.shape.text import finalize_v2_label
from bbb_presentation_video.renderer.tldraw.utils import (
    STROKE_WIDTHS,
    STROKES,
    DashStyle,
    apply_geo_fill,
    draw_smooth_path,
    draw_smooth_stroke_point_path,
    finalize_dash_geo,
    getPolygonVertices,
)


def hexagon_stroke_points(id: str, shape: Hexagon) -> List[StrokePoint]:
    random = Random(id)
    size = shape.size

    width = size.width
    height = size.height

    stroke_width = STROKE_WIDTHS[shape.style.size]

    width = max(0, shape.size.width)
    height = max(0, shape.size.height)

    sides = 6

    strokes = getPolygonVertices(width, height, sides)
    variation = stroke_width * 0.75

    v1 = (
        strokes[0][0].x + random.uniform(-variation, variation),
        strokes[0][0].y + random.uniform(-variation, variation),
    )

    v2 = (
        strokes[1][0].x + random.uniform(-variation, variation),
        strokes[1][0].y + random.uniform(-variation, variation),
    )

    v3 = (
        strokes[2][0].x + random.uniform(-variation, variation),
        strokes[2][0].y + random.uniform(-variation, variation),
    )

    v4 = (
        strokes[3][0].x + random.uniform(-variation, variation),
        strokes[3][0].y + random.uniform(-variation, variation),
    )

    v5 = (
        strokes[4][0].x + random.uniform(-variation, variation),
        strokes[4][0].y + random.uniform(-variation, variation),
    )

    v6 = (
        strokes[5][0].x + random.uniform(-variation, variation),
        strokes[5][0].y + random.uniform(-variation, variation),
    )

    # Which side to start drawing first
    rm = random.randrange(0, sides - 1)

    # Number of points per side
    # Insert each line by the corner radii and let the freehand algo
    # interpolate points for the corners.
    lines = [
        vec.points_between(v1, v2, 32),
        vec.points_between(v2, v3, 32),
        vec.points_between(v3, v4, 32),
        vec.points_between(v4, v5, 32),
        vec.points_between(v5, v6, 32),
        vec.points_between(v6, v1, 32),
    ]

    lines = lines[rm:] + lines[0:rm]
    points = [
        *lines[0],
        *lines[1],
        *lines[2],
        *lines[3],
        *lines[4],
        *lines[5],
        *lines[0],
    ]

    return perfect_freehand.get_stroke_points(
        points, size=stroke_width, streamline=0.3, last=True
    )


CairoSomeSurface = TypeVar("CairoSomeSurface", bound=cairo.Surface)


def draw_hexagon(ctx: cairo.Context[CairoSomeSurface], id: str, shape: Hexagon) -> None:
    style = shape.style

    stroke = STROKES[style.color]
    stroke_width = STROKE_WIDTHS[style.size]

    stroke_points = hexagon_stroke_points(id, shape)

    if style.isFilled:
        draw_smooth_stroke_point_path(ctx, stroke_points, closed=False)
        apply_geo_fill(ctx, style)

    stroke_outline_points = perfect_freehand.get_stroke_outline_points(
        stroke_points,
        size=stroke_width,
        thinning=0.65,
        smoothing=1,
        simulate_pressure=False,
        last=True,
    )
    draw_smooth_path(ctx, stroke_outline_points, closed=True)

    ctx.set_source_rgba(stroke.r, stroke.g, stroke.b, style.opacity)
    ctx.fill_preserve()
    ctx.set_line_width(stroke_width)
    ctx.set_line_cap(cairo.LineCap.ROUND)
    ctx.set_line_join(cairo.LineJoin.ROUND)
    ctx.stroke()


def dash_hexagon(ctx: cairo.Context[CairoSomeSurface], shape: Hexagon) -> None:
    style = shape.style
    width = max(0, shape.size.width)
    height = max(0, shape.size.height)

    sides = 6

    strokes = getPolygonVertices(width, height, sides)

    if style.isFilled:
        ctx.move_to(strokes[0][0].x, strokes[0][0].y)
        ctx.line_to(strokes[1][0].x, strokes[1][0].y)
        ctx.line_to(strokes[2][0].x, strokes[2][0].y)
        ctx.line_to(strokes[3][0].x, strokes[3][0].y)
        ctx.line_to(strokes[4][0].x, strokes[4][0].y)
        ctx.line_to(strokes[5][0].x, strokes[5][0].y)
        ctx.close_path()
        apply_geo_fill(ctx, style)

    finalize_dash_geo(ctx, strokes, style)


def finalize_hexagon(
    ctx: cairo.Context[CairoSomeSurface], id: str, shape: Hexagon
) -> None:
    print(f"\tTldraw: Finalizing Hexagon: {id}")

    style = shape.style

    ctx.rotate(shape.rotation)

    if style.dash is DashStyle.DRAW:
        draw_hexagon(ctx, id, shape)
    else:
        dash_hexagon(ctx, shape)

    finalize_v2_label(ctx, shape)
