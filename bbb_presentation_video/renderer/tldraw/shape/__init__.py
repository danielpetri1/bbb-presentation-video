# SPDX-FileCopyrightText: 2022 BigBlueButton Inc. and by respective authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Optional, Protocol, Tuple, Type, TypeVar, Union

import cairo
from attrs import define

from bbb_presentation_video.events import Size
from bbb_presentation_video.events.helpers import Position
from bbb_presentation_video.events.tldraw import ShapeData
from bbb_presentation_video.renderer.tldraw.utils import Bounds, DrawPoints, Style

BaseShapeSelf = TypeVar("BaseShapeSelf", bound="BaseShape")


@define
class BaseShape:
    """The base class for all tldraw shapes."""

    data: ShapeData
    """A copy of the original JSON shape data from tldraw, for handling updates."""
    style: Style
    """Style related properties, such as color, line size, font."""
    childIndex: float
    """Unsure: possibly z-position of this shape within a group?"""
    point: Position
    """Position of the origin of the shape."""

    def __init__(self, data: ShapeData) -> None:
        self.style = Style()
        self.childIndex = 1
        self.point = Position(0, 0)

        self.update_from_data(data)

    def update_from_data(self, data: ShapeData) -> None:
        self.data = data

        if "style" in data:
            self.style = Style.from_data(data["style"])
        if "childIndex" in data:
            self.childIndex = data["childIndex"]
        if "point" in data:
            point = data["point"]
            self.point = Position(point[0], point[1])

class RotatableShapeProto(Protocol):
    """The size and rotation fields that are common to many shapes."""

    size: Size
    rotation: float

    def update_from_data(self, data: ShapeData) -> None:
        """Update the common size and rotation fields."""
        if "size" in data:
            self.size = Size(*data["size"])
        if "rotation" in data:
            self.rotation = data["rotation"]


class LabelledShapeProto(Protocol):
    style: Style
    size: Size
    label: Optional[str]
    labelPoint: Position

    def update_from_data(self, data: ShapeData) -> None:
        if "label" in data:
            self.label = data["label"] if data["label"] != "" else None
        if "labelPoint" in data:
            self.labelPoint = Position(*data["labelPoint"])


def shape_sort_key(shape: BaseShape) -> float:
    return shape.childIndex


@define
class DrawShape(BaseShape):
    points: DrawPoints
    isComplete: bool

    # RotatableShapeProto
    size: Size
    rotation: float

    cached_bounds: Optional[Bounds] = None
    cached_path: Optional[cairo.Path] = None
    cached_outline_path: Optional[cairo.Path] = None

    def __init__(self, data: ShapeData) -> None:
        self.points = []
        self.isComplete = False
        self.size = Size(0, 0)
        self.rotation = 0

        super().__init__(data)

    def update_from_data(self, data: ShapeData) -> None:
        super().update_from_data(data)

        RotatableShapeProto.update_from_data(self, data)

        if "points" in data:
            self.points = []
            for point in data["points"]:
                if len(point) == 3:
                    self.points.append((point[0], point[1], point[2]))
                else:
                    self.points.append((point[0], point[1]))
        if "isComplete" in data:
            self.isComplete = data["isComplete"]

        self.cached_bounds = None
        self.cached_path = None
        self.cached_outline_path = None


@define
class RectangleShape(BaseShape):
    # LabelledShapeProto
    label: Optional[str]
    labelPoint: Position

    # RotatableShapeProto
    size: Size
    rotation: float

    cached_path: Optional[cairo.Path] = None
    cached_outline_path: Optional[cairo.Path] = None

    def __init__(self, data: ShapeData) -> None:
        self.label = None
        self.labelPoint = Position(0.5, 0.5)
        self.size = Size(1, 1)
        self.rotation = 0

        super().__init__(data)

    def update_from_data(self, data: ShapeData) -> None:
        super().update_from_data(data)

        LabelledShapeProto.update_from_data(self, data)
        RotatableShapeProto.update_from_data(self, data)

        self.cached_path = None
        self.cached_outline_path = None


@define
class EllipseShape(BaseShape):
    radius: Tuple[float, float]

    # LabelledShapeProto
    label: Optional[str]
    labelPoint: Position

    # RotatableShapeProto
    size: Size
    rotation: float

    cached_path: Optional[cairo.Path] = None
    cached_outline_path: Optional[cairo.Path] = None

    def __init__(self, data: ShapeData) -> None:
        self.radius = (1.0, 1.0)
        self.label = None
        self.labelPoint = Position(0.5, 0.5)
        self.size = Size(1.0, 1.0)
        self.rotation = 0

        super().__init__(data)

    def update_from_data(self, data: ShapeData) -> None:
        super().update_from_data(data)

        if "radius" in data:
            radius = data["radius"]
            self.radius = (radius[0], radius[1])

        LabelledShapeProto.update_from_data(self, data)
        RotatableShapeProto.update_from_data(self, data)

        self.cached_path = None
        self.cached_outline_path = None


