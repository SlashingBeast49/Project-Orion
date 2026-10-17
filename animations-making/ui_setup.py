from manim import *

cyan = "#ff8800"
dark_grey = "#3D3D3D"

class scene1(Scene):
    def construct(self):
        title = Text("O R I O N", font="Helvetica", weight=BOLD).scale(2).set_color(cyan)
        subtitle = Text("SYSTEM SETUP LOADING", font="Courier").scale(0.5).next_to(title, DOWN, buff=0.5).set_color(WHITE)
        orbit = Circle(radius=3.5, color=dark_grey).set_stroke(opacity=0.5)
        tracker_dot = Dot(color=cyan).move_to(orbit.point_from_proportion(0))
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle, shift=UP), Create(orbit), run_time=1)
        self.play(MoveAlongPath(tracker_dot, orbit), run_time=2)
        self.play(ShrinkToCenter(orbit), ShrinkToCenter(tracker_dot),FadeOut(title, scale=1.5), FadeOut(subtitle), run_time=2)
        self.wait(0.5)