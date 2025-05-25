import numpy as np
from matplotlib.animation import FuncAnimation
from scipy.spatial import Delaunay
from modules.utils import initialize_points, get_color, initialize_triangle_colors

class AnimationManager:
    """
    Manage animation of points with Delaunay triangulation and customizable rendering options.
    """
    def __init__(self, figure, ax, canvas, get_parameters, fixed_corners_check,
                 show_points_check, show_lines_check, fill_triangles_check,
                 color_slider, point_line_brightness_slider, brightness_range_slider,
                 speed_slider, background_color_slider, background_brightness_slider,
                 side_points_check):
        """
        Initialize the animation manager with UI and plotting components.

        Args:
            figure: Matplotlib figure object.
            ax: Matplotlib axes object.
            canvas: Matplotlib canvas object.
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
            side_points_check: Checkbox for side points.
        """
        self.figure = figure
        self.ax = ax
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

        # Animation variables
        self.points = np.array([])
        self.velocities = np.array([])
        self.anim = None
        self.triangle_colors = {}
        self.current_frame = 0
        self.is_static_frame = False

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

    def draw_frame(self):
        """Draw the current frame based on current points and parameters."""
        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()
        base_hue = self.color_slider.value() / 360.0

        # Update triangle colors if needed
        tri = Delaunay(self.points)
        if self.fill_triangles_check.isChecked():
            self.initialize_triangle_colors(tri.simplices, base_hue)
        else:
            self.triangle_colors = {}

        self.ax.clear()
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_aspect('equal')
        self.ax.set_axis_off()
        self.figure.patch.set_facecolor(self.get_background_color())
        self.ax.set_facecolor(self.get_background_color())

        color = self.get_color()

        if self.show_lines_check.isChecked() or self.fill_triangles_check.isChecked():
            for simplex in tri.simplices:
                triangle = self.points[simplex]
                triangle = np.vstack((triangle, triangle[0:1]))
                simplex_key = tuple(sorted(simplex))
                if self.fill_triangles_check.isChecked() and simplex_key in self.triangle_colors:
                    self.ax.fill(triangle[:, 0], triangle[:, 1], color=self.triangle_colors[simplex_key], zorder=1)
                if self.show_lines_check.isChecked():
                    self.ax.plot(triangle[:, 0], triangle[:, 1], c=color, linewidth=line_width, zorder=2)

        if self.show_points_check.isChecked():
            self.ax.scatter(self.points[:, 0], self.points[:, 1], c=[color], s=point_size, zorder=3)

        self.canvas.draw()

    def generate_single_frame(self):
        """Generate and display a single static frame."""
        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()
        self.initialize_points(num_points, width, height)
        self.current_frame = 0
        self.triangle_colors = {}
        self.is_static_frame = True
        self.draw_frame()

    def update_animation(self):
        """Update animation or static frame with current parameters."""
        if not self.points.any():
            self.start_animation()
            return

        if self.is_static_frame:
            self.draw_frame()
            return

        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()
        base_hue = self.color_slider.value() / 360.0
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0
        speed = self.get_speed()

        # Normalize velocities for free points
        for i in range(len(self.points) - num_fixed - num_side):
            current_speed = np.linalg.norm(self.velocities[i])
            if current_speed > 0:
                self.velocities[i] = (self.velocities[i] / current_speed) * speed

        def update(frame):
            self._update_points()
            self._handle_boundary_collisions(width, height, num_fixed, num_side)

            tri = Delaunay(self.points)
            if self.fill_triangles_check.isChecked():
                self.initialize_triangle_colors(tri.simplices, base_hue)

            self.ax.clear()
            self.ax.set_xlim(0, width)
            self.ax.set_ylim(0, height)
            self.ax.set_aspect('equal')
            self.ax.set_axis_off()
            self.figure.patch.set_facecolor(self.get_background_color())
            self.ax.set_facecolor(self.get_background_color())

            color = self.get_color()

            if self.show_lines_check.isChecked() or self.fill_triangles_check.isChecked():
                for simplex in tri.simplices:
                    triangle = self.points[simplex]
                    triangle = np.vstack((triangle, triangle[0:1]))
                    simplex_key = tuple(sorted(simplex))
                    if self.fill_triangles_check.isChecked() and simplex_key in self.triangle_colors:
                        self.ax.fill(triangle[:, 0], triangle[:, 1], color=self.triangle_colors[simplex_key], zorder=1)
                    if self.show_lines_check.isChecked():
                        self.ax.plot(triangle[:, 0], triangle[:, 1], c=color, linewidth=line_width, zorder=2)

            if self.show_points_check.isChecked():
                self.ax.scatter(self.points[:, 0], self.points[:, 1], c=[color], s=point_size, zorder=3)

            self.current_frame = frame
            return []

        if self.anim:
            self.anim.event_source.stop()
        self.anim = FuncAnimation(self.figure, update, frames=int(fps * duration),
                                 interval=1000 / fps, blit=True)
        self.canvas.draw()

    def start_animation(self):
        """Start the animation from scratch."""
        self.is_static_frame = False
        width, height, fps, duration, num_points, point_size, line_width = self.get_parameters()
        self.initialize_points(num_points, width, height)
        self.current_frame = 0
        self.triangle_colors = {}

        base_hue = self.color_slider.value() / 360.0
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0

        def update(frame):
            self._update_points()
            self._handle_boundary_collisions(width, height, num_fixed, num_side)

            tri = Delaunay(self.points)
            if self.fill_triangles_check.isChecked():
                self.initialize_triangle_colors(tri.simplices, base_hue)

            self.ax.clear()
            self.ax.set_xlim(0, width)
            self.ax.set_ylim(0, height)
            self.ax.set_aspect('equal')
            self.ax.set_axis_off()
            self.figure.patch.set_facecolor(self.get_background_color())
            self.ax.set_facecolor(self.get_background_color())

            color = self.get_color()

            if self.show_lines_check.isChecked() or self.fill_triangles_check.isChecked():
                for simplex in tri.simplices:
                    triangle = self.points[simplex]
                    triangle = np.vstack((triangle, triangle[0:1]))
                    simplex_key = tuple(sorted(simplex))
                    if self.fill_triangles_check.isChecked() and simplex_key in self.triangle_colors:
                        self.ax.fill(triangle[:, 0], triangle[:, 1], color=self.triangle_colors[simplex_key], zorder=1)
                    if self.show_lines_check.isChecked():
                        self.ax.plot(triangle[:, 0], triangle[:, 1], c=color, linewidth=line_width, zorder=2)

            if self.show_points_check.isChecked():
                self.ax.scatter(self.points[:, 0], self.points[:, 1], c=[color], s=point_size, zorder=3)

            self.current_frame = frame
            return []

        if self.anim:
            self.anim.event_source.stop()
        self.anim = FuncAnimation(self.figure, update, frames=int(fps * duration),
                                 interval=1000 / fps, blit=True)
        self.canvas.draw()

    def stop_animation(self):
        """Stop the current animation and keep the current frame."""
        if self.anim:
            self.anim.event_source.stop()
            self.anim = None
            self.is_static_frame = True
            self.draw_frame()