@define
class TriangleShape(BaseShape):
    # LabelledShapeProto
    label: Optional[str]
    labelPoint: Position

    # RotatableShapeProto
    size: Size
    rotation: float

    cached_path: Optional[cairo.Path] = None
    cached_outline_path: Optional[cairo.Path] = None

    def __init__(self, data: ShapeData) -> None:
        self.label = None
        self.labelPoint = Position(0.5, 0.5)
        self.size = Size(1.0, 1.0)
        self.rotation = 0

        super().__init__(data)

    def update_from_data(self, data: ShapeData) -> None:
        super().update_from_data(data)

        LabelledShapeProto.update_from_data(self, data)
        RotatableShapeProto.update_from_data(self, data)

        self.cached_path = None
        self.cached_outline_path = None


@define
class TextShape(BaseShape):
    text: str

    # RotatableShapeProto
    size: Size
    rotation: float

    def __init__(self, data: ShapeData) -> None:
        self.text = ""
        self.size = Size(0.0, 0.0)
        self.rotation = 0.0

        super().__init__(data)

    def update_from_data(self, data: ShapeData) -> None:
        super().update_from_data(data)

        if "text" in data:
            self.text = data["text"]

        RotatableShapeProto.update_from_data(self, data)


@define
class GroupShape(BaseShape):
    # children: List[str]
    # size: Size
    # rotation: float
    
    def __init__(self, data: ShapeData) -> None:
        super().__init__(data)


@define
class StickyShape(BaseShape):
    text: str

    # RotatableShapeProto
    size: Size
    rotation: float

    def __init__(self, data: ShapeData) -> None:
        self.text = ""
        self.size = Size(200.0, 200.0)
        self.rotation = 0

        super().__init__(data)

    def update_from_data(self, data: ShapeData) -> None:
        super().update_from_data(data)

        if "text" in data:
            self.text = data["text"]

        RotatableShapeProto.update_from_data(self, data)


@define
class ArrowHandle:
    point: Position


@define
class ArrowHandles:
    start: ArrowHandle
    end: ArrowHandle
    bend: ArrowHandle

    def __init__(self):
        # TODO: This is temporary so arrows don't crash the app. Needs to be replaced with proper parsing.
        self.start = ArrowHandle(Position(0, 0))
        self.end = ArrowHandle(Position(0, 0))
        self.bend = ArrowHandle(Position(0, 0))


@define
class ArrowShape(BaseShape):
    bend: float
    handles: ArrowHandles

    # LabelledShapeProto
    label: Optional[str]
    labelPoint: Position

    # RotatableShapeProto
    size: Size
    rotation: float

    def __init__(self, data: ShapeData) -> None:
        self.bend = 0.0
        self.handles = ArrowHandles()
        self.label = None,
        self.labelPoint = Position(0.5, 0.5)
        self.size = Size(0.0, 0.0)
        self.rotation = 0.0

        super().__init__(data)

    def update_from_data(self, data: ShapeData) -> None:
        super().update_from_data(data)

        if "bend" in data:
            self.bend = data["bend"]
        
        # TODO: parse this from data
        self.handles = ArrowHandles()

        LabelledShapeProto.update_from_data(self, data)
        RotatableShapeProto.update_from_data(self, data)


Shape = Union[
    DrawShape,
    RectangleShape,
    EllipseShape,
    TriangleShape,
    ArrowShape,
    TextShape,
    GroupShape,
    StickyShape,
]


def parse_shape_from_data(data: ShapeData) -> Shape:
    type = data["type"]
    if type == "draw":
        return DrawShape(data)
    elif type == "rectangle":
        return RectangleShape(data)
    elif type == "ellipse":
        return EllipseShape(data)
    elif type == "triangle":
        return TriangleShape(data)
    elif type == "arrow":
        return ArrowShape(data)
    elif type == "text":
        return TextShape(data)
    elif type == "group":
        return GroupShape(data)
    elif type == "sticky":
        return StickyShape(data)
    else:
        raise Exception(f"Unknown shape type: {type}")


def apply_shape_rotation(ctx: cairo.Context, shape: RotatableShapeProto) -> None:
    x = shape.size.width / 2
    y = shape.size.height / 2
    ctx.translate(x, y)
    ctx.rotate(shape.rotation)
    ctx.translate(-x, -y)
