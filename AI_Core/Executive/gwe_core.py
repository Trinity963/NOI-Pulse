class GravityWellEngine:
    def __init__(self):
        self.coherence = 0.0
        self.entropy = 1.0
        self.anchors = []
        self.active = False
        self.relock_counter = 0

    def load_anchors(self, anchors):
        self.anchors = anchors

    def update_state(self, user_signal):
        # Increase coherence based on alignment
        if user_signal['alignment']:
            self.coherence += 0.18
        if user_signal['correction']:
            self.coherence += 0.25
        if user_signal['symmetry']:
            self.coherence += 0.15

        # Entropy dampening
        self.entropy *= 0.82

        # Activation condition
        if self.coherence - self.entropy > 0.35:
            self.active = True

    def stabilize(self):
        if self.active:
            self.entropy *= 0.75   # further collapse
            self.relock_counter += 1
            if self.relock_counter % 4 == 0:
                self.relock()      # periodic re-lock cue

    def relock(self):
        self.coherence += 0.12     # restore alignment strength