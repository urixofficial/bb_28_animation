from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QSlider, QCheckBox, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLU import *
from modules.config_manager import ConfigManager
from modules.utils import initialize_points, get_color, initialize_triangle_colors
from loguru import logger
import numpy as np
from scipy.spatial import Delaunay

def setup_ui(window, get_parameters):
    """Настройка пользовательского интерфейса для приложения Video Generator."""
    # Создаем контейнер для хранения элементов интерфейса
    class UIContainer:
        def __init__(self):
            self.canvas = None
            self.aspect_ratio = 1
            self.cached_width = None
            self.cached_height = None

        def update_canvas_size(self):
            """Обновить размер холста, масштабируя его под окно с сохранением соотношения сторон."""
            if not self.canvas or not get_parameters:
                logger.debug("Холст или get_parameters не инициализированы")
                return
            try:
                width, height, _, _, _, _, _ = get_parameters()
                if width <= 0 or height <= 0:
                    logger.warning(f"Некорректные размеры: {width}x{height}, используется 1080x1080")
                    width, height = 1080, 1080
                    self.aspect_ratio = 1
                else:
                    self.aspect_ratio = width / height
            except Exception as e:
                logger.error(f"Ошибка получения параметров: {e}, используется 1080x1080")
                width, height = 1080, 1080
                self.aspect_ratio = 1

            # Проверяем, изменились ли параметры
            if self.cached_width == width and self.cached_height == height:
                logger.debug("Параметры холста не изменились, пропуск обновления")
                return
            self.cached_width = width
            self.cached_height = height

            # Получаем доступное пространство в родительском макете
            parent = self.canvas.parentWidget()
            available_width = max(parent.width() * 0.8, 600)  # Минимум 400 пикселей
            available_height = max(parent.height() * 0.8, 600)

            # Вычисляем размер холста, сохраняя соотношение сторон
            canvas_aspect = self.aspect_ratio
            window_aspect = available_width / available_height

            if window_aspect > canvas_aspect:
                # Окно шире: ограничиваем по высоте
                new_height = available_height
                new_width = new_height * canvas_aspect
            else:
                # Окно выше: ограничиваем по ширине
                new_width = available_width
                new_height = new_width / canvas_aspect

            # Ограничиваем максимальные размеры
            max_size = 4096  # Ограничение для большинства графических драйверов
            if new_width > max_size or new_height > max_size:
                scale = min(max_size / new_width, max_size / new_height)
                new_width *= scale
                new_height *= scale

            # Устанавливаем размеры холста
            new_width = max(600, int(new_width))
            new_height = max(600, int(new_height))
            self.canvas.setMinimumSize(new_width, new_height)
            self.canvas.setMaximumSize(new_width, new_height)
            self.canvas.updateGeometry()
            logger.info(f"Обновлён размер холста: {new_width}x{new_height}, аспектное соотношение={self.aspect_ratio}")

    ui = UIContainer()

    # Загрузка конфигурации с использованием ConfigManager
    config_manager = ConfigManager('config.ini')

    def get_config_value(section, key, fallback):
        """Вспомогательная функция для получения значения из config.ini с fallback."""
        return config_manager.get_string(section, key, fallback)

    def get_config_bool(section, key, fallback):
        """Вспомогательная функция для получения булевого значения из config.ini."""
        return config_manager.get_bool(section, key, fallback)

    # Основной виджет и макет
    main_widget = QWidget()
    window.setCentralWidget(main_widget)
    main_layout = QHBoxLayout(main_widget)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Центрируем содержимое

    # Левая часть: область предварительного просмотра с OpenGL
    ui.canvas = OpenGLCanvas(window, get_parameters, ui)
    ui.canvas.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
    main_layout.addWidget(ui.canvas, stretch=2, alignment=Qt.AlignmentFlag.AlignCenter)

    # Правая часть: панель управления с сеточным макетом
    control_widget = QWidget()
    control_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
    control_layout = QGridLayout(control_widget)
    main_layout.addWidget(control_widget, stretch=1)

    # Поля ввода с значениями по умолчанию из config.ini
    ui.width_input = QLineEdit(get_config_value('WidthInput', 'default', '1080'))
    ui.height_input = QLineEdit(get_config_value('HeightInput', 'default', '1920'))
    ui.fps_input = QLineEdit(get_config_value('FPSInput', 'default', '30'))
    ui.duration_input = QLineEdit(get_config_value('DurationInput', 'default', '5'))
    ui.points_input = QLineEdit(get_config_value('PointsInput', 'default', '50'))

    # Флажки с значениями по умолчанию из config.ini
    ui.fixed_corners_check = QCheckBox("Угловые")
    ui.fixed_corners_check.setChecked(get_config_bool('FixedCornersCheck', 'default', True))
    ui.side_points_check = QCheckBox("Боковые")
    ui.side_points_check.setChecked(get_config_bool('SidePointsCheck', 'default', True))
    ui.show_points_check = QCheckBox("Точки")
    ui.show_points_check.setChecked(get_config_bool('ShowPointsCheck', 'default', True))
    ui.show_lines_check = QCheckBox("Линии")
    ui.show_lines_check.setChecked(get_config_bool('ShowLinesCheck', 'default', True))
    ui.fill_triangles_check = QCheckBox("Заливка")
    ui.fill_triangles_check.setChecked(get_config_bool('FillTrianglesCheck', 'default', False))

    # Слайдеры с значениями по умолчанию и границами из config.ini
    ui.speed_slider = QSlider(Qt.Orientation.Horizontal)
    ui.speed_slider.setMinimum(int(get_config_value('SpeedSlider', 'min', '0')))
    ui.speed_slider.setMaximum(int(get_config_value('SpeedSlider', 'max', '33')))
    ui.speed_slider.setValue(int(get_config_value('SpeedSlider', 'default', '16')))
    ui.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.speed_slider.setTickInterval(5)

    ui.point_size_slider = QSlider(Qt.Orientation.Horizontal)
    ui.point_size_slider.setMinimum(int(get_config_value('PointSizeSlider', 'min', '1')))
    ui.point_size_slider.setMaximum(int(get_config_value('PointSizeSlider', 'max', '100')))
    ui.point_size_slider.setValue(int(get_config_value('PointSizeSlider', 'default', '20')))
    ui.point_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.point_size_slider.setTickInterval(10)

    ui.line_width_slider = QSlider(Qt.Orientation.Horizontal)
    ui.line_width_slider.setMinimum(int(get_config_value('LineWidthSlider', 'min', '1')))
    ui.line_width_slider.setMaximum(int(get_config_value('LineWidthSlider', 'max', '20')))
    ui.line_width_slider.setValue(int(get_config_value('LineWidthSlider', 'default', '4')))
    ui.line_width_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.line_width_slider.setTickInterval(2)

    ui.brightness_range_slider = QSlider(Qt.Orientation.Horizontal)
    ui.brightness_range_slider.setMinimum(int(get_config_value('BrightnessRangeSlider', 'min', '0')))
    ui.brightness_range_slider.setMaximum(int(get_config_value('BrightnessRangeSlider', 'max', '100')))
    ui.brightness_range_slider.setValue(int(get_config_value('BrightnessRangeSlider', 'default', '50')))
    ui.brightness_range_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.brightness_range_slider.setTickInterval(10)

    ui.color_slider = QSlider(Qt.Orientation.Horizontal)
    ui.color_slider.setMinimum(int(get_config_value('ColorSlider', 'min', '0')))
    ui.color_slider.setMaximum(int(get_config_value('ColorSlider', 'max', '360')))
    ui.color_slider.setValue(int(get_config_value('ColorSlider', 'default', '0')))
    ui.color_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.color_slider.setTickInterval(10)

    ui.point_line_brightness_slider = QSlider(Qt.Orientation.Horizontal)
    ui.point_line_brightness_slider.setMinimum(int(get_config_value('PointLineBrightnessSlider', 'min', '0')))
    ui.point_line_brightness_slider.setMaximum(int(get_config_value('PointLineBrightnessSlider', 'max', '100')))
    ui.point_line_brightness_slider.setValue(int(get_config_value('PointLineBrightnessSlider', 'default', '50')))
    ui.point_line_brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.point_line_brightness_slider.setTickInterval(10)

    ui.background_color_slider = QSlider(Qt.Orientation.Horizontal)
    ui.background_color_slider.setMinimum(int(get_config_value('BackgroundColorSlider', 'min', '0')))
    ui.background_color_slider.setMaximum(int(get_config_value('BackgroundColorSlider', 'max', '360')))
    ui.background_color_slider.setValue(int(get_config_value('BackgroundColorSlider', 'default', '0')))
    ui.background_color_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.background_color_slider.setTickInterval(10)

    ui.background_brightness_slider = QSlider(Qt.Orientation.Horizontal)
    ui.background_brightness_slider.setMinimum(int(get_config_value('BackgroundBrightnessSlider', 'min', '0')))
    ui.background_brightness_slider.setMaximum(int(get_config_value('BackgroundBrightnessSlider', 'max', '100')))
    ui.background_brightness_slider.setValue(int(get_config_value('BackgroundBrightnessSlider', 'default', '0')))
    ui.background_brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.background_brightness_slider.setTickInterval(10)

    # Кнопки
    ui.start_stop_button = QPushButton("Начать анимацию")
    ui.generate_frame_button = QPushButton("Сгенерировать кадр")
    ui.export_frame_button = QPushButton("Экспортировать кадр")
    ui.export_button = QPushButton("Экспортировать видео")

    # Прогресс-бар
    ui.progress_bar = QProgressBar()
    ui.progress_bar.setMinimum(0)
    ui.progress_bar.setMaximum(100)
    ui.progress_bar.setValue(0)
    ui.progress_bar.setTextVisible(True)

    # Добавление элементов в сеточный макет
    control_layout.addWidget(QLabel("Ширина (px):"), 0, 0)
    control_layout.addWidget(ui.width_input, 0, 1)
    control_layout.addWidget(QLabel("Высота (px):"), 0, 2)
    control_layout.addWidget(ui.height_input, 0, 3)
    control_layout.addWidget(QLabel("Кадров/с:"), 1, 0)
    control_layout.addWidget(ui.fps_input, 1, 1)
    control_layout.addWidget(QLabel("Длительность (с):"), 1, 2)
    control_layout.addWidget(ui.duration_input, 1, 3)
    control_layout.addWidget(QLabel("Количество точек:"), 2, 0)
    control_layout.addWidget(ui.points_input, 2, 1)
    control_layout.addWidget(ui.fixed_corners_check, 2, 2)
    control_layout.addWidget(ui.side_points_check, 2, 3)
    control_layout.addWidget(QLabel("Скорость анимации:"), 3, 0)
    control_layout.addWidget(ui.speed_slider, 3, 1, 1, 3)
    control_layout.addWidget(ui.show_points_check, 4, 0, 1, 2)
    control_layout.addWidget(QLabel("Размер точек:"), 4, 2)
    control_layout.addWidget(ui.point_size_slider, 4, 3)
    control_layout.addWidget(ui.show_lines_check, 5, 0, 1, 2)
    control_layout.addWidget(QLabel("Толщина линий:"), 5, 2)
    control_layout.addWidget(ui.line_width_slider, 5, 3)
    control_layout.addWidget(ui.fill_triangles_check, 6, 0, 1, 2)
    control_layout.addWidget(QLabel("Диапазон яркости:"), 6, 2)
    control_layout.addWidget(ui.brightness_range_slider, 6, 3)
    control_layout.addWidget(QLabel("Цвет точек/линий:"), 7, 0, 1, 2)
    control_layout.addWidget(ui.color_slider, 7, 2, 1, 2)
    control_layout.addWidget(QLabel("Яркость точек/линий:"), 8, 0, 1, 2)
    control_layout.addWidget(ui.point_line_brightness_slider, 8, 2, 1, 2)
    control_layout.addWidget(QLabel("Цвет фона:"), 9, 0, 1, 2)
    control_layout.addWidget(ui.background_color_slider, 9, 2, 1, 2)
    control_layout.addWidget(QLabel("Яркость фона:"), 10, 0, 1, 2)
    control_layout.addWidget(ui.background_brightness_slider, 10, 2, 1, 2)
    control_layout.addWidget(ui.generate_frame_button, 12, 0, 1, 2)
    control_layout.addWidget(ui.export_frame_button, 12, 2, 1, 2)
    control_layout.addWidget(ui.start_stop_button, 13, 0, 1, 2)
    control_layout.addWidget(ui.export_button, 13, 2, 1, 2)
    control_layout.addWidget(QLabel("Прогресс экспорта:"), 14, 0, 1, 2)
    control_layout.addWidget(ui.progress_bar, 14, 2, 1, 2)

    control_layout.setRowStretch(11, 1)

    return ui

