def is_valid_color(color: str) -> bool:
    """
    This function asserts that the color is a valid hex color.
    """
    return (
        color.startswith("#")
        and len(color) == 7
        and all(c in "0123456789abcdef" for c in color[1:].lower())
    )


def assert_valid_color(color: str):
    """
    This function asserts that the color is a valid hex color.
    """
    if not is_valid_color(color):
        raise ValueError("Invalid color")
