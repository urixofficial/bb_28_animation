import sys
from loguru import logger
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIntValidator
from modules.ui import setup_ui
from modules.animation import AnimationManager
from modules.export import ExportManager
import configparser
import os

# Настройка логирования с использованием loguru
config = configparser.ConfigParser()
config_file = 'config.ini'
if os.path.exists(config_file):
    config.read(config_file)
    log_level = config.get('Logging', 'level', fallback='INFO')
    logger.remove()  # Удаляем стандартный обработчик
    logger.add(sys.stderr, level=log_level)
else:
    logger.remove()
    logger.add(sys.stderr, level='INFO')
    logger.warning(f"Файл конфигурации {config_file} не найден")

class VideoGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Generator")
        self.resize(1200, 640)
        self.is_animation_running = False

        # Загрузка конфигурации из config.ini
        self.config = configparser.ConfigParser()
        config_file = 'config.ini'
        if os.path.exists(config_file):
            self.config.read(config_file)
            logger.info(f"Загружен файл конфигурации: {config_file}")
        else:
            logger.warning(f"Файл конфигурации {config_file} не найден")
            self.config = None

        # Инициализация интерфейса
        self.ui = setup_ui(self, self.get_parameters)
        self.ui.update_canvas_size()  # Вызываем после инициализации ui

        # Добавляем валидатор для полей ввода
        validator = QIntValidator(1, 3840, self)
        self.ui.width_input.setValidator(validator)
        self.ui.height_input.setValidator(validator)

        # Инициализация менеджера анимации
        self.anim_manager = AnimationManager(
            canvas=self.ui.canvas,
            get_parameters=self.get_parameters,
            fixed_corners_check=self.ui.fixed_corners_check,
            show_points_check=self.ui.show_points_check,
            show_lines_check=self.ui.show_lines_check,
            fill_triangles_check=self.ui.fill_triangles_check,
            color_slider=self.ui.color_slider,
            point_line_brightness_slider=self.ui.point_line_brightness_slider,
            brightness_range_slider=self.ui.brightness_range_slider,
            speed_slider=self.ui.speed_slider,
            background_color_slider=self.ui.background_color_slider,
            background_brightness_slider=self.ui.background_brightness_slider,
            side_points_check=self.ui.side_points_check
        )

        # Инициализация менеджера экспорта
        self.export_manager = ExportManager(
            get_parameters=self.get_parameters,
            fixed_corners_check=self.ui.fixed_corners_check,
            show_points_check=self.ui.show_points_check,
            show_lines_check=self.ui.show_lines_check,
            fill_triangles_check=self.ui.fill_triangles_check,
            color_slider=self.ui.color_slider,
            point_line_brightness_slider=self.ui.point_line_brightness_slider,
            brightness_range_slider=self.ui.brightness_range_slider,
            speed_slider=self.ui.speed_slider,
            background_color_slider=self.ui.background_color_slider,
            background_brightness_slider=self.ui.background_brightness_slider,
            progress_bar=self.ui.progress_bar,
            side_points_check=self.ui.side_points_check
        )

        # Отрисовка начального кадра
        self.anim_manager.generate_single_frame()

        # Подключение кнопок интерфейса к методам
        self.ui.start_stop_button.clicked.connect(self.toggle_animation)
        self.ui.generate_frame_button.clicked.connect(self.anim_manager.generate_single_frame)
        self.ui.export_button.clicked.connect(self.export_manager.export_animation)
        self.ui.export_frame_button.clicked.connect(self.export_manager.export_frame)
        self.ui.speed_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.point_size_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.line_width_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.brightness_range_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.color_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.point_line_brightness_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.background_color_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.background_brightness_slider.valueChanged.connect(self.anim_manager.update_animation)
        self.ui.show_points_check.stateChanged.connect(self.anim_manager.update_animation)
        self.ui.show_lines_check.stateChanged.connect(self.anim_manager.update_animation)
        self.ui.fill_triangles_check.stateChanged.connect(self.anim_manager.update_animation)
        self.ui.fixed_corners_check.stateChanged.connect(self.on_geometry_change)
        self.ui.side_points_check.stateChanged.connect(self.on_geometry_change)
        self.ui.width_input.returnPressed.connect(self.on_geometry_change)
        self.ui.width_input.editingFinished.connect(self.on_geometry_change)
        self.ui.height_input.returnPressed.connect(self.on_geometry_change)
        self.ui.height_input.editingFinished.connect(self.on_geometry_change)
        self.ui.fps_input.returnPressed.connect(self.on_animation_parameters_change)
        self.ui.fps_input.editingFinished.connect(self.on_animation_parameters_change)
        self.ui.points_input.returnPressed.connect(self.on_geometry_change)
        self.ui.points_input.editingFinished.connect(self.on_geometry_change)

    def toggle_animation(self):
        """Переключение между запуском и остановкой анимации."""
        if not self.is_animation_running:
            logger.info("Запуск анимации")
            self.anim_manager.start_animation()
            self.ui.start_stop_button.setText("Остановить анимацию")
            self.is_animation_running = True
        else:
            logger.info("Остановка анимации")
            self.anim_manager.stop_animation()
            self.ui.start_stop_button.setText("Начать анимацию")
            self.is_animation_running = False

    def on_geometry_change(self):
        """Обработка изменений параметров геਮетрии."""
        try:
            logger.info("Изменение размеров холста")
            self.ui.update_canvas_size()  # Обновляем размер холста
            if self.anim_manager.is_static_frame:
                self.anim_manager.generate_single_frame()
            else:
                self.anim_manager.start_animation()
        except Exception as e:
            logger.error(f"Ошибка в on_geometry_change: {e}")

    def on_animation_parameters_change(self):
        """Обработка изменений параметров анимации."""
        try:
            logger.info("Изменение параметров анимации")
            if not self.is_animation_running:
                self.anim_manager.generate_single_frame()
            else:
                self.anim_manager.start_animation()
        except Exception as e:
            logger.error(f"Ошибка в on_animation_parameters_change: {e}")

    def _get_config_value(self, section, key, fallback, is_float=False):
        """Получение значения из конфигурации с обработкой ошибок."""
        try:
            if self.config and section in self.config:
                value = float(self.config[section][key]) if is_float else int(self.config[section][key])
                return value
            return fallback
        except (KeyError, ValueError):
            logger.warning(f"Ошибка чтения {section}.{key}, используется значение по умолчанию: {fallback}")
            return fallback

    def _validate_width(self, width_text):
        """Валидация значения ширины."""
        min_val = self._get_config_value('WidthInput', 'min', 1)
        max_val = self._get_config_value('WidthInput', 'max', 3840)
        default = self._get_config_value('WidthInput', 'default', 1080)
        try:
            width = int(width_text)
            if not (min_val <= width <= max_val):
                logger.error(f"Ширина {width} вне диапазона [{min_val}, {max_val}], используется значение по умолчанию: {default}")
                return default
            return width
        except ValueError:
            logger.error(f"Некорректное значение ширины: {width_text}, используется значение по умолчанию: {default}")
            return default

    def _validate_height(self, height_text):
        """Валидация значения высоты."""
        min_val = self._get_config_value('HeightInput', 'min', 1)
        max_val = self._get_config_value('HeightInput', 'max', 3840)
        default = self._get_config_value('HeightInput', 'default', 1920)
        try:
            height = int(height_text)
            if not (min_val <= height <= max_val):
                logger.error(f"Высота {height} вне диапазона [{min_val}, {max_val}], используется значение по умолчанию: {default}")
                return default
            return height
        except ValueError:
            logger.error(f"Некорректное значение высоты: {height_text}, используется значение по умолчанию: {default}")
            return default

    def _validate_fps(self, fps_text):
        """Валидация значения FPS."""
        min_val = self._get_config_value('FPSInput', 'min', 1)
        max_val = self._get_config_value('FPSInput', 'max', 120)
        default = self._get_config_value('FPSInput', 'default', 30)
        try:
            fps = int(fps_text)
            if not (min_val <= fps <= max_val):
                logger.error(f"FPS {fps} вне диапазона [{min_val}, {max_val}], используется значение по умолчанию: {default}")
                return default
            return fps
        except ValueError:
            logger.error(f"Некорректное значение FPS: {fps_text}, используется значение по умолчанию: {default}")
            return default

    def _validate_duration(self, duration_text):
        """Валидация значения длительности."""
        min_val = self._get_config_value('DurationInput', 'min', 0.1, is_float=True)
        max_val = self._get_config_value('DurationInput', 'max', 60, is_float=True)
        default = self._get_config_value('DurationInput', 'default', 5, is_float=True)
        try:
            duration = float(duration_text)
            if not (min_val <= duration <= max_val):
                logger.error(f"Длительность {duration} вне диапазона [{min_val}, {max_val}], используется значение по умолчанию: {default}")
                return default
            return duration
        except ValueError:
            logger.error(f"Некорректное значение длительности: {duration_text}, используется значение по умолчанию: {default}")
            return default

    def _validate_num_points(self, points_text):
        """Валидация значения количества точек."""
        min_val = self._get_config_value('PointsInput', 'min', 3)
        max_val = self._get_config_value('PointsInput', 'max', 1000)
        default = self._get_config_value('PointsInput', 'default', 50)
        try:
            num_points = int(points_text)
            if not (min_val <= num_points <= max_val):
                logger.error(f"Количество точек {num_points} вне диапазона [{min_val}, {max_val}], используется значение по умолчанию: {default}")
                return default
            return num_points
        except ValueError:
            logger.error(f"Некорректное значение количества точек: {points_text}, используется значение по умолчанию: {default}")
            return default

    def get_parameters(self):
        """Получение и валидация входных параметров из элементов интерфейса."""
        try:
            logger.info("Получение параметров интерфейса")
            width = self._validate_width(self.ui.width_input.text())
            height = self._validate_height(self.ui.height_input.text())
            fps = self._validate_fps(self.ui.fps_input.text())
            duration = self._validate_duration(self.ui.duration_input.text())
            num_points = self._validate_num_points(self.ui.points_input.text())
            point_size = self.ui.point_size_slider.value()
            line_width = self.ui.line_width_slider.value() / 10.0
            logger.info(f"Параметры: ширина={width}, высота={height}, fps={fps}, длительность={duration}, точки={num_points}, размер точек={point_size}, толщина линий={line_width}")
            return width, height, fps, duration, num_points, point_size, line_width
        except Exception as e:
            logger.error(f"Ошибка в get_parameters: {e}")
            return 1080, 1080, 30, 5, 50, 20, 4.0

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoGeneratorApp()
    window.show()
    sys.exit(app.exec())