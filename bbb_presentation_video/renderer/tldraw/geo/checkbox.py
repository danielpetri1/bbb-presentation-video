# SPDX-FileCopyrightText: 2022 BigBlueButton Inc. and by respective authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from math import hypot
from typing import List, TypeVar

import cairo
import perfect_freehand
from bbb_presentation_video.events.helpers import Position

from bbb_presentation_video.renderer.tldraw.shape import (
    XBox,
)
from bbb_presentation_video.renderer.tldraw.geo.rectangle import (
    rectangle_stroke_points,
)
from bbb_presentation_video.renderer.tldraw.shape.text import finalize_v2_label
from bbb_presentation_video.renderer.tldraw.utils import (
    STROKE_WIDTHS,
    STROKES,
    DashStyle,
    Style,
    apply_geo_fill,
    draw_smooth_path,
    draw_smooth_stroke_point_path,
    finalize_dash_geo,
)

CairoSomeSurface = TypeVar("CairoSomeSurface", bound=cairo.Surface)


def get_check_box_lines(w: float, h: float) -> List[List[List[float, float]]]:
    size = min(w, h) * 0.82
    ox = (w - size) / 2
    oy = (h - size) / 2

    def clamp_x(x):
        return max(0, min(w, x))

    def clamp_y(y):
        return max(0, min(h, y))

    return [
        [
            [clamp_x(ox + size * 0.25), clamp_y(oy + size * 0.52)],
            [clamp_x(ox + size * 0.45), clamp_y(oy + size * 0.82)],
        ],
        [
            [clamp_x(ox + size * 0.45), clamp_y(oy + size * 0.82)],
            [clamp_x(ox + size * 0.82), clamp_y(oy + size * 0.22)],
        ],
    ]


def overlay_checkmark(ctx: cairo.Context[CairoSomeSurface], shape: XBox) -> None:
    sw = STROKE_WIDTHS[shape.style.size]

    # Calculate dimensions
    w = max(0, shape.size.width)
    h = max(0, shape.size.height)

    # Get checkmark lines based on the dimensions
    lines = get_check_box_lines(w, h)

    stroke = STROKES[shape.style.color]

    sw = 1 + sw

    ctx.set_source_rgba(stroke.r, stroke.g, stroke.b, shape.style.opacity)

    # Set stroke width and other drawing properties
    ctx.set_line_width(sw)
    ctx.set_line_cap(cairo.LineCap.ROUND)
    ctx.set_line_join(cairo.LineJoin.ROUND)

    # Draw each line of the checkmark
    for start, end in lines:
        for point in [start, end]:
            ctx.line_to(*point)
    ctx.stroke()


def draw_checkbox(ctx: cairo.Context[CairoSomeSurface], id: str, shape: XBox) -> None:
    style = shape.style
    is_filled = style.isFilled
    stroke = STROKES[style.color]
    stroke_width = STROKE_WIDTHS[style.size]
    stroke_points = rectangle_stroke_points(id, shape)

    if is_filled:
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

    overlay_checkmark(ctx, shape)


def dash_checkbox(ctx: cairo.Context[CairoSomeSurface], shape: XBox) -> None:
    style = shape.style

    w = max(0, shape.size.width)
    h = max(0, shape.size.height)

    if style.isFilled:
        ctx.move_to(0, 0)
        ctx.line_to(w, 0)
        ctx.line_to(w, h)
        ctx.line_to(0, h)
        ctx.close_path()
        apply_geo_fill(ctx, style)

    strokes = [
        (Position(0, 0), Position(w, 0), w),
        (Position(w, 0), Position(w, h), h),
        (Position(w, h), Position(0, h), w),
        (Position(0, h), Position(0, 0), h),
    ]

    overlay_checkmark(ctx, shape)
    finalize_dash_geo(ctx, strokes, style)


def finalize_checkmark(
    ctx: cairo.Context[CairoSomeSurface], id: str, shape: XBox
) -> None:
    print(f"\tTldraw: Finalizing checkmark: {id}")

    ctx.rotate(shape.rotation)

    if shape.style.dash is DashStyle.DRAW:
        draw_checkbox(ctx, id, shape)
    else:
        dash_checkbox(ctx, shape)

    finalize_v2_label(ctx, shape)
