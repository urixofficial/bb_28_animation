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

    def export_frame(self):
        """Экспорт текущего кадра в изображение."""
        logger.info("Начало экспорта кадра")
        try:
            width, height, _, _, _, _, _ = self.anim_manager.get_parameters()
            file_path, _ = QFileDialog.getSaveFileName(
                None, "Сохранить кадр", "", "PNG Files (*.png);;All Files (*)"
            )
            if not file_path:
                logger.info("Экспорт кадра отменён")
                return

            self.anim_manager.draw_frame()
            glPixelStorei(GL_PACK_ALIGNMENT, 1)
            data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
            image = Image.frombytes("RGB", (width, height), data)
            image = image.transpose(Image.FLIP_VERTICAL)
            image.save(file_path, "PNG")
            logger.info(f"Кадр успешно экспортирован: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка экспорта кадра: {e}")

    def export_animation(self):
        """Экспорт анимации в видео."""
        logger.info("Начало экспорта анимации")
        try:
            width, height, fps, duration, num_points, point_size, line_width = self.anim_manager.get_parameters()
            file_path, _ = QFileDialog.getSaveFileName(
                None, "Сохранить анимацию", "", "MP4 Files (*.mp4);;All Files (*)"
            )
            if not file_path:
                logger.info("Экспорт анимации отменён")
                return

            total_frames = int(fps * duration)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
            self.progress_bar.setMaximum(total_frames)
            self.progress_bar.setValue(0)

            # Инициализация точек для анимации
            self.anim_manager.initialize_points(num_points, width, height)
            self.anim_manager.lines_alpha = 1.0 if self.show_lines_check.isChecked() else 0.0
            self.anim_manager.triangles_alpha = 1.0 if self.fill_triangles_check.isChecked() else 0.0
            self.anim_manager.canvas.lines_alpha = self.anim_manager.lines_alpha
            self.anim_manager.canvas.triangles_alpha = self.anim_manager.triangles_alpha
            self.anim_manager.update_triangulation_and_colors()

            for frame in range(total_frames):
                self.anim_manager.update_frame(for_export=True)
                glPixelStorei(GL_PACK_ALIGNMENT, 1)
                data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
                image = Image.frombytes("RGB", (width, height), data)
                image = image.transpose(Image.FLIP_VERTICAL)
                frame_data = np.array(image)
                frame_data = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR)
                out.write(frame_data)
                self.progress_bar.setValue(frame + 1)
                QCoreApplication.processEvents()

            out.release()
            logger.info(f"Анимация успешно экспортирована: {file_path}")
            self.progress_bar.setValue(0)
        except Exception as e:
            logger.error(f"Ошибка экспорта анимации: {e}")
            if 'out' in locals():
                out.release()
            self.progress_bar.setValue(0)