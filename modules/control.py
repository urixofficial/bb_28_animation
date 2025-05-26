from PySide6.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QSlider, QCheckBox, QProgressBar, QSizePolicy, QGroupBox, QVBoxLayout
from PySide6.QtCore import Qt
from modules.config_manager import ConfigManager
from loguru import logger

def setup_control_panel(window, get_parameters, canvas_class):
    """Настройка панели управления для приложения Video Generator."""
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
                    logger.warning(f"Некорректные размеры: {width}x{height}, используется {config_manager.get_int('Canvas', 'default_width', 1080)}x{config_manager.get_int('Canvas', 'default_height', 1080)}")
                    width = config_manager.get_int('Canvas', 'default_width', 1080)
                    height = config_manager.get_int('Canvas', 'default_height', 1080)
                    self.aspect_ratio = width / height
                else:
                    self.aspect_ratio = width / height
            except Exception as e:
                logger.error(f"Ошибка получения параметров: {e}, используется {config_manager.get_int('Canvas', 'default_width', 1080)}x{config_manager.get_int('Canvas', 'default_height', 1080)}")
                width = config_manager.get_int('Canvas', 'default_width', 1080)
                height = config_manager.get_int('Canvas', 'default_height', 1080)
                self.aspect_ratio = width / height

            if self.cached_width == width and self.cached_height == height:
                logger.debug("Параметры холста не изменились, пропуск обновления")
                return
            self.cached_width = width
            self.cached_height = height

            parent = self.canvas.parentWidget()
            available_width = max(parent.width() * 0.8, config_manager.get_int('Canvas', 'min_width', 600))
            available_height = max(parent.height() * 0.8, config_manager.get_int('Canvas', 'min_height', 600))

            canvas_aspect = self.aspect_ratio
            window_aspect = available_width / available_height

            if window_aspect > canvas_aspect:
                new_height = available_height
                new_width = new_height * canvas_aspect
            else:
                new_width = available_width
                new_height = new_width / canvas_aspect

            max_size = config_manager.get_int('Canvas', 'max_size', 4096)
            if new_width > max_size or new_height > max_size:
                scale = min(max_size / new_width, max_size / new_height)
                new_width *= scale
                new_height *= scale

            new_width = max(config_manager.get_int('Canvas', 'min_width', 600), int(new_width))
            new_height = max(config_manager.get_int('Canvas', 'min_height', 600), int(new_height))
            self.canvas.setMinimumSize(new_width, new_height)
            self.canvas.setMaximumSize(new_width, new_height)
            self.canvas.updateGeometry()
            logger.info(f"Обновлён размер холста: {new_width}x{new_height}, аспектное соотношение={self.aspect_ratio}")

    ui = UIContainer()

    config_manager = ConfigManager('config.ini')

    def get_config_value(section, key, fallback):
        return config_manager.get_string(section, key, fallback)

    def get_config_bool(section, key, fallback):
        return config_manager.get_bool(section, key, fallback)

    main_widget = QWidget()
    window.setCentralWidget(main_widget)
    main_layout = QHBoxLayout(main_widget)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    ui.canvas = canvas_class(window, get_parameters, ui)
    ui.canvas.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
    ui.canvas.setMinimumSize(
        config_manager.get_int('Window', 'min_width', 400),
        config_manager.get_int('Window', 'min_height', 400)
    )
    main_layout.addWidget(ui.canvas, stretch=2, alignment=Qt.AlignmentFlag.AlignCenter)

    control_widget = QWidget()
    control_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
    control_layout = QVBoxLayout(control_widget)
    control_layout.setSpacing(30)
    main_layout.addWidget(control_widget, stretch=1)

    ui.width_input = QLineEdit(get_config_value('WidthInput', 'default', '1080'))
    ui.height_input = QLineEdit(get_config_value('HeightInput', 'default', '1920'))
    ui.fps_input = QLineEdit(get_config_value('FPSInput', 'default', '30'))
    ui.duration_input = QLineEdit(get_config_value('DurationInput', 'default', '5'))
    ui.points_input = QLineEdit(get_config_value('PointsInput', 'default', '50'))

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

    ui.transition_speed_slider = QSlider(Qt.Orientation.Horizontal)
    ui.transition_speed_slider.setMinimum(int(get_config_value('TransitionSpeedSlider', 'min', '5')))
    ui.transition_speed_slider.setMaximum(int(get_config_value('TransitionSpeedSlider', 'max', '40')))
    ui.transition_speed_slider.setValue(int(get_config_value('TransitionSpeedSlider', 'default', '20')))
    ui.transition_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.transition_speed_slider.setTickInterval(5)

    # Блок для основного цвета
    main_color_group = QGroupBox("Основной цвет")
    main_color_layout = QGridLayout()
    main_color_group.setLayout(main_color_layout)
    main_color_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    ui.main_hue_slider = QSlider(Qt.Orientation.Horizontal)
    ui.main_hue_slider.setMinimum(int(get_config_value('MainHueSlider', 'min', '0')))
    ui.main_hue_slider.setMaximum(int(get_config_value('MainHueSlider', 'max', '360')))
    ui.main_hue_slider.setValue(int(get_config_value('MainHueSlider', 'default', '0')))
    ui.main_hue_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.main_hue_slider.setTickInterval(10)
    ui.main_hue_input = QLineEdit(str(ui.main_hue_slider.value()))
    ui.main_hue_input.setFixedWidth(50)

    ui.main_saturation_slider = QSlider(Qt.Orientation.Horizontal)
    ui.main_saturation_slider.setMinimum(int(get_config_value('MainSaturationSlider', 'min', '0')))
    ui.main_saturation_slider.setMaximum(int(get_config_value('MainSaturationSlider', 'max', '100')))
    ui.main_saturation_slider.setValue(int(get_config_value('MainSaturationSlider', 'default', '100')))
    ui.main_saturation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.main_saturation_slider.setTickInterval(10)
    ui.main_saturation_input = QLineEdit(str(ui.main_saturation_slider.value()))
    ui.main_saturation_input.setFixedWidth(50)

    ui.main_value_slider = QSlider(Qt.Orientation.Horizontal)
    ui.main_value_slider.setMinimum(int(get_config_value('MainValueSlider', 'min', '0')))
    ui.main_value_slider.setMaximum(int(get_config_value('MainValueSlider', 'max', '100')))
    ui.main_value_slider.setValue(int(get_config_value('MainValueSlider', 'default', '50')))
    ui.main_value_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.main_value_slider.setTickInterval(10)
    ui.main_value_input = QLineEdit(str(ui.main_value_slider.value()))
    ui.main_value_input.setFixedWidth(50)

    main_color_layout.addWidget(QLabel("Оттенок:"), 0, 0)
    main_color_layout.addWidget(ui.main_hue_slider, 0, 1)
    main_color_layout.addWidget(ui.main_hue_input, 0, 2)
    main_color_layout.addWidget(QLabel("Насыщенность:"), 1, 0)
    main_color_layout.addWidget(ui.main_saturation_slider, 1, 1)
    main_color_layout.addWidget(ui.main_saturation_input, 1, 2)
    main_color_layout.addWidget(QLabel("Яркость:"), 2, 0)
    main_color_layout.addWidget(ui.main_value_slider, 2, 1)
    main_color_layout.addWidget(ui.main_value_input, 2, 2)

    # Подключение сигналов для синхронизации слайдеров и полей ввода
    def update_hue_input():
        ui.main_hue_input.setText(str(ui.main_hue_slider.value()))

    def update_saturation_input():
        ui.main_saturation_input.setText(str(ui.main_saturation_slider.value()))

    def update_value_input():
        ui.main_value_input.setText(str(ui.main_value_slider.value()))

    ui.main_hue_slider.valueChanged.connect(update_hue_input)
    ui.main_saturation_slider.valueChanged.connect(update_saturation_input)
    ui.main_value_slider.valueChanged.connect(update_value_input)

    def on_hue_input_changed():
        try:
            value = int(ui.main_hue_input.text())
            if ui.main_hue_slider.minimum() <= value <= ui.main_hue_slider.maximum():
                ui.main_hue_slider.setValue(value)
            else:
                ui.main_hue_input.setText(str(ui.main_hue_slider.value()))
        except ValueError:
            ui.main_hue_input.setText(str(ui.main_hue_slider.value()))

    def on_saturation_input_changed():
        try:
            value = int(ui.main_saturation_input.text())
            if ui.main_saturation_slider.minimum() <= value <= ui.main_saturation_slider.maximum():
                ui.main_saturation_slider.setValue(value)
            else:
                ui.main_saturation_input.setText(str(ui.main_saturation_slider.value()))
        except ValueError:
            ui.main_saturation_input.setText(str(ui.main_saturation_slider.value()))

    def on_value_input_changed():
        try:
            value = int(ui.main_value_input.text())
            if ui.main_value_slider.minimum() <= value <= ui.main_value_slider.maximum():
                ui.main_value_slider.setValue(value)
            else:
                ui.main_value_input.setText(str(ui.main_value_slider.value()))
        except ValueError:
            ui.main_value_input.setText(str(ui.main_value_slider.value()))

    ui.main_hue_input.textChanged.connect(on_hue_input_changed)
    ui.main_saturation_input.textChanged.connect(on_saturation_input_changed)
    ui.main_value_input.textChanged.connect(on_value_input_changed)

    # Блок для цвета фона
    bg_color_group = QGroupBox("Цвет фона")
    bg_color_layout = QGridLayout()
    bg_color_group.setLayout(bg_color_layout)
    bg_color_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    ui.bg_hue_slider = QSlider(Qt.Orientation.Horizontal)
    ui.bg_hue_slider.setMinimum(int(get_config_value('BackgroundColorSlider', 'min', '0')))
    ui.bg_hue_slider.setMaximum(int(get_config_value('BackgroundColorSlider', 'max', '360')))
    ui.bg_hue_slider.setValue(int(get_config_value('BackgroundColorSlider', 'default', '0')))
    ui.bg_hue_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.bg_hue_slider.setTickInterval(10)
    ui.bg_hue_input = QLineEdit(str(ui.bg_hue_slider.value()))
    ui.bg_hue_input.setFixedWidth(50)

    ui.bg_saturation_slider = QSlider(Qt.Orientation.Horizontal)
    ui.bg_saturation_slider.setMinimum(int(get_config_value('BackgroundSaturationSlider', 'min', '0')))
    ui.bg_saturation_slider.setMaximum(int(get_config_value('BackgroundSaturationSlider', 'max', '100')))
    ui.bg_saturation_slider.setValue(int(get_config_value('BackgroundSaturationSlider', 'default', '100')))
    ui.bg_saturation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.bg_saturation_slider.setTickInterval(10)
    ui.bg_saturation_input = QLineEdit(str(ui.bg_saturation_slider.value()))
    ui.bg_saturation_input.setFixedWidth(50)

    ui.bg_value_slider = QSlider(Qt.Orientation.Horizontal)
    ui.bg_value_slider.setMinimum(int(get_config_value('BackgroundBrightnessSlider', 'min', '0')))
    ui.bg_value_slider.setMaximum(int(get_config_value('BackgroundBrightnessSlider', 'max', '100')))
    ui.bg_value_slider.setValue(int(get_config_value('BackgroundBrightnessSlider', 'default', '0')))
    ui.bg_value_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    ui.bg_value_slider.setTickInterval(10)
    ui.bg_value_input = QLineEdit(str(ui.bg_value_slider.value()))
    ui.bg_value_input.setFixedWidth(50)

    bg_color_layout.addWidget(QLabel("Оттенок:"), 0, 0)
    bg_color_layout.addWidget(ui.bg_hue_slider, 0, 1)
    bg_color_layout.addWidget(ui.bg_hue_input, 0, 2)
    bg_color_layout.addWidget(QLabel("Насыщенность:"), 1, 0)
    bg_color_layout.addWidget(ui.bg_saturation_slider, 1, 1)
    bg_color_layout.addWidget(ui.bg_saturation_input, 1, 2)
    bg_color_layout.addWidget(QLabel("Яркость:"), 2, 0)
    bg_color_layout.addWidget(ui.bg_value_slider, 2, 1)
    bg_color_layout.addWidget(ui.bg_value_input, 2, 2)

    # Подключение сигналов для синхронизации слайдеров и полей ввода
    def update_bg_hue_input():
        ui.bg_hue_input.setText(str(ui.bg_hue_slider.value()))

    def update_bg_saturation_input():
        ui.bg_saturation_input.setText(str(ui.bg_saturation_slider.value()))

    def update_bg_value_input():
        ui.bg_value_input.setText(str(ui.bg_value_slider.value()))

    ui.bg_hue_slider.valueChanged.connect(update_bg_hue_input)
    ui.bg_saturation_slider.valueChanged.connect(update_bg_saturation_input)
    ui.bg_value_slider.valueChanged.connect(update_bg_value_input)

    def on_bg_hue_input_changed():
        try:
            value = int(ui.bg_hue_input.text())
            if ui.bg_hue_slider.minimum() <= value <= ui.bg_hue_slider.maximum():
                ui.bg_hue_slider.setValue(value)
            else:
                ui.bg_hue_input.setText(str(ui.bg_hue_slider.value()))
        except ValueError:
            ui.bg_hue_input.setText(str(ui.bg_hue_slider.value()))

    def on_bg_saturation_input_changed():
        try:
            value = int(ui.bg_saturation_input.text())
            if ui.bg_saturation_slider.minimum() <= value <= ui.bg_saturation_slider.maximum():
                ui.bg_saturation_slider.setValue(value)
            else:
                ui.bg_saturation_input.setText(str(ui.bg_saturation_slider.value()))
        except ValueError:
            ui.bg_saturation_input.setText(str(ui.bg_saturation_slider.value()))

    def on_bg_value_input_changed():
        try:
            value = int(ui.bg_value_input.text())
            if ui.bg_value_slider.minimum() <= value <= ui.bg_value_slider.maximum():
                ui.bg_value_slider.setValue(value)
            else:
                ui.bg_value_input.setText(str(ui.bg_value_slider.value()))
        except ValueError:
            ui.bg_value_input.setText(str(ui.bg_value_slider.value()))

    ui.bg_hue_input.textChanged.connect(on_bg_hue_input_changed)
    ui.bg_saturation_input.textChanged.connect(on_bg_saturation_input_changed)
    ui.bg_value_input.textChanged.connect(on_bg_value_input_changed)

    # Блок для параметров изображения
    image_params_group = QGroupBox("Параметры изображения")
    image_params_layout = QGridLayout()
    image_params_group.setLayout(image_params_layout)
    image_params_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    image_params_layout.addWidget(QLabel("Ширина (px):"), 0, 0)
    image_params_layout.addWidget(ui.width_input, 0, 1)
    image_params_layout.addWidget(QLabel("Высота (px):"), 0, 2)
    image_params_layout.addWidget(ui.height_input, 0, 3)
    image_params_layout.addWidget(QLabel("Кадров/с:"), 1, 0)
    image_params_layout.addWidget(ui.fps_input, 1, 1)
    image_params_layout.addWidget(QLabel("Длительность (с):"), 1, 2)
    image_params_layout.addWidget(ui.duration_input, 1, 3)

    # Блок для параметров генерации
    generation_params_group = QGroupBox("Параметры генерации")
    generation_params_layout = QGridLayout()
    generation_params_group.setLayout(generation_params_layout)
    generation_params_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    generation_params_layout.addWidget(QLabel("Количество точек:"), 0, 0)
    generation_params_layout.addWidget(ui.points_input, 0, 1)
    generation_params_layout.addWidget(ui.fixed_corners_check, 0, 2)
    generation_params_layout.addWidget(ui.side_points_check, 0, 3)
    generation_params_layout.addWidget(ui.show_points_check, 1, 0, 1, 2)
    generation_params_layout.addWidget(QLabel("Размер точек:"), 1, 2)
    generation_params_layout.addWidget(ui.point_size_slider, 1, 3)
    generation_params_layout.addWidget(ui.show_lines_check, 2, 0, 1, 2)
    generation_params_layout.addWidget(QLabel("Толщина линий:"), 2, 2)
    generation_params_layout.addWidget(ui.line_width_slider, 2, 3)
    generation_params_layout.addWidget(ui.fill_triangles_check, 3, 0, 1, 2)
    generation_params_layout.addWidget(QLabel("Диапазон яркости:"), 3, 2)
    generation_params_layout.addWidget(ui.brightness_range_slider, 3, 3)
    generation_params_layout.addWidget(QLabel("Скорость переходов:"), 4, 0)
    generation_params_layout.addWidget(ui.transition_speed_slider, 4, 1, 1, 3)
    generation_params_layout.addWidget(QLabel("Скорость анимации:"), 5, 0)
    generation_params_layout.addWidget(ui.speed_slider, 5, 1, 1, 3)

    # Блок для действий (кнопки и прогресс-бар)
    actions_group = QGroupBox("Действия")
    actions_layout = QGridLayout()
    actions_group.setLayout(actions_layout)
    actions_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    ui.start_stop_button = QPushButton("Начать анимацию")
    ui.generate_frame_button = QPushButton("Сгенерировать кадр")
    ui.export_frame_button = QPushButton("Экспортировать кадр")
    ui.export_button = QPushButton("Экспортировать видео")

    ui.progress_bar = QProgressBar()
    ui.progress_bar.setMinimum(0)
    ui.progress_bar.setMaximum(100)
    ui.progress_bar.setValue(0)
    ui.progress_bar.setTextVisible(True)

    actions_layout.addWidget(ui.generate_frame_button, 0, 0, 1, 2)
    actions_layout.addWidget(ui.export_frame_button, 0, 2, 1, 2)
    actions_layout.addWidget(ui.start_stop_button, 1, 0, 1, 2)
    actions_layout.addWidget(ui.export_button, 1, 2, 1, 2)
    actions_layout.addWidget(QLabel("Прогресс экспорта:"), 2, 0, 1, 2)
    actions_layout.addWidget(ui.progress_bar, 2, 2, 1, 2)

    # Компоновка основного layout
    control_layout.addWidget(image_params_group)
    control_layout.addWidget(generation_params_group)
    control_layout.addWidget(main_color_group)
    control_layout.addWidget(bg_color_group)
    control_layout.addStretch()
    control_layout.addWidget(actions_group)

    return ui