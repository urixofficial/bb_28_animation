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
                 show_lines_check, fill_triangles_check, color_slider,
                 point_line_brightness_slider, brightness_range_slider, speed_slider,
                 background_color_slider, background_brightness_slider, side_points_check):
        """
        Инициализация менеджера анимации.

        Args:
            canvas: QOpenGLWidget для рендеринга.
            get_parameters: Функция для получения параметров анимации.
            fixed_corners_check: Флажок для фиксированных угловых точек.
            show_points_check: Флажок для отображения точек.
            show_lines_check: Флажок для отображения линий.
            fill_triangles_check: Флажок для заливки треугольников.
            color_slider: Слайдер для оттенка цвета точек/линий.
            point_line_brightness_slider: Слайдер для яркости точек/линий.
            brightness_range_slider: Слайдер для диапазона яркости треугольников.
            speed_slider: Слайдер для скорости анимации.
            background_color_slider: Слайдер для оттенка цвета фона.
            background_brightness_slider: Слайдер для яркости фона.
            side_points_check: Флажок для боковых точек.
        """
        self.canvas = canvas
        self.get_parameters = get_parameters
        self.fixed_corners_check = fixed_corners_check
        self.show_points_check = show_points_check
        self.show_lines_check = show_lines_check
        self.fill_triangles_check = fill_triangles_check
        self.color_slider = color_slider
        self.point_line_brightness_slider = point_line_brightness_slider
        self.brightness_range_slider = brightness_range_slider
        self.speed_slider = speed_slider
        self.background_color_slider = background_color_slider
        self.background_brightness_slider = background_brightness_slider
        self.side_points_check = side_points_check
        self.points = np.array([])
        self.velocities = np.array([])
        self.triangle_colors = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_static_frame = False

    def initialize_points(self, num_points, width, height):
        """Инициализация точек и их скоростей."""
        logger.info(f"Инициализация {num_points} точек на холсте {width}x{height}")
        self.points, self.velocities = initialize_points(
            num_points, width, height, self.fixed_corners_check.isChecked(),
            self.side_points_check.isChecked(), self.get_speed()
        )
        tri = Delaunay(self.points)
        self.canvas.simplices = tri.simplices
        self.triangle_colors = initialize_triangle_colors(
            tri.simplices, self.color_slider.value() / 360.0,
            self.brightness_range_slider.value(), {}
        )

    def get_speed(self):
        """Получение скорости анимации."""
        return self.speed_slider.value()

    def get_color(self):
        """Получение RGB цвета для точек и линий."""
        return get_color(self.color_slider.value(), self.point_line_brightness_slider.value())

    def get_background_color(self):
        """Получение RGB цвета для фона."""
        return get_color(self.background_color_slider.value(), self.background_brightness_slider.value())

    def _update_points(self):
        """Обновление позиций точек на основе скоростей."""
        self.points += self.velocities

    def _handle_boundary_collisions(self, width, height, num_fixed, num_side):
        """Обработка столкновений точек с границами холста."""
        free_points = self.points[:-num_fixed - num_side]
        free_velocities = self.velocities[:-num_fixed - num_side]
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

    def update_frame(self):
        """Обновление кадра анимации."""
        if self.is_static_frame:
            return
        width, height, fps, _, num_points, point_size, line_width = self.get_parameters()
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0
        self._update_points()
        self._handle_boundary_collisions(width, height, num_fixed, num_side)
        tri = Delaunay(self.points)
        self.canvas.points = self.points
        self.canvas.simplices = tri.simplices
        if self.fill_triangles_check.isChecked():
            self.triangle_colors = initialize_triangle_colors(
                tri.simplices, self.color_slider.value() / 360.0,
                self.brightness_range_slider.value(), self.triangle_colors
            )
            self.canvas.triangle_colors = self.triangle_colors
        self.canvas.update()

    def draw_frame(self):
        """Отрисовка текущего кадра."""
        self.canvas.update()

    def generate_single_frame(self):
        """Генерация и отрисовка одиночного кадра."""
        logger.info("Генерация одиночного кадра")
        width, height, _, _, num_points, _, _ = self.get_parameters()
        self.initialize_points(num_points, width, height)
        self.is_static_frame = True
        self.canvas.points = self.points
        self.draw_frame()

    def start_animation(self):
        """Запуск анимации с нуля."""
        logger.info("Запуск анимации")
        self.is_static_frame = False
        width, height, fps, _, num_points, _, _ = self.get_parameters()
        self.initialize_points(num_points, width, height)
        self.canvas.points = self.points
        self.timer.start(int(1000 / fps))

    def stop_animation(self):
        """Остановка анимации с сохранением текущего кадра."""
        logger.info("Остановка анимации")
        self.timer.stop()
        self.is_static_frame = True
        self.draw_frame()

    def update_animation(self):
        """Обновление анимации или статического кадра."""
        if self.is_static_frame:
            self.draw_frame()
        else:
            width, height, fps, _, _, _, _ = self.get_parameters()
            self.timer.setInterval(int(1000 / fps))
            self.canvas.update()