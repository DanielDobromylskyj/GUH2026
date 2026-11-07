"""Opening hours are stored as human readable strings (8am .. 8pm)."""

HOURS: tuple[str, ...] = (
    "8am", "9am", "10am", "11am", "12pm",
    "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm",
)

_HOUR_TO_LABEL = {h: HOURS[i] for i, h in enumerate(range(8, 21))}
_LABEL_TO_HOUR = {label: hour for hour, label in _HOUR_TO_LABEL.items()}


def hour_to_label(hour: int) -> str:
    """Convert a 24 hour clock value (8-20) into its label, e.g. 13 -> '1pm'."""
    try:
        return _HOUR_TO_LABEL[hour]
    except KeyError:
        raise ValueError(f"Hour {hour} is outside of opening hours (8-20)") from None


def label_to_hour(label: str) -> int:
    """Convert a label into a 24 hour clock value, e.g. '1pm' -> 13."""
    try:
        return _LABEL_TO_HOUR[label]
    except KeyError:
        raise ValueError(f"Invalid hour label: {label!r}, expected one of {HOURS}") from None


def validate_label(label: str) -> str:
    label_to_hour(label)
    return label
