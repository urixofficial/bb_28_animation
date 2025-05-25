# utils.py
import numpy as np
import colorsys

def initialize_points(num_points, width, height, fixed_corners, side_points, speed):
    """
    Initialize random points and their velocities, with optional fixed corner and side points.

    Args:
        num_points (int): Number of random points.
        width (float): Canvas width.
        height (float): Canvas height.
        fixed_corners (bool): Whether to include fixed corner points.
        side_points (bool): Whether to include side points.
        speed (float): Base speed for point movement.

    Returns:
        tuple: Arrays of points and velocities.
    """
    points = np.random.rand(num_points, 2) * np.array([width, height])
    velocities = (np.random.rand(num_points, 2) - 0.5) * speed

    if fixed_corners:
        corner_points = np.array([
            [0, 0],
            [width, 0],
            [0, height],
            [width, height]
        ])
        points = np.vstack((points, corner_points))
        velocities = np.vstack((velocities, np.zeros((4, 2))))

    if side_points:
        side_points_list = []
        side_velocities_list = []
        side_speed = lambda: np.random.uniform(speed / 4, speed / 2) * np.random.choice([-1, 1])

        # Bottom side (y=0, x from 0 to width)
        side_points_list.extend([[0, 0], [width, 0]])
        side_velocities_list.extend([[side_speed(), 0], [side_speed(), 0]])

        # Top side (y=height, x from 0 to width)
        side_points_list.extend([[0, height], [width, height]])
        side_velocities_list.extend([[side_speed(), 0], [side_speed(), 0]])

        # Left side (x=0, y from 0 to height)
        side_points_list.extend([[0, 0], [0, height]])
        side_velocities_list.extend([[0, side_speed()], [0, side_speed()]])

        # Right side (x=width, y from 0 to height)
        side_points_list.extend([[width, 0], [width, height]])
        side_velocities_list.extend([[0, side_speed()], [0, side_speed()]])

        points = np.vstack((points, np.array(side_points_list)))
        velocities = np.vstack((velocities, np.array(side_velocities_list)))

    return points, velocities

def get_color(hue, brightness):
    """
    Convert hue and brightness to RGB color.

    Args:
        hue (float): Hue value (0-360).
        brightness (float): Brightness value (0-100).

    Returns:
        tuple: RGB color values.
    """
    hue = hue / 360.0  # Normalize to [0, 1]
    brightness = brightness / 100.0  # Normalize to [0, 1]
    if brightness <= 0.5:
        value = brightness * 2
        saturation = 1.0
    else:
        value = 1.0
        saturation = 1.0 - (brightness - 0.5) * 2
    return colorsys.hsv_to_rgb(hue, saturation, value)

def initialize_triangle_colors(simplices, base_hue, brightness_range, triangle_colors):
    """
    Initialize or update colors for triangles, varying only brightness.

    Args:
        simplices (list): List of triangle simplices from Delaunay triangulation.
        base_hue (float): Base hue for colors (0-1).
        brightness_range (float): Brightness range (0-100).
        triangle_colors (dict): Existing triangle colors to preserve.

    Returns:
        dict: Updated triangle colors.
    """
    brightness_range = brightness_range / 100.0
    new_colors = {}
    for simplex in simplices:
        simplex_key = tuple(sorted(simplex))
        if simplex_key in triangle_colors:
            new_colors[simplex_key] = triangle_colors[simplex_key]
        else:
            value = max(0.0, min(1.0, 1.0 - brightness_range + np.random.rand() * brightness_range * 2))
            rgb = colorsys.hsv_to_rgb(base_hue, 1.0, value)
            new_colors[simplex_key] = rgb
    return new_colors