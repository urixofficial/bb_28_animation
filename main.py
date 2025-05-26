import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from modules.control import setup_control_panel
from modules.canvas import OpenGLCanvas
from modules.animation import AnimationManager
from modules.export import ExportManager
from loguru import logger

class VideoGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Generator")
        logger.add("app.log", rotation="10 MB", level="DEBUG")
        self.ui = setup_control_panel(self, self.get_parameters, OpenGLCanvas)
        self.anim_manager = AnimationManager(
            self.ui.canvas,
            self.get_parameters,
            self.ui.fixed_corners_check,
            self.ui.show_points_check,
            self.ui.show_lines_check,
            self.ui.fill_triangles_check,
            self.ui.main_hue_slider,
            self.ui.main_saturation_slider,
            self.ui.main_value_slider,
            self.ui.brightness_range_slider,
            self.ui.speed_slider,
            self.ui.bg_hue_slider,
            self.ui.bg_saturation_slider,
            self.ui.bg_value_slider,
            self.ui.side_points_check,
            self.ui.transition_speed_slider
        )
        self.export_manager = ExportManager(
            self.anim_manager,
            self.ui.fixed_corners_check,
            self.ui.show_points_check,
            self.ui.show_lines_check,
            self.ui.fill_triangles_check,
            self.ui.main_hue_slider,
            self.ui.main_saturation_slider,
            self.ui.main_value_slider,
            self.ui.brightness_range_slider,
            self.ui.speed_slider,
            self.ui.bg_hue_slider,
            self.ui.bg_saturation_slider,
            self.ui.bg_value_slider,
            self.ui.progress_bar,
            self.ui.side_points_check,
            self.ui.transition_speed_slider
        )
        self.is_animating = False
        self.setup_connections()
        # Генерируем начальный кадр для предпросмотра
        self.anim_manager.generate_single_frame()

    def get_parameters(self):
        """Получение параметров анимации из UI."""
        try:
            width = int(self.ui.width_input.text())
            height = int(self.ui.height_input.text())
            fps = float(self.ui.fps_input.text())
            duration = float(self.ui.duration_input.text())
            num_points = int(self.ui.points_input.text())
            point_size = self.ui.point_size_slider.value()
            line_width = self.ui.line_width_slider.value()
            return width, height, fps, duration, num_points, point_size, line_width
        except ValueError as e:
            logger.error(f"Ошибка получения параметров: {e}")
            return 1080, 1080, 30, 5, 50, 20, 4

    def setup_connections(self):
        """Настройка соединений сигналов и слотов."""
        # Анимация и генерация кадров
        self.ui.start_stop_button.clicked.connect(self.toggle_animation)
        self.ui.generate_frame_button.clicked.connect(self.anim_manager.generate_single_frame)
        self.ui.export_frame_button.clicked.connect(self.export_frame)
        self.ui.export_button.clicked.connect(self.export_animation)

        # Изменение размеров холста или количества точек (требует новой генерации точек)
        self.ui.width_input.textChanged.connect(self.anim_manager.update_points_and_frame)
        self.ui.height_input.textChanged.connect(self.anim_manager.update_points_and_frame)
        self.ui.points_input.textChanged.connect(self.anim_manager.update_points_and_frame)
        self.ui.fixed_corners_check.stateChanged.connect(self.anim_manager.update_points_and_frame)
        self.ui.side_points_check.stateChanged.connect(self.anim_manager.update_points_and_frame)

        # Изменение параметров отрисовки (не влияет на позиции точек)
        self.ui.show_points_check.stateChanged.connect(self.anim_manager.draw_frame)
        self.ui.brightness_range_slider.valueChanged.connect(self.anim_manager.update_render_parameters)
        self.ui.main_hue_slider.valueChanged.connect(self.anim_manager.update_render_parameters)
        self.ui.main_saturation_slider.valueChanged.connect(self.anim_manager.update_render_parameters)
        self.ui.main_value_slider.valueChanged.connect(self.anim_manager.update_render_parameters)
        self.ui.bg_hue_slider.valueChanged.connect(self.anim_manager.update_render_parameters)
        self.ui.bg_saturation_slider.valueChanged.connect(self.anim_manager.update_render_parameters)
        self.ui.bg_value_slider.valueChanged.connect(self.anim_manager.update_render_parameters)
        self.ui.point_size_slider.valueChanged.connect(self.anim_manager.draw_frame)
        self.ui.line_width_slider.valueChanged.connect(self.anim_manager.draw_frame)
        self.ui.transition_speed_slider.valueChanged.connect(self.anim_manager.update_render_parameters)

        # Изменение скорости (влияет только на velocities, не на позиции)
        self.ui.speed_slider.valueChanged.connect(self.anim_manager.update_velocities)

    def toggle_animation(self):
        """Переключение состояния анимации (запуск/остановка)."""
        if self.is_animating:
            self.anim_manager.stop_animation()
            self.ui.start_stop_button.setText("Начать анимацию")
            self.is_animating = False
        else:
            self.anim_manager.start_animation()
            self.ui.start_stop_button.setText("Остановить анимацию")
            self.is_animating = True

    def export_frame(self):
        """Экспорт текущего кадра с остановкой анимации."""
        if self.is_animating:
            self.anim_manager.stop_animation()
            self.ui.start_stop_button.setText("Начать анимацию")
            self.is_animating = False
        self.export_manager.export_frame()

    def export_animation(self):
        """Экспорт анимации с остановкой текущей анимации."""
        if self.is_animating:
            self.anim_manager.stop_animation()
            self.ui.start_stop_button.setText("Начать анимацию")
            self.is_animating = False
        self.export_manager.export_animation()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoGenerator()
    window.show()
    sys.exit(app.exec())