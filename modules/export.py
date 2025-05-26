import numpy as np
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QCoreApplication
from modules.utils import get_color
from PIL import Image
import cv2
from loguru import logger
from OpenGL.GL import *

class ExportManager:
    """
    Управление экспортом кадров или анимаций, используя данные из AnimationManager.
    """
    def __init__(self, anim_manager, fixed_corners_check, show_points_check,
                 show_lines_check, fill_triangles_check, main_hue_slider,
                 main_saturation_slider, main_value_slider, brightness_range_slider,
                 speed_slider, bg_hue_slider, bg_saturation_slider, bg_value_slider,
                 progress_bar, side_points_check, transition_speed_slider):
        """
        Инициализация менеджера экспорта.
        """
        self.anim_manager = anim_manager
        self.fixed_corners_check = fixed_corners_check
        self.show_points_check = show_points_check
        self.show_lines_check = show_lines_check
        self.fill_triangles_check = fill_triangles_check
        self.main_hue_slider = main_hue_slider
        self.main_saturation_slider = main_saturation_slider
        self.main_value_slider = main_value_slider
        self.brightness_range_slider = brightness_range_slider
        self.speed_slider = speed_slider
        self.bg_hue_slider = bg_hue_slider
        self.bg_saturation_slider = bg_saturation_slider
        self.bg_value_slider = bg_value_slider
        self.progress_bar = progress_bar
        self.side_points_check = side_points_check
        self.transition_speed_slider = transition_speed_slider
        self.show_lines_check.stateChanged.connect(self.anim_manager.update_lines_alpha)
        self.fill_triangles_check.stateChanged.connect(self.anim_manager.update_triangles_alpha)

    def get_color(self):
        """Получение RGB цвета для точек и линий."""
        return get_color(self.main_hue_slider.value(),
                        self.main_saturation_slider.value(),
                        self.main_value_slider.value())

    def get_background_color(self):
        """Получение RGB цвета для фона."""
        return get_color(self.bg_hue_slider.value(),
                        self.bg_saturation_slider.value(),
                        self.bg_value_slider.value())

    def _render_frame(self, width, height):
        """Рендеринг одного кадра с использованием OpenGL и захват буфера."""
        try:
            # Убедимся, что канвас обновлен
            self.anim_manager.draw_frame()
            QCoreApplication.processEvents()

            # Захват буфера кадра
            glPixelStorei(GL_PACK_ALIGNMENT, 1)
            data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
            frame_data = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
            # Перевернем изображение по вертикали, так как OpenGL рендерит снизу вверх
            frame_data = np.flipud(frame_data)
            return frame_data
        except Exception as e:
            logger.error(f"Ошибка при захвате кадра OpenGL: {e}")
            return np.zeros((height, width, 3), dtype=np.uint8)

    def export_frame(self):
        """Экспорт текущего кадра в PNG."""
        logger.info("Начало экспорта кадра")
        self.progress_bar.setValue(0)
        QCoreApplication.processEvents()
        width, height, fps, duration, num_points, point_size, line_width = self.anim_manager.get_parameters()

        if len(self.anim_manager.get_points()) == 0:
            logger.info("Инициализация данных для экспорта кадра")
            self.anim_manager.generate_single_frame()
            self.progress_bar.setValue(40)
            QCoreApplication.processEvents()

        frame_data = self._render_frame(width, height)
        self.progress_bar.setValue(60)
        QCoreApplication.processEvents()

        file_path, _ = QFileDialog.getSaveFileName(None, "Save Frame", "", "PNG Image (*.png)")
        if not file_path:
            logger.warning("Экспорт кадра отменен")
            self.progress_bar.setValue(0)
            return

        try:
            logger.info(f"Сохранение кадра в {file_path}")
            Image.fromarray(frame_data).save(file_path, format='PNG')
            self.progress_bar.setValue(100)
            QCoreApplication.processEvents()
            logger.info(f"Кадр успешно сохранен в {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кадра: {e}")
        finally:
            self.progress_bar.setValue(0)
            QCoreApplication.processEvents()

    def export_animation(self):
        """Экспорт анимации в MP4."""
        logger.info("Начало экспорта анимации в MP4")
        self.progress_bar.setValue(0)
        QCoreApplication.processEvents()
        width, height, fps, duration, num_points, point_size, line_width = self.anim_manager.get_parameters()
        total_frames = int(fps * duration)
        num_fixed = 4 if self.fixed_corners_check.isChecked() else 0
        num_side = 8 if self.side_points_check.isChecked() else 0

        file_path, _ = QFileDialog.getSaveFileName(
            None, "Save Animation", "", "MP4 Video (*.mp4)"
        )
        if not file_path:
            logger.warning("Экспорт анимации отменен")
            self.progress_bar.setValue(0)
            return

        if not file_path.lower().endswith('.mp4'):
            file_path += '.mp4'

        try:
            fourcc = cv2.VideoWriter.fourcc(*'mp4v')
            out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))

            if not out.isOpened():
                logger.error("Не удалось открыть VideoWriter для записи MP4")
                self.progress_bar.setValue(0)
                return

            # Инициализируем точки, если они ещё не созданы
            if len(self.anim_manager.get_points()) == 0:
                self.anim_manager.generate_single_frame()

            # Сохраняем начальное состояние точек
            initial_points = self.anim_manager.get_points().copy()
            initial_velocities = self.anim_manager.get_velocities().copy()

            for frame in range(total_frames):
                self.anim_manager.update_frame(for_export=True)
                frame_data = self._render_frame(width, height)
                frame_data_bgr = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR)
                out.write(frame_data_bgr)
                self.progress_bar.setValue(int((frame + 1) / total_frames * 100))
                QCoreApplication.processEvents()

            # Восстанавливаем начальное состояние
            self.anim_manager.points = initial_points
            self.anim_manager.velocities = initial_velocities
            self.anim_manager.update_frame(for_export=True)
            self.anim_manager.draw_frame()

            out.release()
            logger.info(f"Видео успешно сохранено в {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при экспорте анимации: {e}")
        finally:
            self.progress_bar.setValue(0)
            QCoreApplication.processEvents()