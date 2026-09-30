from django.db import models


class HighScore(models.Model):
    player_name = models.CharField(max_length=40)
    seconds = models.PositiveIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["seconds", "completed_at"]

    def __str__(self):
        return f"{self.player_name} - {self.seconds}s"

    @property
    def minutes_seconds(self):
        m, s = divmod(self.seconds, 60)
        return f"{m}:{s:02d}"
