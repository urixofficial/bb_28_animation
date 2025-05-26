import numpy as np
from scipy.spatial import Delaunay
from modules.utils import initialize_points, get_color, initialize_triangle_colors
from loguru import logger
from PySide6.QtCore import QTimer

class AnimationManager:
    """
    Управление анимацией точек с Delaunay-триангуляцией и настраиваемыми параметрами рендеринга.
    """
    def __init__(self, canvas, get_parameters, fixed_corners_check, show_points_check,
                 show_lines_check, fill_triangles_check, main_hue_slider,
                 main_saturation_slider, main_value_slider, brightness_range_slider, speed_slider,
                 bg_hue_slider, bg_saturation_slider, bg_value_slider, side_points_check,
                 transition_speed_slider):
        """
        Инициализация менеджера анимации.
        """
        self.canvas = canvas
        self.get_parameters = get_parameters
        self.fixed_corners_check = fixed_corners_check
        self.show_points_check = show_points_check
        self.show_lines_check = show_lines_check
        self.fill_triangles_check = fill_triangles_check
        self.main_hue_slider = main_hue_slider
        self.main_saturation_slider = main_saturation_slider
        self.main_value_slider = main_value_slider
        self.brightness_range_slider = brightness_range_slider
        self.speed_slider = speed_slider
        self.bg_hue_slider = bg_hue_slider
        self.bg_saturation_slider = bg_saturation_slider
        self.bg_value_slider = bg_value_slider
        self.side_points_check = side_points_check
        self.transition_speed_slider = transition_speed_slider
        self.points = np.array([])
        self.velocities = np.array([])
        self.triangle_colors = {}
        self.triangle_alphas = {}
        self.line_alphas = {}
        self.simplices = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_static_frame = False
        self.lines_alpha = 1.0 if self.show_lines_check.isChecked() else 0.0
        self.triangles_alpha = 1.0 if self.fill_triangles_check.isChecked() else 0.0
        self.show_lines_check.stateChanged.connect(self.update_lines_alpha)
        self.fill_triangles_check.stateChanged.connect(self.update_triangles_alpha)

    def update_lines_alpha(self):
        """Мгновенное обновление альфа-значения для линий."""
        self.lines_alpha = 1.0 if self.show_lines_check.isChecked() else 0.0
        self.canvas.lines_alpha = self.lines_alpha
        self.update_render_parameters()
        logger.debug(f"Альфа для линий: {self.lines_alpha}")

    def update_triangles_alpha(self):
        """Мгновенное обновление альфа-значения для треугольников."""
        self.triangles_alpha = 1.0 if self.fill_triangles_check.isChecked() else 0.0
        self.canvas.triangles_alpha = self.triangles_alpha
        self.update_render_parameters()
        logger.debug(f"Альфа для треугольников: {self.triangles_alpha}")

    def initialize_points(self, num_points, width, height):
        """Инициализация точек и их скоростей."""
        logger.info(f"Инициализация {num_points} точек на холсте {width}x{height}")
        self.points, self.velocities = initialize_points(
            num_points, width, height, self.fixed_corners_check.isChecked(),
            self.side_points_check.isChecked(), self.get_speed()
        )
        self.update_triangulation_and_colors()

    def update_triangulation_and_colors(self):
        """Обновление триангуляции и цветов треугольников."""
        if len(self.points) == 0:
            return
        tri = Delaunay(self.points)
        self.simplices = tri.simplices
        if self.triangles_alpha > 0.0:
            base_color = self.get_color()
            self.triangle_colors = initialize_triangle_colors(
                tri.simplices, base_color,
                self.brightness_range_slider.value(), {}
            )
            for simplex in tri.simplices:
                simplex_key = tuple(sorted(simplex))
                if simplex_key not in self.triangle_alphas:
                    self.triangle_alphas[simplex_key] = 1.0
        if self.lines_alpha > 0.0:
            for simplex in tri.simplices:
                for i in range(3):
                    v0, v1 = simplex[i], simplex[(i + 1) % 3]
                    line_key = tuple(sorted([v0, v1]))
                    if line_key not in self.line_alphas:
                        self.line_alphas[line_key] = 1.0
        self.canvas.triangle_colors = self.triangle_colors
        self.canvas.triangle_alphas = self.triangle_alphas
        self.canvas.line_alphas = self.line_alphas
        self.canvas.simplices = self.simplices
        self.canvas.points = self.points

    def get_speed(self):
        """Получение скорости анимации."""
        return self.speed_slider.value()

    def get_color(self):
        """Получение RGB цвета для точек и линий."""
        return get_color(self.main_hue_slider.value(),
                        self.main_saturation_slider.value(),
                        self.main_value_slider.value())

    def get_background_color(self):
        """Получение RGB цвета для фона."""
        return get_color(self.bg_hue_slider.value(),
                        self.bg_saturation_slider.value(),
                        self.bg_value_slider.value())

    def _update_points(self):
        """Обновление позиций точек на основе скоростей."""
        self.points += self.velocities

    def _handle_boundary_collisions(self, width, height, num_fixed, num_side):
        """Обработка столкновений точек с границами холста."""
        if len(self.points) == 0:
            return
        free_points = self.points[:-num_fixed - num_side] if num_fixed + num_side > 0 else self.points
        free_velocities = self.velocities[:-num_fixed - num_side] if num_fixed + num_side > 0 else self.velocities
        if len(free_points) > 0:
            mask_x = (free_points[:, 0] < 0) | (free_points[:, 0] > width)
            mask_y = (free_points[:, 1] < 0) | (free_points[:, 1] > height)
            free_velocities[:, 0][mask_x] *= -1
            free_velocities[:, 1][mask_y] *= -1

        if num_side > 0:
            side_idx = len(self.points) - num_side
            for i in [side_idx, side_idx + 1, side_idx + 2, side_idx + 3]:
                if self.points[i, 0] < 0 or self.points[i, 0] > width:
                    self.velocities[i, 0] *= -1
            for i in [side_idx + 4, side_idx + 5, side_idx + 6, side_idx + 7]:
                if self.points[i, 1] < 0 or self.points[i, 1] > height:
                    self.velocities[i, 1] *= -1

    def update_frame(self, for_export=False):
        """Обновление кадра анимации."""
        if self.is_static_frame and not for_export:
            return
        width, height, fps, _, num_points, point_size, line_width = self.get_parameters()
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0
        transition_speed = self.transition_speed_slider.value() / 10.0

        self._update_points()
        self._handle_boundary_collisions(width, height, num_fixed, num_side)
        tri = Delaunay(self.points)
        new_simplices = tri.simplices
        self.simplices = new_simplices
        new_simplex_keys = set(tuple(sorted(simplex)) for simplex in new_simplices)
        old_simplex_keys = set(self.triangle_alphas.keys())
        new_line_keys = set()
        for simplex in new_simplices:
            for i in range(3):
                v0, v1 = simplex[i], simplex[(i + 1) % 3]
                new_line_keys.add(tuple(sorted([v0, v1])))
        old_line_keys = set(self.line_alphas.keys())

        if self.triangles_alpha > 0.0:
            base_color = self.get_color()
            self.triangle_colors = initialize_triangle_colors(
                new_simplices, base_color,
                self.brightness_range_slider.value(), self.triangle_colors
            )
            delta = transition_speed * (1.0 / fps)
            for simplex_key in new_simplex_keys - old_simplex_keys:
                self.triangle_alphas[simplex_key] = 0.0
            for simplex_key in list(self.triangle_alphas.keys()):
                if simplex_key in new_simplex_keys:
                    self.triangle_alphas[simplex_key] = min(self.triangle_alphas[simplex_key] + delta, 1.0)
                else:
                    self.triangle_alphas[simplex_key] = max(self.triangle_alphas[simplex_key] - delta, 0.0)
                    if self.triangle_alphas[simplex_key] <= 0.01:
                        del self.triangle_alphas[simplex_key]
                        if simplex_key in self.triangle_colors:
                            del self.triangle_colors[simplex_key]

        if self.lines_alpha > 0.0:
            delta = transition_speed * (1.0 / fps)
            for line_key in new_line_keys - old_line_keys:
                self.line_alphas[line_key] = 0.0
            for line_key in list(self.line_alphas.keys()):
                if line_key in new_line_keys:
                    self.line_alphas[line_key] = min(self.line_alphas[line_key] + delta, 1.0)
                else:
                    self.line_alphas[line_key] = max(self.line_alphas[line_key] - delta, 0.0)
                    if self.line_alphas[line_key] <= 0.01:
                        del self.line_alphas[line_key]

        self.canvas.points = self.points
        self.canvas.simplices = new_simplices
        self.canvas.triangle_colors = self.triangle_colors
        self.canvas.triangle_alphas = self.triangle_alphas
        self.canvas.line_alphas = self.line_alphas
        self.canvas.lines_alpha = self.lines_alpha
        self.canvas.triangles_alpha = self.triangles_alpha
        if not for_export:
            self.canvas.update()

    def draw_frame(self):
        """Отрисовка текущего кадра."""
        self.canvas.lines_alpha = self.lines_alpha
        self.canvas.triangles_alpha = self.triangles_alpha
        self.canvas.triangle_alphas = self.triangle_alphas
        self.canvas.line_alphas = self.line_alphas
        self.canvas.triangle_colors = self.triangle_colors
        self.canvas.simplices = self.simplices
        self.canvas.points = self.points
        self.canvas.update()

    def generate_single_frame(self):
        """Генерация и отрисовка одиночного кадра."""
        logger.info("Генерация одиночного кадра")
        width, height, _, _, num_points, _, _ = self.get_parameters()
        self.initialize_points(num_points, width, height)
        self.is_static_frame = True
        self.lines_alpha = 1.0 if self.show_lines_check.isChecked() else 0.0
        self.triangles_alpha = 1.0 if self.fill_triangles_check.isChecked() else 0.0
        self.canvas.lines_alpha = self.lines_alpha
        self.canvas.triangles_alpha = self.triangles_alpha
        self.update_triangulation_and_colors()
        self.draw_frame()

    def start_animation(self):
        """Запуск анимации с текущими точками."""
        logger.info("Запуск анимации")
        self.is_static_frame = False
        width, height, fps, _, num_points, _, _ = self.get_parameters()
        if len(self.points) == 0 or len(self.points) != num_points or self.points.shape[1] != 2:
            self.initialize_points(num_points, width, height)
        self.canvas.points = self.points
        self.lines_alpha = 1.0 if self.show_lines_check.isChecked() else 0.0
        self.triangles_alpha = 1.0 if self.fill_triangles_check.isChecked() else 0.0
        self.canvas.lines_alpha = self.lines_alpha
        self.canvas.triangles_alpha = self.triangles_alpha
        self.update_triangulation_and_colors()
        self.timer.start(int(1000 / fps))

    def stop_animation(self):
        """Остановка анимации с сохранением текущего кадра."""
        logger.info("Остановка анимации")
        self.timer.stop()
        self.is_static_frame = True
        self.draw_frame()

    def update_points_and_frame(self):
        """Обновление точек и кадра при изменении num_points, width, height или чекбоксов."""
        logger.info("Обновление точек и кадра")
        width, height, fps, _, num_points, _, _ = self.get_parameters()
        self.initialize_points(num_points, width, height)
        if self.is_static_frame:
            self.draw_frame()
        else:
            self.timer.setInterval(int(1000 / fps))
            self.update_triangulation_and_colors()
            self.canvas.update()

    def update_render_parameters(self):
        """Обновление параметров отрисовки (цвета, яркость, прозрачность) в реальном времени."""
        logger.info("Обновление параметров отрисовки")
        if len(self.points) == 0:
            width, height, _, _, num_points, _, _ = self.get_parameters()
            self.initialize_points(num_points, width, height)
        else:
            tri = Delaunay(self.points)
            self.simplices = tri.simplices
            if self.triangles_alpha > 0.0:
                base_color = self.get_color()
                self.triangle_colors = initialize_triangle_colors(
                    self.simplices, base_color,
                    self.brightness_range_slider.value(), self.triangle_colors
                )
                new_simplex_keys = set(tuple(sorted(simplex)) for simplex in self.simplices)
                for simplex_key in new_simplex_keys:
                    if simplex_key not in self.triangle_alphas:
                        self.triangle_alphas[simplex_key] = 1.0
                for simplex_key in list(self.triangle_alphas.keys()):
                    if simplex_key not in new_simplex_keys:
                        del self.triangle_alphas[simplex_key]
                        if simplex_key in self.triangle_colors:
                            del self.triangle_colors[simplex_key]
            if self.lines_alpha > 0.0:
                for simplex in self.simplices:
                    for i in range(3):
                        v0, v1 = simplex[i], simplex[(i + 1) % 3]
                        line_key = tuple(sorted([v0, v1]))
                        if line_key not in self.line_alphas:
                            self.line_alphas[line_key] = 1.0
            self.canvas.triangle_colors = self.triangle_colors
            self.canvas.triangle_alphas = self.triangle_alphas
            self.canvas.line_alphas = self.line_alphas
            self.canvas.simplices = self.simplices
            self.canvas.lines_alpha = self.lines_alpha
            self.canvas.triangles_alpha = self.triangles_alpha
            self.canvas.update()

    def update_velocities(self):
        """Обновление скоростей точек без изменения их позиций."""
        logger.info("Обновление скоростей точек")
        if len(self.points) == 0:
            width, height, _, _, num_points, _, _ = self.get_parameters()
            self.initialize_points(num_points, width, height)
            return

        speed = self.get_speed()
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0
        num_total = len(self.points)
        free_points_end = num_total - num_fixed - num_side

        # Обновляем скорости для свободных точек
        if free_points_end > 0:
            current_speeds = np.linalg.norm(self.velocities[:free_points_end], axis=1)
            non_zero = current_speeds > 1e-6  # Избегаем деления на ноль
            if np.any(non_zero):
                # Нормализуем и масштабируем только ненулевые скорости
                normalized_velocities = np.zeros_like(self.velocities[:free_points_end])
                normalized_velocities[non_zero] = (
                    self.velocities[:free_points_end][non_zero] /
                    current_speeds[non_zero][:, np.newaxis]
                ) * speed
                self.velocities[:free_points_end] = normalized_velocities
            else:
                # Если все скорости нулевые, генерируем новые направления
                angles = np.random.uniform(0, 2 * np.pi, free_points_end)
                self.velocities[:free_points_end] = np.vstack([
                    speed * np.cos(angles),
                    speed * np.sin(angles)
                ]).T

        # Обновляем скорости для боковых точек
        if num_side > 0:
            side_idx = num_total - num_side
            side_speed = lambda: np.random.uniform(speed / 4, speed / 2) * np.random.choice([-1, 1])
            for i in [side_idx, side_idx + 1, side_idx + 2, side_idx + 3]:
                current_speed = abs(self.velocities[i, 0]) or side_speed()
                self.velocities[i, 0] = np.sign(self.velocities[i, 0]) * speed / 2 if current_speed != 0 else side_speed()
                self.velocities[i, 1] = 0
            for i in [side_idx + 4, side_idx + 5, side_idx + 6, side_idx + 7]:
                current_speed = abs(self.velocities[i, 1]) or side_speed()
                self.velocities[i, 0] = 0
                self.velocities[i, 1] = np.sign(self.velocities[i, 1]) * speed / 2 if current_speed != 0 else side_speed()

        # Скорости угловых точек остаются нулевыми
        if num_fixed > 0:
            self.velocities[-num_fixed:] = 0

        self.canvas.update()

    def get_points(self):
        return self.points

    def get_velocities(self):
        return self.velocities

    def get_simplices(self):
        return self.simplices

    def get_triangle_colors(self):
        return self.triangle_colors

    def get_triangle_alphas(self):
        return self.triangle_alphas

    def get_line_alphas(self):
        return self.line_alphas

    def get_lines_alpha(self):
        return self.lines_alpha

    def get_triangles_alpha(self):
        return self.triangles_alpha