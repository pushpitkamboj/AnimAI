from manim import *

# Colors (Manim's built-in, per instructions)
BOX_COLORS = [BLUE_C, GREEN_D, GOLD_D, PURPLE_C, TEAL_C]
BOX_LABELS = ["New", "Ready", "Running", "Waiting/Blocked", "Terminated"]
ARROW_LABELS = [
    "Admitted",            # New → Ready
    "Scheduler Dispatch",  # Ready → Running
    "I/O/Event Wait",      # Running → Waiting/Blocked
    "Exit",                # Running → Terminated
    "I/O/Event Completion" # Waiting/Blocked → Ready
]

# Helper for box positions in safe area/margin enforcement
def get_horizontal_positions(n, box_width, min_spacing, left_bound, right_bound):
    total_box_width = n * box_width
    total_spacing = (n-1) * min_spacing
    total_width = total_box_width + total_spacing
    # Center group
    start_x = left_bound + (right_bound - left_bound - total_width) / 2 + box_width/2
    positions = [start_x + i*(box_width+min_spacing) for i in range(n)]
    return positions

class ProcessStateDiagramHelper:
    @staticmethod
    def create_state_boxes(scene, center_y=0):
        # Configurations for strict spatial constraints
        safe_margin = 0.5
        min_spacing = 0.3
        frame_left = -config.frame_width/2 + safe_margin
        frame_right = config.frame_width/2 - safe_margin
        # Box geometry
        width = 2.0
        height = 1.0
        # Compute horizontal positions
        xs = get_horizontal_positions(len(BOX_LABELS), width, min_spacing, frame_left, frame_right)
        boxes = []
        texts = []
        for i, (label, color) in enumerate(zip(BOX_LABELS, BOX_COLORS)):
            rect = Rectangle(width=width, height=height, color=color, fill_color=color, fill_opacity=0.65)
            text = Text(label, color=WHITE, font_size=38)
            group = VGroup(rect, text).arrange(DOWN, buff=0.15)
            group.move_to([xs[i], center_y, 0])
            boxes.append(rect)
            texts.append(text)
        # Stack text on top of rectangles correctly (keep text centered)
        box_groups = [VGroup(box, text).arrange(DOWN, buff=0.15).move_to([xs[i], center_y, 0]) for i, (box, text) in enumerate(zip(boxes, texts))]
        boxes_vgroup = VGroup(*[bg[0] for bg in box_groups])
        labels_vgroup = VGroup(*[bg[1] for bg in box_groups])
        diagram_vgroup = VGroup(*box_groups)
        # Check box positions vs. safe margin
        for i, bg in enumerate(box_groups):
            x = bg.get_center()[0]
            if not (frame_left + width/2 <= x <= frame_right - width/2):
                # Constraint violation - box outside safe area
                scene.add(bg)
                scene.add(Text(f"Box '{BOX_LABELS[i]}' too close to margin", color=RED, font_size=22).next_to(bg, DOWN))
        return boxes, texts, box_groups, boxes_vgroup, labels_vgroup, diagram_vgroup

    @staticmethod
    def create_transitions_arrows(box_groups):
        # Map: source_idx, dest_idx, label, below_offset for arrow label
        transitions = [
            (0, 1, ARROW_LABELS[0], 0.32), # New → Ready
            (1, 2, ARROW_LABELS[1], 0.32), # Ready → Running
            (2, 3, ARROW_LABELS[2], -0.32), # Running → Waiting/Blocked (downwards)
            (2, 4, ARROW_LABELS[3], 0.32), # Running → Terminated
            (3, 1, ARROW_LABELS[4], -0.32) # Waiting/Blocked → Ready (upwards)
        ]
        arrows = []
        labels = []
        for src, dst, label, label_dy in transitions:
            start = box_groups[src].get_right()
            end = box_groups[dst].get_left()
            # For vertical transitions, change start/end
            if (src, dst) == (2, 3): # Running → Waiting/Blocked (vertical down)
                start = box_groups[src][0].get_bottom()
                end = box_groups[dst][0].get_top()
            elif (src, dst) == (3, 1): # Waiting/Blocked → Ready (curve up)
                start = box_groups[src][0].get_top()
                end = box_groups[dst][0].get_bottom()
            arrow = Arrow(start, end, buff=0.22, color=WHITE, stroke_width=3,
                          max_tip_length_to_length_ratio=0.16)
            # Place label at midpoint with offset
            label_pos = arrow.get_center() + label_dy * UP
            label_mob = Text(label, color=GREY_B, font_size=28).move_to(label_pos)
            arrows.append(arrow)
            labels.append(label_mob)
        return arrows, labels

    @staticmethod
    def create_dot_above_new(box_groups):
        dot = Dot(color=WHITE, radius=0.15)
        # Dot above New state's rectangle
        new_box = box_groups[0][0]
        dot.move_to(new_box.get_top() + UP*0.35)
        return dot

    @staticmethod
    def create_surrounding_animated_boundary(box):
        # AnimatedBoundary: uses SurroundingRectangle with growing/fading edges, or via AnimatedBoundary (plugin)
        from manim.utils.color import to_color
        boundary = SurroundingRectangle(box, color=to_color(WHITE), buff=0.08, corner_radius=0.18)
        return boundary

