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

        side_points_list.extend([[0, 0], [width, 0]])
        side_velocities_list.extend([[side_speed(), 0], [side_speed(), 0]])
        side_points_list.extend([[0, height], [width, height]])
        side_velocities_list.extend([[side_speed(), 0], [side_speed(), 0]])
        side_points_list.extend([[0, 0], [0, height]])
        side_velocities_list.extend([[0, side_speed()], [0, side_speed()]])
        side_points_list.extend([[width, 0], [width, height]])
        side_velocities_list.extend([[0, side_speed()], [0, side_speed()]])

        points = np.vstack((points, np.array(side_points_list)))
        velocities = np.vstack((velocities, np.array(side_velocities_list)))

    return points, velocities

def get_color(hue, saturation, value):
    """
    Convert HSV values to RGB color.

    Args:
        hue (float): Hue value (0-360).
        saturation (float): Saturation value (0-100).
        value (float): Value/Brightness value (0-100).

    Returns:
        tuple: RGB color values.
    """
    hue = hue / 360.0
    saturation = saturation / 100.0
    value = value / 100.0
    return colorsys.hsv_to_rgb(hue, saturation, value)

def initialize_triangle_colors(simplices, base_color, brightness_range, triangle_colors):
    """
    Initialize or update colors for triangles, varying only brightness based on base color.

    Args:
        simplices (list): List of triangle simplices from Delaunay triangulation.
        base_color (tuple): Base RGB color of points/lines (from get_color).
        brightness_range (float): Brightness range (0-100).
        triangle_colors (dict): Existing triangle colors to preserve.

    Returns:
        dict: Updated triangle colors with RGBA.
    """
    brightness_range = brightness_range / 100.0
    new_colors = {}
    base_hsv = colorsys.rgb_to_hsv(*base_color)
    base_hue = base_hsv[0]
    base_saturation = base_hsv[1]

    for simplex in simplices:
        simplex_key = tuple(sorted(simplex))
        if simplex_key in triangle_colors:
            new_colors[simplex_key] = triangle_colors[simplex_key]
        else:
            value = max(0.0, min(1.0, 1.0 - brightness_range + np.random.rand() * brightness_range * 2))
            rgb = colorsys.hsv_to_rgb(base_hue, base_saturation, value)
            new_colors[simplex_key] = rgb + (1.0,)
    return new_colors

def point_in_polygon(point, polygon):
    """
    Проверка, находится ли точка внутри полигона (Ray Casting Algorithm).

    Args:
        point (np.array): Координаты точки [x, y].
        polygon (np.array): Массив вершин полигона [[x1, y1], [x2, y2], ...].

    Returns:
        bool: True, если точка внутри полигона, иначе False.
    """
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        if ((polygon[i][1] > y) != (polygon[j][1] > y)) and \
           (x < (polygon[j][0] - polygon[i][0]) * (y - polygon[i][1]) / (polygon[j][1] - polygon[i][1] + 1e-10) + polygon[i][0]):
            inside = not inside
        j = i
    return inside

def segment_intersects_polygon(p1, p2, polygon):
    """
    Проверка, пересекает ли отрезок [p1, p2] полигон.

    Args:
        p1 (np.array): Начальная точка отрезка [x1, y1].
        p2 (np.array): Конечная точка отрезка [x2, y2].
        polygon (np.array): Массив вершин полигона [[x1, y1], [x2, y2], ...].

    Returns:
        bool: True, если отрезок пересекает полигон, иначе False.
    """
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def intersects(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    for i in range(len(polygon)):
        p3 = polygon[i]
        p4 = polygon[(i + 1) % len(polygon)]
        if intersects(p1, p2, p3, p4):
            return True
    return False

def closest_point_on_polygon(point, polygon):
    """
    Нахождение ближайшей точки на границе полигона к данной точке.

    Args:
        point (np.array): Координаты точки [x, y].
        polygon (np.array): Массив вершин полигона [[x1, y1], [x2, y2], ...].

    Returns:
        np.array: Координаты ближайшей точки на границе полигона.
    """
    min_dist = float('inf')
    closest = point
    for i in range(len(polygon)):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]
        # Проекция точки на отрезок
        v = p2 - p1
        w = point - p1
        c1 = np.dot(w, v)
        if c1 <= 0:
            closest_candidate = p1
        else:
            c2 = np.dot(v, v)
            if c2 <= c1:
                closest_candidate = p2
            else:
                t = c1 / c2
                closest_candidate = p1 + t * v
        dist = np.linalg.norm(point - closest_candidate)
        if dist < min_dist:
            min_dist = dist
            closest = closest_candidate
    return closest