import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QSlider, QCheckBox, QProgressBar
from PySide6.QtCore import Qt
import configparser
import os

def setup_ui(window):
    """Настройка пользовательского интерфейса для приложения Video Generator."""
    # Создаем контейнер для хранения элементов интерфейса
    class UIContainer:
        pass
    ui = UIContainer()

    # Загрузка конфигурации из config.ini
    config = configparser.ConfigParser()
    config_file = '../config.ini'
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        print(f"Файл {config_file} не найден, используются значения по умолчанию")
        config = None

    def get_config_value(section, key, fallback):
        """Вспомогательная функция для получения значения из config.ini с fallback."""
        try:
            return config[section][key] if config and section in config else fallback
        except (KeyError, ValueError):
            print(f"Ошибка чтения {section}.{key}, используется значение: {fallback}")
            return fallback

    def get_config_bool(section, key, fallback):
        """Вспомогательная функция для получения булевого значения из config.ini."""
        try:
            return config.getboolean(section, key) if config and section in config else fallback
        except (KeyError, ValueError):
            print(f"Ошибка чтения {section}.{key}, используется значение: {fallback}")
            return fallback

    # Основной виджет и макет
    main_widget = QWidget()
    window.setCentralWidget(main_widget)
    main_layout = QHBoxLayout(main_widget)

    # Левая часть: область предварительного просмотра
    ui.figure, ui.ax = plt.subplots()
    ui.canvas = FigureCanvas(ui.figure)
    main_layout.addWidget(ui.canvas, stretch=2)

    # Правая часть: панель управления с сеточным макетом
    control_widget = QWidget()
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