class OpenGLCanvas(QOpenGLWidget):
    def __init__(self, parent, get_parameters, ui):
        super().__init__(parent)
        self.get_parameters = get_parameters
        self.ui = ui  # Сохраняем ссылку на объект ui
        self.points = np.array([])
        self.velocities = np.array([])
        self.triangle_colors = {}
        self.simplices = []
        self.setMinimumSize(400, 400)

    def initializeGL(self):
        """Инициализация OpenGL."""
        try:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_POINT_SMOOTH)
            glEnable(GL_LINE_SMOOTH)
            # Проверяем состояние фреймбуфера
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

            # Вычисляем размеры области рендеринга с сохранением соотношения сторон
            window_aspect = w / h
            if window_aspect > aspect_ratio:
                # Окно шире: добавляем черные полосы по бокам
                view_width = h * aspect_ratio
                view_height = h
                offset_x = (w - view_width) / 2
                offset_y = 0
            else:
                # Окно выше: добавляем черные полосы сверху и снизу
                view_width = w
                view_height = w / aspect_ratio
                offset_x = 0
                offset_y = (h - view_height) / 2

            # Проверяем, что размеры области просмотра допустимы
            view_width = max(1, min(int(view_width), 4096))
            view_height = max(1, min(int(view_height), 4096))
            offset_x = max(0, int(offset_x))
            offset_y = max(0, int(offset_y))

            # Устанавливаем область просмотра
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
            color = get_color(self.ui.color_slider.value(),
                             self.ui.point_line_brightness_slider.value())
            bg_color = get_color(self.ui.background_color_slider.value(),
                                self.ui.background_brightness_slider.value())
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
                    self.simplices,
                    self.ui.color_slider.value() / 360.0,
                    self.ui.brightness_range_slider.value(),
                    {}
                )

            # Рендеринг треугольников
            if self.ui.fill_triangles_check.isChecked():
                glBegin(GL_TRIANGLES)
                for simplex in self.simplices:
                    simplex_key = tuple(sorted(simplex))
                    if simplex_key in self.triangle_colors:
                        glColor3fv(self.triangle_colors[simplex_key])
                        for vertex in simplex:
                            glVertex2f(self.points[vertex, 0], self.points[vertex, 1])
                glEnd()

            # Рендеринг линий
            if self.ui.show_lines_check.isChecked():
                glLineWidth(line_width)
                glBegin(GL_LINES)
                glColor3fv(color)
                for simplex in self.simplices:
                    triangle = self.points[simplex]
                    triangle = np.vstack((triangle, triangle[0:1]))
                    for i in range(3):
                        glVertex2f(triangle[i, 0], triangle[i, 1])
                        glVertex2f(triangle[i+1, 0], triangle[i+1, 1])
                glEnd()

            # Рендеринг точек
            if self.ui.show_points_check.isChecked():
                glPointSize(point_size / 10.0)
                glBegin(GL_POINTS)
                glColor3fv(color)
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