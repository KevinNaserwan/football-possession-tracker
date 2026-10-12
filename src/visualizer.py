import matplotlib
matplotlib.use("Agg") # Non-interactive headless backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import Dict, Any, Optional

class PitchVisualizer:
    """
    Renders 2D tactical football pitch diagrams with:
    - Standard FIFA lines (penalty boxes, center circle, halfway line)
    - Home & Away player positions with velocity arrows
    - Ball position and trajectory
    - Optional Spearman Pitch Control probability surface overlay
    """
    def __init__(self, pitch_length: float = 105.0, pitch_width: float = 68.0):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def draw_pitch(self, ax: plt.Axes, bg_color: str = "#14532d", line_color: str = "#ffffff"):
        """Draws standard football pitch markings on matplotlib axes"""
        ax.set_facecolor(bg_color)
        
        # Pitch boundary
        rect = patches.Rectangle((0, 0), self.pitch_length, self.pitch_width, linewidth=1.8, edgecolor=line_color, facecolor="none")
        ax.add_patch(rect)

        # Halfway line & Center circle
        ax.plot([self.pitch_length / 2, self.pitch_length / 2], [0, self.pitch_width], color=line_color, linewidth=1.5)
        center_circle = patches.Circle((self.pitch_length / 2, self.pitch_width / 2), 9.15, edgecolor=line_color, facecolor="none", linewidth=1.5)
        center_spot = patches.Circle((self.pitch_length / 2, self.pitch_width / 2), 0.5, facecolor=line_color)
        ax.add_patch(center_circle)
        ax.add_patch(center_spot)

        # Penalty boxes
        # Left penalty box
        ax.add_patch(patches.Rectangle((0, (self.pitch_width - 40.32) / 2), 16.5, 40.32, edgecolor=line_color, facecolor="none", linewidth=1.5))
        # Right penalty box
        ax.add_patch(patches.Rectangle((self.pitch_length - 16.5, (self.pitch_width - 40.32) / 2), 16.5, 40.32, edgecolor=line_color, facecolor="none", linewidth=1.5))

        # Goal areas (6 yard box)
        ax.add_patch(patches.Rectangle((0, (self.pitch_width - 18.32) / 2), 5.5, 18.32, edgecolor=line_color, facecolor="none", linewidth=1.2))
        ax.add_patch(patches.Rectangle((self.pitch_length - 5.5, (self.pitch_width - 18.32) / 2), 5.5, 18.32, edgecolor=line_color, facecolor="none", linewidth=1.2))

        ax.set_xlim(-2, self.pitch_length + 2)
        ax.set_ylim(-2, self.pitch_width + 2)
        ax.set_aspect("equal")
        ax.axis("off")

    def render_frame(
        self,
        frame_data: Dict[str, Any],
        pitch_control_surface: Optional[np.ndarray] = None,
        output_file: Optional[str] = None,
        title: str = "Match Frame Possession"
    ) -> plt.Figure:
        """
        Renders a single frame with players, ball, and optional pitch control overlay.
        """
        fig, ax = plt.subplots(figsize=(12, 8), dpi=120)
        self.draw_pitch(ax)

        # 1. Overlay Pitch Control heatmap if provided
        if pitch_control_surface is not None:
            # Home control in red/blue colormap
            im = ax.imshow(
                pitch_control_surface,
                extent=[0, self.pitch_length, 0, self.pitch_width],
                origin="lower",
                cmap="bwr",
                alpha=0.35,
                vmin=0.0,
                vmax=1.0
            )

        # 2. Plot Players
        players = frame_data.get("players", [])
        for p in players:
            color = "#ef4444" if p.get("team") == "Home" else "#3b82f6" # Red vs Blue
            px, py = p.get("x", 0.0), p.get("y", 0.0)
            ax.scatter(px, py, color=color, s=120, edgecolors="white", linewidths=1.2, zorder=5)
            
            # Player label
            ax.text(px, py + 1.2, p.get("id", ""), color="white", fontsize=8, ha="center", weight="bold", zorder=6)

            # Velocity vector arrow
            vx, vy = p.get("vx", 0.0), p.get("vy", 0.0)
            if abs(vx) > 0.1 or abs(vy) > 0.1:
                ax.arrow(px, py, vx * 0.8, vy * 0.8, color="yellow", width=0.15, head_width=0.8, zorder=4)

        # 3. Plot Ball
        ball = frame_data.get("ball", {})
        if ball:
            bx, by = ball.get("x", 0.0), ball.get("y", 0.0)
            ax.scatter(bx, by, color="#ffffff", s=100, edgecolors="#000000", linewidths=1.5, zorder=10)

        plt.title(f"{title} (Frame #{frame_data.get('frame_id', 0)})", color="white", fontsize=14, weight="bold", pad=15)
        fig.patch.set_facecolor("#0b0f19")
        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, facecolor=fig.get_facecolor(), bbox_inches="tight")
            plt.close(fig)

        return fig
