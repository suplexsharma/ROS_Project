from enum import IntEnum


class Gesture(IntEnum):
    ONE_FINGER = 1
    TWO_FINGER = 2
    THUMB_UP = 3
    NO_GESTURE = 4

    @classmethod
    def from_name(cls, name: str) -> "Gesture":
        if name == "Thumb_Up":
            return cls.THUMB_UP
        elif name == "Pointing_UP":
            return cls.ONE_FINGER
        elif name == "Victory":
            return cls.TWO_FINGER
        else:
            return cls.NO_GESTURE

    @classmethod
    def from_int(cls, value: int) -> "Gesture":
        return cls(value)