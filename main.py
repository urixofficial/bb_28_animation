import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from ui import setup_ui
from animation import AnimationManager
from export import ExportManager
import configparser
import os

class VideoGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Generator")
        self.setGeometry(100, 100, 1200, 600)

        # Флаг для отслеживания состояния анимации
        self.is_animation_running = False

        # Загрузка конфигурации из config.ini
        self.config = configparser.ConfigParser()
        config_file = 'config.ini'
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            print(f"Файл {config_file} не найден, используются значения по умолчанию")
            self.config = None

        # Инициализация интерфейса
        self.ui = setup_ui(self)

        # Инициализация менеджера анимации
        self.anim_manager = AnimationManager(
            figure=self.ui.figure,
            ax=self.ui.ax,
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
        self.ui.height_input.returnPressed.connect(self.on_geometry_change)
        self.ui.fps_input.returnPressed.connect(self.on_animation_parameters_change)
        self.ui.duration_input.returnPressed.connect(self.on_animation_parameters_change)
        self.ui.points_input.returnPressed.connect(self.on_geometry_change)

    def toggle_animation(self):
        """Переключение между запуском и остановкой анимации."""
        if not self.is_animation_running:
            self.anim_manager.start_animation()
            self.ui.start_stop_button.setText("Остановить анимацию")
            self.is_animation_running = True
        else:
            self.anim_manager.stop_animation()
            self.ui.start_stop_button.setText("Начать анимацию")
            self.is_animation_running = False

    def on_geometry_change(self):
        """Handle changes to geometry parameters (width, height, points, fixed corners, side points)."""
        if self.anim_manager.is_static_frame:
            self.anim_manager.generate_single_frame()
        else:
            self.anim_manager.start_animation()

    def on_animation_parameters_change(self):
        """Handle changes to animation parameters (fps, duration)."""
        if not self.is_animation_running:
            self.anim_manager.generate_single_frame()
        else:
            self.anim_manager.start_animation()

    def get_parameters(self):
        """Получение и проверка входных параметров из элементов интерфейса."""
        def get_config_value(section, key, fallback, is_float=False):
            """Вспомогательная функция для получения значения из config.ini."""
            try:
                if self.config and section in self.config:
                    return float(self.config[section][key]) if is_float else int(self.config[section][key])
                return fallback
            except (KeyError, ValueError):
                print(f"Ошибка чтения {section}.{key}, используется значение: {fallback}")
                return fallback

        try:
            # Получение и валидация ширины
            width = int(self.ui.width_input.text())
            width_min = get_config_value('WidthInput', 'min', 1)
            width_max = get_config_value('WidthInput', 'max', 3840)
            if not (width_min <= width <= width_max):
                raise ValueError(f"Ширина должна быть в диапазоне [{width_min}, {width_max}]")

            # Получение и валидация высоты
            height = int(self.ui.height_input.text())
            height_min = get_config_value('HeightInput', 'min', 1)
            height_max = get_config_value('HeightInput', 'max', 3840)
            if not (height_min <= height <= height_max):
                raise ValueError(f"Высота должна быть в диапазоне [{height_min}, {height_max}]")

            # Получение и валидация FPS
            fps = int(self.ui.fps_input.text())
            fps_min = get_config_value('FPSInput', 'min', 1)
            fps_max = get_config_value('FPSInput', 'max', 120)
            if not (fps_min <= fps <= fps_max):
                raise ValueError(f"FPS должен быть в диапазоне [{fps_min}, {fps_max}]")

            # Получение и валидация длительности
            duration = float(self.ui.duration_input.text())
            duration_min = get_config_value('DurationInput', 'min', 0.1, is_float=True)
            duration_max = get_config_value('DurationInput', 'max', 60, is_float=True)
            if not (duration_min <= duration <= duration_max):
                raise ValueError(f"Длительность должна быть в диапазоне [{duration_min}, {duration_max}]")

            # Получение и валидация количества точек
            num_points = int(self.ui.points_input.text())
            points_min = get_config_value('PointsInput', 'min', 3)
            points_max = get_config_value('PointsInput', 'max', 1000)
            if not (points_min <= num_points <= points_max):
                raise ValueError(f"Количество точек должно быть в диапазоне [{points_min}, {points_max}]")

            # Получение значений слайдеров (они уже ограничены в ui.py)
            point_size = self.ui.point_size_slider.value()
            line_width = self.ui.line_width_slider.value() / 10.0  # Масштабирование до 0.1-2.0

            return width, height, fps, duration, num_points, point_size, line_width
        except ValueError as e:
            print(f"Ошибка ввода: {e}")
            # Возврат значений по умолчанию из config.ini или жестко закодированных
            return (
                get_config_value('WidthInput', 'default', 1080),
                get_config_value('HeightInput', 'default', 1920),
                get_config_value('FPSInput', 'default', 30),
                get_config_value('DurationInput', 'default', 5, is_float=True),
                get_config_value('PointsInput', 'default', 50),
                self.ui.point_size_slider.value(),  # Текущее значение слайдера
                self.ui.line_width_slider.value() / 10.0  # Текущее значение слайдера
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoGeneratorApp()
    window.show()
    sys.exit(app.exec())