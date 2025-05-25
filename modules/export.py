import os
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QCoreApplication
import numpy as np
from modules.utils import initialize_points, get_color, initialize_triangle_colors
import matplotlib.animation as animation
import logging

logging.basicConfig(level=logging.INFO, filename='../video_generator.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
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

    def _render_frame(self, ax, width, height, point_size, line_width, base_hue):
        """Render a single frame of the animation."""
        ax.clear()
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')
        ax.set_axis_off()
        ax.set_facecolor(self.get_background_color())

        tri = Delaunay(self.points)
        if self.fill_triangles_check.isChecked():
            self.initialize_triangle_colors(tri.simplices, base_hue)

        color = self.get_color()

        if self.show_lines_check.isChecked() or self.fill_triangles_check.isChecked():
            for simplex in tri.simplices:
                triangle = self.points[simplex]
                triangle = np.vstack((triangle, triangle[0:1]))
                simplex_key = tuple(sorted(simplex))
                if self.fill_triangles_check.isChecked() and simplex_key in self.triangle_colors:
                    ax.fill(triangle[:, 0], triangle[:, 1], color=self.triangle_colors[simplex_key], zorder=1)
                if self.show_lines_check.isChecked():
                    ax.plot(triangle[:, 0], triangle[:, 1], c=color, linewidth=line_width, zorder=2)

        if self.show_points_check.isChecked():
            ax.scatter(self.points[:, 0], self.points[:, 1], c=[color], s=point_size, zorder=3)

    def export_frame(self):
        """Export the current frame as a PNG file."""
        logger.info("Starting frame export...")
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
        ax.set_facecolor(self.get_background_color())
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')
        ax.set_axis_off()

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
            logger.warning("Frame export canceled")
            self.progress_bar.setValue(0)
            plt.close(fig)
            return

        try:
            logger.info(f"Saving frame to {file_path}")
            fig.savefig(file_path, format='png', bbox_inches='tight', pad_inches=0)
            self.progress_bar.setValue(100)
            QCoreApplication.processEvents()
            logger.info(f"Frame successfully saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving frame: {e}")
        finally:
            plt.close(fig)
            self.progress_bar.setValue(0)
            QCoreApplication.processEvents()

    def _save_animation(self, anim, file_path, selected_filter, fps, total_frames):
        """Save the animation to a file (MP4 or PNG sequence)."""
        ffmpeg_available = 'ffmpeg' in animation.writers.list()
        output_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            if selected_filter.startswith("MP4 Video") and ffmpeg_available:
                writer = animation.FFMpegWriter(
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
                logger.info(f"Saving MP4 to {file_path} with fps={fps}, bitrate=5000")
                anim.save(file_path, writer=writer)
                self.progress_bar.setValue(100)
                QCoreApplication.processEvents()
                logger.info(f"MP4 successfully saved to {file_path}")
            elif selected_filter.startswith("PNG Sequence"):
                logger.info(f"Saving PNG sequence to {output_dir}/{base_name}_XXXX.png")
                anim.save(f"{output_dir}/{base_name}_%04d.png", writer='pillow', fps=fps)
                self.progress_bar.setValue(100)
                QCoreApplication.processEvents()
                logger.info(f"PNG sequence saved to {output_dir}/{base_name}_XXXX.png")
                if ffmpeg_available:
                    logger.info("To convert PNG sequence to MP4 with accurate colors, run:")
                    logger.info(f'ffmpeg -framerate {fps} -i "{output_dir}/{base_name}_%04d.png" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 15 -vf colormatrix=smpte170m:bt709 -colorspace bt709 "{output_dir}/{base_name}.mp4"')
            else:
                if not ffmpeg_available and selected_filter.startswith("MP4 Video"):
                    logger.error("ffmpeg not available. Install ffmpeg and ensure it is in PATH.")
                    logger.info(f"Falling back to PNG sequence export: {output_dir}/{base_name}_XXXX.png")
                    anim.save(f"{output_dir}/{base_name}_%04d.png", writer='pillow', fps=fps)
                    self.progress_bar.setValue(100)
                    QCoreApplication.processEvents()
                    logger.info(f"PNG sequence saved to {output_dir}/{base_name}_XXXX.png")
                    logger.info("To convert PNG sequence to MP4, run:")
                    logger.info(f'ffmpeg -framerate {fps} -i "{output_dir}/{base_name}_%04d.png" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 15 -vf colormatrix=smpte170m:bt709 -colorspace bt709 "{output_dir}/{base_name}.mp4"')
                else:
                    logger.error("Unsupported file format selected.")
        except Exception as e:
            logger.error(f"Error saving animation: {e}")
            if not ffmpeg_available and selected_filter.startswith("MP4 Video"):
                logger.error("ffmpeg not found. Install ffmpeg and ensure it is in PATH.")
                logger.info("Alternatively, select PNG sequence for export and convert manually.")

    def export_animation(self):
        """Export animation as MP4 or PNG sequence."""
        logger.info("Starting export process...")
        self.progress_bar.setValue(0)
        QCoreApplication.processEvents()
        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()
        self.initialize_points(num_points, width, height)
        self.triangle_colors = {}

        base_hue = self.color_slider.value() / 360.0
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0

        tri = Delaunay(self.points)
        if self.fill_triangles_check.isChecked():
            self.initialize_triangle_colors(tri.simplices, base_hue)

        self.progress_bar.setValue(10)
        QCoreApplication.processEvents()

        fig, ax = plt.subplots(figsize=(width / 100, height / 100))
        fig.patch.set_facecolor(self.get_background_color())
        ax.set_facecolor(self.get_background_color())

        total_frames = int(fps * duration)
        logger.info(f"Creating animation: {fps} fps, {duration} seconds, {total_frames} frames")

        def update(frame):
            self._update_points()
            self._handle_boundary_collisions(width, height, num_fixed, num_side)
            self._render_frame(ax, width, height, point_size, line_width, base_hue)

            progress = int((frame + 1) / total_frames * 90) + 10
            self.progress_bar.setValue(progress)
            QCoreApplication.processEvents()
            return []

        try:
            anim = animation.FuncAnimation(fig, update, frames=total_frames, interval=1000 / fps)
        except Exception as e:
            logger.error(f"Error creating animation: {e}")
            self.progress_bar.setValue(0)
            plt.close(fig)
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            None, "Save Animation", "", "MP4 Video (*.mp4);;PNG Sequence (*.png)"
        )

        if not file_path:
            logger.warning("Export canceled")
            self.progress_bar.setValue(0)
            plt.close(fig)
            return

        logger.info(f"Selected file: {file_path}, format: {selected_filter}")
        try:
            self._save_animation(anim, file_path, selected_filter, fps, total_frames)
        finally:
            self.progress_bar.setValue(0)
            QCoreApplication.processEvents()
            plt.close(fig)