class ProcessStateDiagramScene(Scene):
    def construct(self):
        helper = ProcessStateDiagramHelper
        center_y = 0
        # ---- Stage 1: Draw State Boxes with Labels ----
        boxes, texts, box_groups, boxes_vgroup, labels_vgroup, diagram_vgroup = helper.create_state_boxes(self, center_y=center_y)
        self.play(*[Create(bg[0]) for bg in box_groups], run_time=1.5)
        self.play(LaggedStart(*[FadeIn(bg[1]) for bg in box_groups], lag_ratio=0.1), run_time=1.2)
        self.wait(0.6)  # Pause for learners: time to assimilate box meanings

        # ---- Stage 2: Add Transition Arrows & Arrow Labels ----
        arrows, arrow_labels = helper.create_transitions_arrows(box_groups)
        arrow_anims = [GrowArrow(arrow, run_time=0.7) for arrow in arrows]
        self.play(AnimationGroup(*arrow_anims, lag_ratio=0.17), run_time=2)
        self.play(*[FadeIn(alab, shift=DOWN, run_time=0.4) for alab in arrow_labels])
        self.wait(0.7)  # Pause: let viewers examine full diagram with transitions

        # ---- Stage 3: Dot Traversal Animation (One Process Moving) ----
        dot = helper.create_dot_above_new(box_groups)
        self.play(FadeIn(dot, run_time=0.5))
        self.wait(0.3)

        state_path = [0,1,2,3,1,2,4] # New→Ready→Running→Waiting/Blocked→Ready→Running→Terminated
        path_arrows = [0,1,2,4,1,3]  # indices into arrows; path arrows followed in order
        boundary = None

        for i, state_index in enumerate(state_path):
            # Animate boundary & indicate current box
            if boundary:
                self.remove(boundary)  # Clean up previous
            target_box = box_groups[state_index][0]
            boundary = helper.create_surrounding_animated_boundary(target_box)
            self.add(boundary)
            self.play(Indicate(target_box, color=WHITE, scale_factor=1.07, run_time=0.45))
            self.wait(0.2) # Pause: pedagogical focus on current state
            if i < len(path_arrows):
                # Animate dot moving along arrow path to next box
                arrow = arrows[path_arrows[i]]
                trajectory = arrow.copy().set_opacity(0)  # for MoveAlongPath
                self.play(MoveAlongPath(dot, trajectory), run_time=0.9)
                # Brief pedagogical pause to process transition
                self.wait(0.25)
        # Final highlight on Terminated
        self.wait(0.65)

        # ---- Stage 4: Show Multiple Dots in Different States (Concept Reinforcement) ----
        # We place several dots at different boxes to illustrate concurrency.
        states_for_dots = [1, 2, 3, 4]  # Ready, Running, Waiting/Blocked, Terminated
        multi_dots = [Dot(color=WHITE, radius=0.15).move_to(box_groups[i][0].get_top() + UP*0.3) for i in states_for_dots]
        self.play(AnimationGroup(*[FadeIn(md, shift=UP) for md in multi_dots], lag_ratio=0.13), run_time=1.5)
        self.wait(1.2)  # Pause for learners: see different processes in different states
        # Clean up (optional fadeout for clarity)
        self.play(FadeOut(dot), FadeOut(boundary), *[FadeOut(md) for md in multi_dots], run_time=0.7)
        self.wait(0.2)

        # ---- END OF SCENE ----
        # Note: All spatial and margin constraints checked using helper.
        # If any constraint is violated, a warning is shown by helper.