import os
import numpy as np
from scipy.spatial import Delaunay
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QCoreApplication
from modules.utils import initialize_points, get_color, initialize_triangle_colors
from PIL import Image
import pygame
from loguru import logger

class ExportManager:
    """
    Управление экспортом кадров или анимаций с настраиваемыми параметрами рендеринга.
    """
    def __init__(self, get_parameters, fixed_corners_check, show_points_check,
                 show_lines_check, fill_triangles_check, color_slider,
                 point_line_brightness_slider, brightness_range_slider, speed_slider,
                 background_color_slider, background_brightness_slider, progress_bar,
                 side_points_check):
        """
        Инициализация менеджера экспорта.

        Args:
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
            progress_bar: Прогресс-бар для обратной связи при экспорте.
            side_points_check: Флажок для боковых точек.
        """
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
        self.progress_bar = progress_bar
        self.side_points_check = side_points_check
        self.points = None
        self.velocities = None
        self.triangle_colors = {}

    def initialize_points(self, num_points, width, height):
        """Инициализация точек и их скоростей."""
        logger.info(f"Инициализация {num_points} точек для экспорта на холсте {width}x{height}")
        self.points, self.velocities = initialize_points(
            num_points, width, height, self.fixed_corners_check.isChecked(),
            self.side_points_check.isChecked(), self.get_speed()
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

    def initialize_triangle_colors(self, simplices, base_hue):
        """Инициализация или обновление цветов треугольников."""
        self.triangle_colors = initialize_triangle_colors(
            simplices, base_hue, self.brightness_range_slider.value(), self.triangle_colors
        )

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

    def _render_frame(self, width, height, point_size, line_width, base_hue):
        """Рендеринг одного кадра анимации с использованием Pygame."""
        pygame.init()
        surface = pygame.Surface((width, height))
        surface.fill([int(c * 255) for c in self.get_background_color()])

        tri = Delaunay(self.points)
        if self.fill_triangles_check.isChecked():
            self.initialize_triangle_colors(tri.simplices, base_hue)

        # Рендеринг треугольников и линий
        for simplex in tri.simplices:
            triangle = self.points[simplex]
            triangle = np.vstack((triangle, triangle[0:1])).astype(int)
            simplex_key = tuple(sorted(simplex))
            if self.fill_triangles_check.isChecked() and simplex_key in self.triangle_colors:
                pygame.draw.polygon(surface, [int(c * 255) for c in self.triangle_colors[simplex_key]],
                                   [(p[0], height - p[1]) for p in triangle[:-1]])
            if self.show_lines_check.isChecked():
                pygame.draw.lines(surface, [int(c * 255) for c in self.get_color()], True,
                                 [(p[0], height - p[1]) for p in triangle], int(line_width))

        # Рендеринг точек
        if self.show_points_check.isChecked():
            for point in self.points:
                pygame.draw.circle(surface, [int(c * 255) for c in self.get_color()],
                                  (int(point[0]), int(height - point[1])), int(point_size / 10))

        return pygame.surfarray.array3d(surface).swapaxes(0, 1)

    def export_frame(self):
        """Экспорт текущего кадра в PNG."""
        logger.info("Начало экспорта кадра")
        self.progress_bar.setValue(0)
        QCoreApplication.processEvents()
        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()

        if self.points is None or len(self.points) == 0:
            self.progress_bar.setValue(20)
            QCoreApplication.processEvents()
            self.initialize_points(num_points, width, height)
            self.triangle_colors = {}
            tri = Delaunay(self.points)
            base_hue = self.color_slider.value() / 360.0
            if self.fill_triangles_check.isChecked():
                self.initialize_triangle_colors(tri.simplices, base_hue)
            self.progress_bar.setValue(40)
            QCoreApplication.processEvents()

        base_hue = self.color_slider.value() / 360.0
        frame_data = self._render_frame(width, height, point_size, line_width, base_hue)
        self.progress_bar.setValue(60)
        QCoreApplication.processEvents()

        file_path, _ = QFileDialog.getSaveFileName(None, "Save Frame", "", "PNG Image (*.png)")
        if not file_path:
            logger.warning("Экспорт кадра отменен")
            self.progress_bar.setValue(0)
            return

        try:
            logger.info(f"Сохранение кадра в {file_path}")
            Image.fromarray(frame_data).save(file_path, format='PNG')
            self.progress_bar.setValue(100)
            QCoreApplication.processEvents()
            logger.info(f"Кадр успешно сохранен в {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кадра: {e}")
        finally:
            self.progress_bar.setValue(0)
            QCoreApplication.processEvents()

    def export_animation(self):
        """Экспорт анимации как последовательности PNG."""
        logger.info("Начало экспорта анимации")
        self.progress_bar.setValue(0)
        QCoreApplication.processEvents()
        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()
        total_frames = int(fps * duration)
        self.initialize_points(num_points, width, height)
        self.triangle_colors = {}
        base_hue = self.color_slider.value() / 360.0
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0

        file_path, selected_filter = QFileDialog.getSaveFileName(
            None, "Save Animation", "", "PNG Sequence (*.png)"
        )
        if not file_path:
            logger.warning("Экспорт анимации отменен")
            self.progress_bar.setValue(0)
            return

        output_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        for frame in range(total_frames):
            self._update_points()
            self._handle_boundary_collisions(width, height, num_fixed, num_side)
            frame_data = self._render_frame(width, height, point_size, line_width, base_hue)
            try:
                Image.fromarray(frame_data).save(f"{output_dir}/{base_name}_{frame:04d}.png", format='PNG')
                self.progress_bar.setValue(int((frame + 1) / total_frames * 100))
                QCoreApplication.processEvents()
            except Exception as e:
                logger.error(f"Ошибка при сохранении кадра {frame}: {e}")
        logger.info(f"Последовательность PNG сохранена в {output_dir}/{base_name}_XXXX.png")
        logger.info(f"Для конвертации в MP4 выполните: ffmpeg -framerate {fps} -i \"{output_dir}/{base_name}_%04d.png\" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 15 \"{output_dir}/{base_name}.mp4\"")
        self.progress_bar.setValue(0)