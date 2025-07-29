import pathlib
import pytest
import sys
import os

# Add project root to path so modules import correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from types import SimpleNamespace
from Graphics import Graphics

# ─── Fake Classes ──────────────────────────────────────────────────────────

class FakeImg:
    """A fake Img class to simulate loaded images."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<FakeImg {self.name}>"

# Replace _load_sprites to avoid needing real image files
def fake_load_sprites(self, folder):
    return [FakeImg("frame0"), FakeImg("frame1"), FakeImg("frame2")]

# ─── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def fake_board():
    """Returns a fake board with fixed cell size for consistent image sizing."""
    return SimpleNamespace(cell_W_pix=32, cell_H_pix=32)

@pytest.fixture
def graphics(fake_board):
    """Returns a Graphics object using fake board and fake images."""
    Graphics._load_sprites = fake_load_sprites
    return Graphics(pathlib.Path("."), board=fake_board, loop=True, fps=2.0)

# ─── Tests ─────────────────────────────────────────────────────────────────

def test_WhenReset_ThenStartTimeAndFrameReset(graphics):
    """
    Test that reset(cmd) sets the start time and resets current frame to 0.
    Verifies it uses the timestamp from the given command.
    """
    cmd = SimpleNamespace(timestamp=1000)  # Fake Command
    graphics.reset(cmd)
    assert graphics.start_time == 1000
    assert graphics.current_frame == 0

def test_WhenUpdateBeforeStart_ThenFrameZero(graphics):
    """
    Test that if update() is called with time before start_time,
    the current frame remains 0.
    """
    graphics.start_time = 500
    graphics.update(now_ms=400)  # Time before start
    assert graphics.current_frame == 0

def test_WhenUpdateLooping_ThenFrameCycles(graphics):
    """
    Test that update() correctly loops the animation frames if looping is enabled.
    At 2000ms with fps=2.0 → frame time = 500ms → frame_index = 4,
    and with 3 frames, should cycle: 4 % 3 = 1
    """
    graphics.start_time = 0
    graphics.update(now_ms=2000)
    assert graphics.current_frame == 1

def test_WhenUpdateNotLooping_ThenFrameStops(fake_board):
    """
    Test that update() stops at the last frame if looping is disabled.
    Even if time progresses past the last frame, it should clamp.
    """
    Graphics._load_sprites = fake_load_sprites
    g = Graphics(pathlib.Path("."), board=fake_board, loop=False, fps=2.0)
    g.start_time = 0
    g.update(now_ms=5000)  # Way beyond last frame
    assert g.current_frame == 2  # Should clamp to last frame

def test_WhenGetImg_ThenReturnsCorrectFrame(graphics):
    """
    Test that get_img() returns the correct FakeImg object
    corresponding to current_frame.
    """
    graphics.current_frame = 2
    img = graphics.get_img()
    assert isinstance(img, FakeImg)
    assert img.name == "frame2"