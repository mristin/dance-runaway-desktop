"""Define the game events."""

import abc
import enum
from typing import Union

from icontract import DBC


class Event(DBC):
    """Represent an abstract event in the game."""

    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()


class Tick(Event):
    """Mark a tick in the (irregular) game clock."""

    def __str__(self) -> str:
        return self.__class__.__name__


class GameOverKind(enum.Enum):
    """Model different game endings."""

    HAPPY_END = 0
    BUSTED = 1


class GameOver(Event):
    """Signal that we have to exit the game."""

    def __init__(self, kind: GameOverKind) -> None:
        """Initialize with the given values."""
        self.kind = kind

    def __str__(self) -> str:
        return self.__class__.__name__


class Button(enum.Enum):
    """
    Represent abstract buttons, not necessarily tied to a concrete joystick.

    The enumeration of the buttons should follow the circle, with upper left being
    enumerated 0.
    """

    CROSS = 0
    UP = 1
    CIRCLE = 2
    RIGHT = 3
    SQUARE = 4
    DOWN = 5
    TRIANGLE = 6
    LEFT = 7


class ButtonDown(Event):
    """Capture the button down events."""

    def __init__(self, button: Button) -> None:
        """Initialize with the given values."""
        self.button = button

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.button.name})"


class MakeStep(Event):
    """Signal the player to make a step."""

    def __str__(self) -> str:
        return self.__class__.__name__


EventUnion = Union[Tick, GameOver, ButtonDown, MakeStep]
