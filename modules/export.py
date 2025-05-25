import os
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QCoreApplication
import numpy as np
from modules.utils import initialize_points, get_color, initialize_triangle_colors
import matplotlib.animation as animation
import logging

logger = logging.getLogger(__name__)

class ExportManager:
    """
    Manage export of animation frames or videos with customizable rendering options.
    """
    def __init__(self, get_parameters, fixed_corners_check, show_points_check,
                 show_lines_check, fill_triangles_check, color_slider,
                 point_line_brightness_slider, brightness_range_slider, speed_slider,
                 background_color_slider, background_brightness_slider, progress_bar,
                 side_points_check):
        """
        Initialize the export manager with UI components and parameter function.

        Args:
            get_parameters: Function to retrieve animation parameters.
            fixed_corners_check: Checkbox for fixed corner points.
            show_points_check: Checkbox for showing points.
            show_lines_check: Checkbox for showing lines.
            fill_triangles_check: Checkbox for filling triangles.
            color_slider: Slider for point/line color hue.
            point_line_brightness_slider: Slider for point/line brightness.
            brightness_range_slider: Slider for triangle brightness range.
            speed_slider: Slider for animation speed.
            background_color_slider: Slider for background color hue.
            background_brightness_slider: Slider for background brightness.
            progress_bar: Progress bar for export feedback.
            side_points_check: Checkbox for side points.
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
        """Initialize points and velocities using utility function."""
        logger.info(f"Инициализация {num_points} точек для экспорта на холсте {width}x{height}")
        self.points, self.velocities = initialize_points(
            num_points, width, height, self.fixed_corners_check.isChecked(),
            self.side_points_check.isChecked(), self.get_speed()
        )

    def get_speed(self):
        """Retrieve animation speed from the speed slider."""
        return self.speed_slider.value()

    def get_color(self):
        """Get RGB color for points and lines from sliders."""
        return get_color(self.color_slider.value(), self.point_line_brightness_slider.value())

    def get_background_color(self):
        """Get RGB color for background from sliders."""
        return get_color(self.background_color_slider.value(), self.background_brightness_slider.value())

    def initialize_triangle_colors(self, simplices, base_hue):
        """Initialize or update triangle colors using utility function."""
        self.triangle_colors = initialize_triangle_colors(
            simplices, base_hue, self.brightness_range_slider.value(), self.triangle_colors
        )

    def _update_points(self):
        """Update point positions based on velocities."""
        self.points += self.velocities

    def _handle_boundary_collisions(self, width, height, num_fixed, num_side):
        """Handle collisions of points with canvas boundaries using vectorized operations."""
        # Free points
        free_points = self.points[:-num_fixed - num_side]
        free_velocities = self.velocities[:-num_fixed - num_side]
        mask_x = (free_points[:, 0] < 0) | (free_points[:, 0] > width)
        mask_y = (free_points[:, 1] < 0) | (free_points[:, 1] > height)
        free_velocities[:, 0][mask_x] *= -1
        free_velocities[:, 1][mask_y] *= -1

        # Side points (if any)
        if num_side > 0:
            side_idx = len(self.points) - num_side
            # Bottom and top sides (horizontal movement)
            for i in [side_idx, side_idx + 1, side_idx + 2, side_idx + 3]:
                if self.points[i, 0] < 0 or self.points[i, 0] > width:
                    self.velocities[i, 0] *= -1
            # Left and right sides (vertical movement)
            for i in [side_idx + 4, side_idx + 5, side_idx + 6, side_idx + 7]:
                if self.points[i, 1] < 0 or self.points[i, 1] > height:
                    self.velocities[i, 1] *= -1

    def _setup_canvas(self, ax, width, height):
        """Set up the canvas with the specified dimensions and background color."""
        logger.debug("Настройка холста для экспорта")
        ax.clear()
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')
        ax.set_axis_off()
        ax.set_facecolor(self.get_background_color())

    def _render_triangles(self, ax, simplices, color, line_width):
        """Render triangles with optional filling and lines."""
        for simplex in simplices:
            triangle = self.points[simplex]
            triangle = np.vstack((triangle, triangle[0:1]))
            simplex_key = tuple(sorted(simplex))
            if self.fill_triangles_check.isChecked() and simplex_key in self.triangle_colors:
                ax.fill(triangle[:, 0], triangle[:, 1], color=self.triangle_colors[simplex_key], zorder=1)
            if self.show_lines_check.isChecked():
                ax.plot(triangle[:, 0], triangle[:, 1], c=color, linewidth=line_width, zorder=2)

    def _render_points(self, ax, color, point_size):
        """Render points if enabled."""
        if self.show_points_check.isChecked():
            ax.scatter(self.points[:, 0], self.points[:, 1], c=[color], s=point_size, zorder=3)

    def _render_frame(self, ax, width, height, point_size, line_width, base_hue):
        """Render a single frame of the animation."""
        logger.debug("Отрисовка кадра для экспорта")
        tri = Delaunay(self.points)
        if self.fill_triangles_check.isChecked():
            self.initialize_triangle_colors(tri.simplices, base_hue)

        self._setup_canvas(ax, width, height)
        color = self.get_color()
        self._render_triangles(ax, tri.simplices, color, line_width)
        self._render_points(ax, color, point_size)
        logger.debug("Кадр для экспорта отрисован")

    def export_frame(self):
        """Export the current frame as a PNG file."""
        logger.info("Начало экспорта кадра")
        self.progress_bar.setValue(0)
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

        fig, ax = plt.subplots(figsize=(width / 100, height / 100))
        fig.patch.set_facecolor(self.get_background_color())
        self.progress_bar.setValue(60)
        QCoreApplication.processEvents()

        base_hue = self.color_slider.value() / 360.0
        self._render_frame(ax, width, height, point_size, line_width, base_hue)

        self.progress_bar.setValue(80)
        QCoreApplication.processEvents()

        file_path, _ = QFileDialog.getSaveFileName(
            None, "Save Frame", "", "PNG Image (*.png)"
        )

        if not file_path:
            logger.warning("Экспорт кадра отменен")
            self.progress_bar.setValue(0)
            plt.close(fig)
            return

        try:
            logger.info(f"Сохранение кадра в {file_path}")
            fig.savefig(file_path, format='png', bbox_inches='tight', pad_inches=0)
            self.progress_bar.setValue(100)
            QCoreApplication.processEvents()
            logger.info(f"Кадр успешно сохранен в {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кадра: {e}")
        finally:
            plt.close(fig)
            self.progress_bar.setValue(0)
            QCoreApplication.processEvents()

    def _configure_writer(self, selected_filter, fps):
        """Configure the animation writer based on the selected format."""
        ffmpeg_available = 'ffmpeg' in animation.writers.list()
        if selected_filter.startswith("MP4 Video") and ffmpeg_available:
            return animation.FFMpegWriter(
                fps=fps,
                bitrate=5000,
                extra_args=[
                    '-pix_fmt', 'yuv420p',
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '15',
                    '-vf', 'colormatrix=smpte170m:bt709',
                    '-colorspace', 'bt709'
                ]
            )
        return animation.PillowWriter(fps=fps)

    def _save_animation(self, anim, file_path, selected_filter, fps, total_frames):
        """Save the animation to a file (MP4 or PNG sequence)."""
        self.progress_bar.setValue(10)
        QCoreApplication.processEvents()
        output_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        writer = self._configure_writer(selected_filter, fps)

        try:
            if selected_filter.startswith("MP4 Video") and 'ffmpeg' in animation.writers.list():
                logger.info(f"Сохранение MP4 в {file_path} с fps={fps}, bitrate=5000")
                anim.save(file_path, writer=writer, progress_callback=lambda i, n: self._update_progress(i, n, total_frames))
                logger.info(f"MP4 успешно сохранен в {file_path}")
            else:
                logger.info(f"Сохранение последовательности PNG в {output_dir}/{base_name}_XXXX.png")
                anim.save(f"{output_dir}/{base_name}_%04d.png", writer=writer, progress_callback=lambda i, n: self._update_progress(i, n, total_frames))
                logger.info(f"Последовательность PNG сохранена в {output_dir}/{base_name}_XXXX.png")
                if 'ffmpeg' in animation.writers.list():
                    logger.info("Для конвертации PNG в MP4 с точными цветами выполните:")
                    logger.info(f'ffmpeg -framerate {fps} -i "{output_dir}/{base_name}_%04d.png" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 15 -vf colormatrix=smpte170m:bt709 -colorspace bt709 "{output_dir}/{base_name}.mp4"')
                else:
                    logger.warning("ffmpeg недоступен. Установите ffmpeg и убедитесь, что он в PATH.")
                    logger.info("Для конвертации PNG в MP4 выполните:")
                    logger.info(f'ffmpeg -framerate {fps} -i "{output_dir}/{base_name}_%04d.png" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 15 -vf colormatrix=smpte170m:bt709 -colorspace bt709 "{output_dir}/{base_name}.mp4"')
        except Exception as e:
            logger.error(f"Ошибка при сохранении анимации: {e}")
            if not ('ffmpeg' in animation.writers.list()) and selected_filter.startswith("MP4 Video"):
                logger.error("ffmpeg не найден. Установите ffmpeg и убедитесь, что он в PATH.")
        finally:
            self.progress_bar.setValue(100)
            QCoreApplication.processEvents()

    def _update_progress(self, frame, total, total_frames):
        """Update the progress bar during animation saving."""
        progress = int((frame + 1) / total_frames * 90) + 10
        self.progress_bar.setValue(progress)
        QCoreApplication.processEvents()

    def _initialize_animation(self, width, height, fps, duration, num_points):
        """Initialize points and animation parameters."""
        logger.info(f"Инициализация анимации: {fps} fps, {duration} секунд, {num_points} точек")
        self.initialize_points(num_points, width, height)
        self.triangle_colors = {}
        base_hue = self.color_slider.value() / 360.0
        tri = Delaunay(self.points)
        if self.fill_triangles_check.isChecked():
            self.initialize_triangle_colors(tri.simplices, base_hue)
        return int(fps * duration)

    def _update_frame(self, frame, ax, width, height, num_fixed, num_side, base_hue, point_size, line_width):
        """Update and render a single animation frame for export."""
        self._update_points()
        self._handle_boundary_collisions(width, height, num_fixed, num_side)
        self._render_frame(ax, width, height, point_size, line_width, base_hue)
        return []

    def export_animation(self):
        """Export animation as MP4 or PNG sequence."""
        logger.info("Начало экспорта анимации")
        self.progress_bar.setValue(0)
        QCoreApplication.processEvents()
        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()
        total_frames = self._initialize_animation(width, height, fps, duration, num_points)
        self.progress_bar.setValue(10)
        QCoreApplication.processEvents()

        fig, ax = plt.subplots(figsize=(width / 100, height / 100))
        fig.patch.set_facecolor(self.get_background_color())

        base_hue = self.color_slider.value() / 360.0
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0

        def update(frame):
            return self._update_frame(frame, ax, width, height, num_fixed, num_side, base_hue, point_size, line_width)

        try:
            anim = animation.FuncAnimation(fig, update, frames=total_frames, interval=1000 / fps)
        except Exception as e:
            logger.error(f"Ошибка при создании анимации: {e}")
            self.progress_bar.setValue(0)
            plt.close(fig)
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            None, "Save Animation", "", "MP4 Video (*.mp4);;PNG Sequence (*.png)"
        )

        if not file_path:
            logger.warning("Экспорт анимации отменен")
            self.progress_bar.setValue(0)
            plt.close(fig)
            return

        logger.info(f"Выбран файл: {file_path}, формат: {selected_filter}")
        try:
            self._save_animation(anim, file_path, selected_filter, fps, total_frames)
        finally:
            self.progress_bar.setValue(0)
            QCoreApplication.processEvents()
            plt.close(fig)