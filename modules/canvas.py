from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from modules.utils import initialize_points, get_color, initialize_triangle_colors
from modules.config_manager import ConfigManager
from loguru import logger
import numpy as np
from scipy.spatial import Delaunay

class OpenGLCanvas(QOpenGLWidget):
    def __init__(self, parent, get_parameters, ui):
        super().__init__(parent)
        self.get_parameters = get_parameters
        self.ui = ui
        self.points = np.array([])
        self.velocities = np.array([])
        self.triangle_colors = {}
        self.triangle_alphas = {}  # Альфа-значения для каждого симплекса
        self.line_alphas = {}  # Альфа-значения для каждой линии
        self.simplices = []
        self.lines_alpha = 0.0  # По умолчанию 0.0, будет обновлено AnimationManager
        self.triangles_alpha = 0.0  # По умолчанию 0.0, будет обновлено AnimationManager
        config_manager = ConfigManager('config.ini')
        self.setMinimumSize(
            config_manager.get_int('Window', 'min_width', 400),
            config_manager.get_int('Window', 'min_height', 400)
        )

    def initializeGL(self):
        """Инициализация OpenGL."""
        try:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Стандартное альфа-смешивание
            glEnable(GL_POINT_SMOOTH)
            glEnable(GL_LINE_SMOOTH)
            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                logger.error(f"Фреймбуфер не полный, статус: {status}")
            logger.debug("OpenGL инициализирован успешно")
        except Exception as e:
            logger.error(f"Ошибка инициализации OpenGL: {e}")

    def resizeGL(self, w, h):
        """Обработка изменения размера окна с сохранением соотношения сторон."""
        try:
            if w <= 0 or h <= 0:
                logger.warning(f"Некорректные размеры окна: {w}x{h}, пропуск")
                return
            width, height, _, _, _, _, _ = self.get_parameters()
            if width <= 0 or height <= 0:
                logger.warning(f"Некорректные размеры: {width}x{height}, используется 1080x1080")
                width, height = 1080, 1080
            aspect_ratio = width / height

            window_aspect = w / h
            if window_aspect > aspect_ratio:
                view_width = h * aspect_ratio
                view_height = h
                offset_x = (w - view_width) / 2
                offset_y = 0
            else:
                view_width = w
                view_height = w / aspect_ratio
                offset_x = 0
                offset_y = (h - view_height) / 2

            view_width = max(1, min(int(view_width), 4096))
            view_height = max(1, min(int(view_height), 4096))
            offset_x = max(0, int(offset_x))
            offset_y = max(0, int(offset_y))

            glViewport(offset_x, offset_y, view_width, view_height)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluOrtho2D(0, width, 0, height)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            logger.debug(f"ResizeGL: window={w}x{h}, viewport=({offset_x}, {offset_y}, {view_width}x{view_height})")
        except Exception as e:
            logger.error(f"Ошибка в resizeGL: {e}")

    def paintGL(self):
        """Рендеринг кадра с использованием OpenGL."""
        try:
            glClear(GL_COLOR_BUFFER_BIT)
            width, height, _, _, num_points, point_size, line_width = self.get_parameters()
            if width <= 0 or height <= 0:
                logger.warning(f"Некорректные размеры в paintGL: {width}x{height}, используется 1080x1080")
                width, height = 1080, 1080
            color = get_color(self.ui.main_hue_slider.value(),
                             self.ui.main_saturation_slider.value(),
                             self.ui.main_value_slider.value())
            bg_color = get_color(self.ui.bg_hue_slider.value(),
                                self.ui.bg_saturation_slider.value(),
                                self.ui.bg_value_slider.value())
            glClearColor(*bg_color, 1.0)

            if len(self.points) == 0:
                self.points, self.velocities = initialize_points(
                    num_points, width, height,
                    self.ui.fixed_corners_check.isChecked(),
                    self.ui.side_points_check.isChecked(),
                    self.ui.speed_slider.value()
                )
                tri = Delaunay(self.points)
                self.simplices = tri.simplices
                self.triangle_colors = initialize_triangle_colors(
                    self.simplices, color,
                    self.ui.brightness_range_slider.value(), {}
                )
                for simplex in self.simplices:
                    simplex_key = tuple(sorted(simplex))
                    self.triangle_alphas[simplex_key] = 1.0
                for simplex in self.simplices:
                    for i in range(3):
                        v0, v1 = simplex[i], simplex[(i + 1) % 3]
                        line_key = tuple(sorted([v0, v1]))
                        self.line_alphas[line_key] = 1.0
                logger.debug("Инициализированы точки и триангуляция")

            # Рендеринг треугольников
            if self.triangles_alpha > 0.0:
                logger.debug("Рендеринг треугольников с альфа-смешиванием")
                glBegin(GL_TRIANGLES)
                for simplex in self.simplices:
                    simplex_key = tuple(sorted(simplex))
                    if simplex_key in self.triangle_colors and simplex_key in self.triangle_alphas:
                        r, g, b, _ = self.triangle_colors[simplex_key]
                        alpha = self.triangle_alphas[simplex_key] * self.triangles_alpha
                        glColor4f(r, g, b, alpha)
                        for vertex in simplex:
                            glVertex2f(self.points[vertex, 0], self.points[vertex, 1])
                glEnd()

            # Рендеринг линий
            if self.lines_alpha > 0.0:
                logger.debug("Рендеринг линий с альфа-смешиванием")
                glLineWidth(line_width)
                glBegin(GL_LINES)
                for simplex in self.simplices:
                    for i in range(3):
                        v0, v1 = simplex[i], simplex[(i + 1) % 3]
                        line_key = tuple(sorted([v0, v1]))
                        if line_key in self.line_alphas:
                            alpha = self.line_alphas[line_key] * self.lines_alpha
                            glColor4f(*color, alpha)
                            glVertex2f(self.points[v0, 0], self.points[v0, 1])
                            glVertex2f(self.points[v1, 0], self.points[v1, 1])
                glEnd()

            # Рендеринг точек
            if self.ui.show_points_check.isChecked():
                logger.debug("Рендеринг точек с альфа-смешиванием")
                glPointSize(point_size / 10.0)
                glBegin(GL_POINTS)
                glColor4f(*color, 1.0)
                for point in self.points:
                    glVertex2f(point[0], point[1])
                glEnd()

        except Exception as e:
            logger.error(f"Ошибка в paintGL: {e}")

    def update_frame(self):
        """Обновление кадра."""
        try:
            self.update()
        except Exception as e:
            logger.error(f"Ошибка в update_frame: {e}")