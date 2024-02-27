# SPDX-FileCopyrightText: 2022 BigBlueButton Inc. and by respective authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Adapted from: https://github.com/tldraw/tldraw/blob/main/packages/tldraw/src/lib/shapes/geo/cloudOutline.ts

from __future__ import annotations
from math import atan2, cos, sin, tau
import math
import attr
from typing import List, Optional, TypeVar, TypedDict, Union

import cairo
from random import Random

from bbb_presentation_video.events.helpers import Position
from bbb_presentation_video.renderer.tldraw.shape import (
    Cloud,
)
from bbb_presentation_video.renderer.tldraw.shape.text import finalize_v2_label
from bbb_presentation_video.renderer.tldraw.utils import (
    STROKE_WIDTHS,
    STROKES,
    SizeStyle,
    circle_from_three_points,
    get_perfect_dash_props,
)
from bbb_presentation_video.renderer.tldraw import vec

CairoSomeSurface = TypeVar("CairoSomeSurface", bound=cairo.Surface)

@attr.s(auto_attribs=True, slots=True)
class StraightPillSection:
    start: Position
    delta: Position
    type: str = 'straight'


@attr.s(auto_attribs=True, slots=True)
class ArcPillSection:
    start_angle: float
    center: Position
    type: str = 'arc'

class Arc(TypedDict):
    leftPoint: Position
    rightPoint: Position
    arcPoint: Position
    center: Optional[Position]
    radius: float

def get_pill_circumference(w: float, h: float) -> float:
    radius = min(w, h) / 2
    long_side = max(w, h) - tau
    return tau * radius + 2 * long_side


def get_point_on_circle(center: Position, radius: float, angle: float) -> Position:
    return Position(center[0] + radius * cos(angle), center[1] + radius * sin(angle))


def get_pill_points(width: float, height: float, numPoints: int) -> List[Position]:
    radius = min(width, height) / 2
    long_side = max(width, height) - radius * 2
    circumference = tau * radius + 2 * long_side
    spacing = circumference / numPoints

    sections: List[Union[StraightPillSection, ArcPillSection]] = []

    if width > height:
        # Definitions for a horizontally oriented pill
        sections = [
            StraightPillSection(start=Position(radius, 0), delta=Position(1, 0)),
            ArcPillSection(center=Position(width - radius, radius), start_angle=-tau / 4),
            StraightPillSection(start=Position(width - radius, height), delta=Position(-1, 0)),
            ArcPillSection(center=Position(radius, radius), start_angle=tau / 4),
        ]
    else:
        # Definitions for a vertically oriented pill
        sections = [
            StraightPillSection(start=Position(width, radius), delta=Position(0, 1)),
            ArcPillSection(center=Position(radius, height - radius), start_angle=0),
            StraightPillSection(start=Position(0, height - radius), delta=Position(0, -1)),
            ArcPillSection(center=Position(radius, radius), start_angle=tau / 2),
        ]

    points = []
    section_offset = 0

    for _ in range(numPoints):
        section = sections[0]

        if section.type == "straight":
            point = vec.add(section.start, vec.mul(section.delta, section_offset))
            points.append(Position(point[0], point[1]))
        else:
            point = get_point_on_circle(
                section.center, radius, section.start_angle + section_offset / radius
            )
            points.append(point)

        section_offset += spacing
        section_length = long_side if section.type == "straight" else tau / 2 * radius

        while section_offset > section_length:
            section_offset -= section_length
            sections.append(sections.pop(0))
            section = sections[0]
            section_length = (
                long_side if section.type == "straight" else tau / 2 * radius
            )

    return points

def switchSize(size: SizeStyle) -> float:
    if size is SizeStyle.S:
        return 50.0
    elif size is SizeStyle.M:
        return 70.0
    elif size is SizeStyle.L:
        return 100.0
    elif size is SizeStyle.XL:
        return 130.0
    else:
        return 70.0

