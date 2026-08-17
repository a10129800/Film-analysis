from PySide6.QtCore import QObject, QTimer, QElapsedTimer


class PlaybackController(QObject):

    def __init__(
        self,
        player,
        duration_provider
    ):
        super().__init__()

        self.player = player
        self.duration_provider = duration_provider

        self.forward_speed = 1.0
        self.playback_speeds = [
            1.0,
            2.0,
            4.0,
            8.0
        ]

        self.reverse_clock = QElapsedTimer()

        self.reverse_timer = QTimer(self)
        self.reverse_timer.setInterval(150)
        self.reverse_timer.timeout.connect(
            self.reverse_step
        )

        self.forward_timer = QTimer(self)
        self.forward_timer.setInterval(50)
        self.forward_timer.timeout.connect(
            self.forward_step
        )

    def reverse_step(self):

        elapsed_ms = self.reverse_clock.restart()

        if elapsed_ms <= 0:
            return

        step_ms = int(
            elapsed_ms * self.forward_speed
        )

        position = self.player.position()

        new_position = max(
            0,
            position - step_ms
        )

        self.player.setPosition(
            new_position
        )

        if new_position <= 0:
            self.reverse_timer.stop()

    def forward_step(self):

        step_ms = int(
            50 * self.forward_speed
        )

        position = self.player.position()

        duration_ms = self.duration_provider()

        new_position = min(
            duration_ms,
            position + step_ms
        )

        self.player.setPosition(
            new_position
        )

        if new_position >= duration_ms:
            self.forward_timer.stop()

    def play_backward(self):

        self.forward_timer.stop()

        speeds = self.playback_speeds

        if self.reverse_timer.isActive():

            if self.forward_speed in speeds:
                index = speeds.index(
                    self.forward_speed
                )
            else:
                index = 0

            self.forward_speed = speeds[
                (index + 1) % len(speeds)
            ]

            self.reverse_clock.restart()

        else:

            self.forward_speed = 1.0

            self.player.pause()

            position = self.player.position()

            new_position = max(
                0,
                position - 200
            )

            self.player.setPosition(
                new_position
            )

            self.reverse_clock.start()

            self.reverse_timer.start()

    def play_forward(self):

        self.reverse_timer.stop()

        speeds = self.playback_speeds

        if self.forward_speed in speeds:
            index = speeds.index(
                self.forward_speed
            )
        else:
            index = 0

        self.forward_speed = speeds[
            (index + 1) % len(speeds)
        ]

        self.player.setPlaybackRate(
            self.forward_speed
        )

        self.player.play()

    def increase_playback_speed(self):

        speeds = self.playback_speeds

        if self.forward_speed in speeds:
            index = speeds.index(
                self.forward_speed
            )
        else:
            index = 0

        self.forward_speed = speeds[
            (index + 1) % len(speeds)
        ]

        self.player.setPlaybackRate(
            self.forward_speed
        )

    def set_playback_speed(self, speed):

        speed = float(speed)

        if speed <= 0:
            return

        self.forward_speed = speed

        self.player.setPlaybackRate(
            self.forward_speed
        )

    def seek_relative(self, offset_ms):

        position = self.player.position()

        duration_ms = self.duration_provider()

        new_position = max(
            0,
            min(
                duration_ms,
                position + offset_ms
            )
        )

        self.player.setPosition(
            new_position
        )

    def stop(self):

        self.reverse_timer.stop()
        self.forward_timer.stop()
        self.reverse_clock.invalidate()
        self.player.pause()

