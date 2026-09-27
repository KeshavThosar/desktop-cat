import sys
import os

if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QKeyEvent, QMouseEvent, QCloseEvent
from PyQt6.QtWidgets import QApplication, QWidget

SCREEN_SIZE = (180, 180)
SPRITE_SCALE = 5
SPRITE_W = 32 * SPRITE_SCALE
SPRITE_H = 32 * SPRITE_SCALE

animation_frames = {
    "sitting": [(x, 0) for x in range(10)] + [(x, 1) for x in range(10)],
    "eating": [(x, 13) for x in range(15)],
    "sitting_to_sleep": [(x, 17) for x in range(10)],
    "sleep_sitting": [(10, 17)],
    "sleep_sitting_end": [(11, 17)],
}

animation_offset = {
    "sitting": (32, 0),
    "eating": (20, 0),
    "sitting_to_sleep": (10, 0),
    "sleep_sitting": (10, 0),
    "sleep_sitting_end": (10, 0),
}


class TransparentPetWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Load and scale sprite sheet
        sprite_dir = Path(__file__).parent.resolve()
        original_sheet = QPixmap(str(sprite_dir / "cat.png"))

        scaled_width = original_sheet.width() * SPRITE_SCALE
        scaled_height = original_sheet.height() * SPRITE_SCALE
        self.sprite_sheet = original_sheet.scaled(
            scaled_width,
            scaled_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

        # Configure animation sequence
        self.animations = []
        self.animations += ["sitting"] * 3
        self.animations += ["eating"] * 3
        self.animations += ["sitting_to_sleep"]
        self.animations += ["sleep_sitting"] * 30
        self.animations += ["sleep_sitting_end"] * 6

        self.anim_index = 0
        self.frame_index = 0

        # Dragging state
        self.drag_position = QPoint()

        # Configure transparent window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(*SCREEN_SIZE)

        # Position window at bottom-right of the screen
        primary_screen = QApplication.primaryScreen()
        
        if not primary_screen:
            return
        
        screen_geometry = primary_screen.availableGeometry()
        margin = 20  # pixels of padding from the screen edges
        x = screen_geometry.right() - SCREEN_SIZE[0] - margin
        y = screen_geometry.bottom() - SCREEN_SIZE[1] - margin
        self.move(x, y)

        # Timer to replace Pygame clock (6 FPS ≈ 166ms per frame)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(166)

    def next_frame(self):
        current_anim = self.animations[self.anim_index]
        frames = animation_frames[current_anim]

        self.frame_index += 1
        if self.frame_index >= len(frames):
            self.frame_index = 0
            self.anim_index = (self.anim_index + 1) % len(self.animations)

        self.update()  # Triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Clear background to transparent
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        current_anim = self.animations[self.anim_index]
        frame = animation_frames[current_anim][self.frame_index]

        # Calculate crop rectangle from sprite sheet
        crop_x = frame[0] * SPRITE_W
        crop_y = frame[1] * SPRITE_H

        # Calculate destination offset on screen
        offset_x, offset_y = animation_offset[current_anim]

        # Draw cropped frame onto window
        painter.drawPixmap(
            offset_x, offset_y, self.sprite_sheet, crop_x, crop_y, SPRITE_W, SPRITE_H
        )

    # Click and Drag Handlers

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            globalPosition = event.globalPosition().toPoint()
            frameTopLeft = self.frameGeometry().topLeft()

            self.drag_position = globalPosition - frameTopLeft
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            globalPosition = event.globalPosition().toPoint()
            self.move(globalPosition - self.drag_position)
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def closeEvent(self, event: QCloseEvent):
        """Cleanly stop timers and exit application when window closes."""
        self.timer.stop()
        QApplication.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Ensure application exits cleanly when last window closes
    app.setQuitOnLastWindowClosed(True)

    window = TransparentPetWindow()
    window.show()

    sys.exit(app.exec())