def get_cloud_arcs(width: float, height: float, seed: str, size: SizeStyle) -> List[Arc]:
    random = Random(seed)
    pillCircumference = get_pill_circumference(width, height)

    numBumps = max(
        math.ceil(pillCircumference / switchSize(size)),
        6,
        math.ceil(pillCircumference / min(width, height)),
    )

    targetBumpProtrusion = (pillCircumference / numBumps) * 0.2
    innerWidth = max(width - targetBumpProtrusion * 2, 1)
    innerHeight = max(height - targetBumpProtrusion * 2, 1)
    paddingX = (width - innerWidth) / 2
    paddingY = (height - innerHeight) / 2

    distanceBetweenPointsOnPerimeter = (
        get_pill_circumference(innerWidth, innerHeight) / numBumps
    )

    bumpPoints = [
        vec.add(p, (paddingX, paddingY))
        for p in get_pill_points(innerWidth, innerHeight, numBumps)
    ]
    maxWiggleX = 0 if width < 20 else targetBumpProtrusion * 0.3
    maxWiggleY = 0 if height < 20 else targetBumpProtrusion * 0.3

    for i in range(math.floor(numBumps / 2)):
        bumpPoints[i] = vec.add(
            bumpPoints[i], (random.random() * maxWiggleX, random.random() * maxWiggleY)
        )
        bumpPoints[numBumps - i - 1] = vec.add(
            bumpPoints[numBumps - i - 1], (random.random() * maxWiggleX, random.random() * maxWiggleY)
        )

    arcs = []

    for i in range(len(bumpPoints)):
        j = 0 if i == len(bumpPoints) - 1 else i + 1
        leftWigglePoint = bumpPoints[i]
        rightWigglePoint = bumpPoints[j]
        leftPoint = bumpPoints[i]
        rightPoint = bumpPoints[j]

        midPoint = vec.med(leftPoint, rightPoint)
        offsetAngle = vec.angle(leftPoint, rightPoint) - tau / 4

        distanceBetweenOriginalPoints = vec.dist(leftPoint, rightPoint)
        curvatureOffset = (
            distanceBetweenPointsOnPerimeter - distanceBetweenOriginalPoints
        )
        distanceBetweenWigglePoints = vec.dist(leftWigglePoint, rightWigglePoint)
        relativeSize = distanceBetweenWigglePoints / distanceBetweenOriginalPoints
        finalDistance = (max(paddingX, paddingY) + curvatureOffset) * relativeSize

        arcPoint = vec.add(midPoint, vec.from_angle(offsetAngle, finalDistance))

        arcPoint_x = 0 if arcPoint[0] < 0 else (width if arcPoint[0] > width else arcPoint[0])
        arcPoint_y = 0 if arcPoint[1] < 0 else (height if arcPoint[1] > height else arcPoint[1])
        arcPoint = (arcPoint_x, arcPoint_y)

        center = circle_from_three_points(leftWigglePoint, rightWigglePoint, arcPoint)
        center = (center[0].x, center[0].y)

        radius = vec.dist(
            center if center else vec.med(leftWigglePoint, rightWigglePoint),
            leftWigglePoint,
        )

        arc_dict = Arc(
            leftPoint=Position(*leftWigglePoint),
            rightPoint=Position(*rightWigglePoint),
            arcPoint=Position(*arcPoint),
            center=Position(*center) if center is not None else None,
            radius=radius
        )

        arcs.append(arc_dict)

    return arcs

# def cloud_outline(width, height, seed, size):
#     path = []

#     arcs = get_cloud_arcs(width, height, seed, size)

#     for arc in arcs:
#         center, radius, leftPoint, rightPoint = arc['center'], arc['radius'], arc['leftPoint'], arc['rightPoint']
#         path.extend(points_on_arc(leftPoint, rightPoint, center, radius, 10))

#     return path

def calculate_angle(center: Position, point: Position) -> float:
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    angle = atan2(dy, dx)
    return angle

def dash_cloud(ctx: cairo.Context[CairoSomeSurface], shape: Cloud, id: str) -> None:
    style = shape.style

    w = max(0, shape.size.width)
    h = max(0, shape.size.height)

    stroke_width = STROKE_WIDTHS[style.size]
    sw = 1 + stroke_width * 1.618

    stroke = STROKES[style.color]

    ctx.save()

    arcs: List[Arc] = get_cloud_arcs(w, h, id, style.size)

    ctx.new_sub_path()

    for arc in arcs:
        leftPoint, rightPoint, radius, center = arc['leftPoint'], arc['rightPoint'], arc['radius'], arc['center']
    
        if center is None:
            # Move to leftPoint and draw a line to rightPoint instead of an arc
            ctx.move_to(*leftPoint)
            ctx.line_to(*rightPoint)
        else:
            # Calculate start and end angles
            start_angle = calculate_angle(center, leftPoint)
            end_angle = calculate_angle(center, rightPoint)
            
            ctx.arc(center[0], center[1], radius, start_angle, end_angle)
        
    ctx.close_path()
    ctx.set_line_width(sw)
    ctx.set_line_cap(cairo.LineCap.ROUND)
    ctx.set_line_join(cairo.LineJoin.ROUND)

    dash_array, dash_offset = get_perfect_dash_props(
        abs(2 * w + 2 * h), sw, style.dash, snap=2, outset=False
    )

    ctx.set_dash(dash_array, dash_offset)
    ctx.set_source_rgba(stroke.r, stroke.g, stroke.b, style.opacity)
    ctx.stroke()
    ctx.restore()


def finalize_cloud(ctx: cairo.Context[CairoSomeSurface], id: str, shape: Cloud) -> None:
    print(f"\tTldraw: Finalizing Cloud: {id}")

    ctx.rotate(shape.rotation)

    dash_cloud(ctx, shape, id)

    finalize_v2_label(ctx, shape)
