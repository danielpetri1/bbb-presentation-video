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
    Diamond,
)
from bbb_presentation_video.renderer.tldraw.shape.text import finalize_v2_label
from bbb_presentation_video.renderer.tldraw.utils import (
    STROKE_WIDTHS,
    STROKES,
    DashStyle,
    apply_geo_fill,
    draw_smooth_path,
    draw_smooth_stroke_point_path,
    get_perfect_dash_props,
)

def diamond_stroke_points(id: str, shape: Diamond) -> List[StrokePoint]:
    random = Random(id)
    size = shape.size
    
    width = size.width
    height = size.height
    half_width = size.width / 2
    half_height = size.height / 2

    stroke_width = STROKE_WIDTHS[shape.style.size]

    # Corners with random offsets
    variation = stroke_width * 0.75

    t = (
        half_width + random.uniform(-variation, variation),
        random.uniform(-variation, variation),
    )
    r = (
        width + random.uniform(-variation, variation),
        half_height + random.uniform(-variation, variation),
    )
    b = (
        half_width + random.uniform(-variation, variation),
        height + random.uniform(-variation, variation),
    )
    l = (
        random.uniform(-variation, variation),
        half_height + random.uniform(-variation, variation),
        )

    # Which side to start drawing first
    rm = random.randrange(0, 3)
    # Number of points per side
    # Insert each line by the corner radii and let the freehand algo
    # interpolate points for the corners.
    lines = [
        vec.points_between(t, r, 32),
        vec.points_between(r, b, 32),
        vec.points_between(b, l, 32),
        vec.points_between(l, t, 32),
    ]
    lines = lines[rm:] + lines[0:rm]

    # For the final points, include the first half of the first line again,
    # so that the line wraps around and avoids ending on a sharp corner.
    # This has a bit of finesse and magic—if you change the points between
    # function, then you'll likely need to change this one too.
    # TODO: It actually includes the whole first line again, not just half?
    points = [*lines[0], *lines[1], *lines[2], *lines[3], *lines[0]]

    return perfect_freehand.get_stroke_points(
        points, size=stroke_width, streamline=0.3, last=True
    )


CairoSomeSurface = TypeVar("CairoSomeSurface", bound=cairo.Surface)

def draw_diamond(
    ctx: cairo.Context[CairoSomeSurface], id: str, shape: Diamond
) -> None:
    style = shape.style

    stroke = STROKES[style.color]
    stroke_width = STROKE_WIDTHS[style.size]

    stroke_points = diamond_stroke_points(id, shape)

    if style.isFilled:
        draw_smooth_stroke_point_path(ctx, stroke_points, closed=False)
        apply_geo_fill(ctx, style, shape.opacity)

    stroke_outline_points = perfect_freehand.get_stroke_outline_points(
        stroke_points,
        size=stroke_width,
        thinning=0.65,
        smoothing=1,
        simulate_pressure=False,
        last=True,
    )
    draw_smooth_path(ctx, stroke_outline_points, closed=True)

    ctx.set_source_rgba(stroke.r, stroke.g, stroke.b, shape.opacity)
    ctx.fill_preserve()
    ctx.set_line_width(stroke_width)
    ctx.set_line_cap(cairo.LineCap.ROUND)
    ctx.set_line_join(cairo.LineJoin.ROUND)
    ctx.stroke()


def dash_diamond(ctx: cairo.Context[CairoSomeSurface], shape: Diamond) -> None:
    style = shape.style

    stroke = STROKES[style.color]
    stroke_width = STROKE_WIDTHS[style.size] * 1.618

    sw = 1 + stroke_width
    w = max(0, shape.size.width - sw / 2)
    h = max(0, shape.size.height - sw / 2)
    half_width = w / 2
    half_height = h / 2

    if style.isFilled:
        ctx.move_to(half_width, 0)
        ctx.line_to(w, half_height)
        ctx.line_to(half_width, h)
        ctx.line_to(0, half_height)
        ctx.close_path()
        apply_geo_fill(ctx, style, shape.opacity)

    strokes = [
        (Position(half_width, 0), Position(w, half_height), hypot(w - half_width, half_height)),
        (Position(w, half_height), Position(half_width, h), hypot(half_width - w, half_height)),
        (Position(half_width, h), Position(0, half_height), hypot(half_width, half_height)),
        (Position(0, half_height), Position(half_width, 0), hypot(half_width, half_height)),
    ]

    ctx.set_line_width(sw)
    ctx.set_line_cap(cairo.LineCap.ROUND)
    ctx.set_line_join(cairo.LineJoin.ROUND)
    ctx.set_source_rgba(stroke.r, stroke.g, stroke.b, shape.opacity)

    for start, end, length in strokes:
        ctx.move_to(start.x, start.y)
        ctx.line_to(end.x, end.y)
        dash_array, dash_offset = get_perfect_dash_props(
            length, stroke_width, style.dash
        )
        ctx.set_dash(dash_array, dash_offset)
        ctx.stroke()


def finalize_diamond(
    ctx: cairo.Context[CairoSomeSurface], id: str, shape: Diamond
) -> None:
    print(f"\tTldraw: Finalizing Diamond: {id}")

    style = shape.style

    ctx.rotate(shape.rotation)

    if style.dash is DashStyle.DRAW:
        draw_diamond(ctx, id, shape)
    else:
        dash_diamond(ctx, shape)

    finalize_v2_label(ctx, shape)
