"""Run away dancing the mat."""

import argparse
import fractions
import importlib.resources
import os.path
import pathlib
import sys
import time
from typing import Optional, Final, List, Union, Tuple, Sequence, Any, MutableMapping

import pygame
import pygame.freetype
from icontract import require, ensure

import dancerunaway
import dancerunaway.events
from dancerunaway.common import assert_never

assert dancerunaway.__doc__ == __doc__

PACKAGE_DIR = (
    pathlib.Path(str(importlib.resources.files(__package__)))  # type: ignore
    if __package__ is not None
    else pathlib.Path(os.path.realpath(__file__)).parent
)


class MaskedSprite:
    """Represent a sprite with a bitmask."""

    sprite: Final[pygame.surface.Surface]
    mask: Final[pygame.mask.Mask]

    #: Offset of the first masked pixel
    first_masked_x: Final[int]

    #: Offset of the last masked pixel
    last_masked_x: Final[int]

    def __init__(self, sprite: pygame.surface.Surface) -> None:
        """Initialize with the given values."""
        self.sprite = sprite
        self.mask = pygame.mask.from_surface(sprite)

        rect_union = None  # type: Any
        for bounding_rect in self.mask.get_bounding_rects():
            if rect_union is None:
                rect_union = bounding_rect
            else:
                rect_union.union_ip(bounding_rect)

        assert rect_union is not None, "Unexpected invisible sprite"
        self.first_masked_x = rect_union.left
        self.last_masked_x = rect_union.right

    def get_height(self) -> int:
        """Return the height of the sprite."""
        return self.sprite.get_height()

    def get_width(self) -> int:
        """Return the width of the sprite."""
        return self.sprite.get_width()

    def get_size(self) -> Tuple[int, int]:
        """Return the size of the sprite."""
        return self.get_size()


class Level:
    """Bundle the appearance of a level."""

    def __init__(
        self,
        bg_decor: pygame.surface.Surface,
        foreground: pygame.surface.Surface,
        ground: pygame.surface.Surface,
        middle_decor: pygame.surface.Surface,
        sky: pygame.surface.Surface,
    ):
        """Initialize with the given values."""
        self.bg_decor = bg_decor
        self.foreground = foreground
        self.ground = ground
        self.middle_decor = middle_decor
        self.sky = sky


class Media:
    """Represent all the media loaded in the main memory from the file system."""

    def __init__(
        self,
        levels: List[Level],
        runaways: List[List[MaskedSprite]],
        chasers: List[List[MaskedSprite]],
        ship: pygame.surface.Surface,
        font: pygame.freetype.Font,
        music_path: pathlib.Path,
    ) -> None:
        """Initialize with the given values."""
        self.levels = levels
        self.runaways = runaways
        self.chasers = chasers
        self.ship = ship
        self.font = font
        self.music_path = music_path


SCENE_WIDTH = 640
SCENE_HEIGHT = 480


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def load_media() -> Tuple[Optional[Media], Optional[str]]:
    """Load the media from the file system."""
    images_dir = PACKAGE_DIR / "media/images"

    levels = []  # type: List[Level]
    for level_dir in sorted(
        pth_dir for pth_dir in images_dir.glob("level*") if pth_dir.is_dir()
    ):
        pth = level_dir / "bg_decor.png"
        try:
            bg_decor = pygame.image.load(str(pth)).convert_alpha()
        except Exception as exception:
            return None, f"Failed to load {pth}: {exception}"

        pth = level_dir / "foreground.png"
        try:
            foreground = pygame.image.load(str(pth)).convert_alpha()
        except Exception as exception:
            return None, f"Failed to load {pth}: {exception}"

        pth = level_dir / "ground.png"
        try:
            ground = pygame.image.load(str(pth)).convert_alpha()
        except Exception as exception:
            return None, f"Failed to load {pth}: {exception}"

        pth = level_dir / "middle_decor.png"
        try:
            middle_decor = pygame.image.load(str(pth)).convert_alpha()
        except Exception as exception:
            return None, f"Failed to load {pth}: {exception}"

        pth = level_dir / "sky.png"
        try:
            sky = pygame.image.load(str(pth)).convert_alpha()
        except Exception as exception:
            return None, f"Failed to load {pth}: {exception}"

        levels.append(
            Level(
                bg_decor=bg_decor,
                foreground=foreground,
                ground=ground,
                middle_decor=middle_decor,
                sky=sky,
            )
        )

    runaways = []  # type: List[List[MaskedSprite]]
    for runaway_dir in sorted(
        pth for pth in (images_dir / "runaways").iterdir() if pth.is_dir()
    ):
        run = []  # type: List[MaskedSprite]
        for pth in sorted(runaway_dir.glob("*.png")):
            try:
                sprite = MaskedSprite(pygame.image.load(str(pth)).convert_alpha())
            except Exception as exception:
                return None, f"Failed to load {pth}: {exception}"

            run.append(sprite)

        runaways.append(run)

    chasers = []  # type: List[List[MaskedSprite]]
    for chaser_dir in sorted(
        pth for pth in (images_dir / "chasers").iterdir() if pth.is_dir()
    ):
        run = []
        for pth in sorted(chaser_dir.glob("*.png")):
            try:
                sprite = MaskedSprite(pygame.image.load(str(pth)).convert_alpha())
            except Exception as exception:
                return None, f"Failed to load {pth}: {exception}"

            run.append(sprite)

        chasers.append(run)

    pth = images_dir / "happy_end/ship.png"
    try:
        ship = pygame.image.load(str(pth)).convert_alpha()
    except Exception as exception:
        return None, f"Failed to load {pth}: {exception}"

    music_path = PACKAGE_DIR / "media/music/wellerman.mid"
    if not pth.exists():
        return None, f"File does not exist: {music_path}"

    return (
        Media(
            levels=levels,
            runaways=runaways,
            chasers=chasers,
            ship=ship,
            font=pygame.freetype.Font(
                str(PACKAGE_DIR / "media/fonts/freesansbold.ttf")
            ),
            music_path=music_path,
        ),
        None,
    )


class Actor:
    """Model an actor in the game."""

    run_sprites: Final[Sequence[MaskedSprite]]

    #: Top-left, in screen coordinates
    xy: Tuple[float, float]

    sprite_index: int

    max_width: Final[int]
    max_height: Final[int]

    def __init__(
        self, xy: Tuple[float, float], run_sprites: Sequence[MaskedSprite]
    ) -> None:
        """Initialize with the given values."""
        self.xy = xy

        self.sprite_index = 0
        self.run_sprites = run_sprites

        self.max_width = max(sprite.get_width() for sprite in run_sprites)
        self.max_height = max(sprite.get_height() for sprite in run_sprites)

    def determine_masked_sprite(self) -> MaskedSprite:
        """Determine the sprite at the current state."""
        return self.run_sprites[self.sprite_index]

    def calculate_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Calculate the bounding box given the current state.

        Return (xmin, ymin, xmax, ymax).
        """
        masked_sprite = self.determine_masked_sprite()

        return (
            self.xy[0],
            self.xy[1],
            self.xy[0] + masked_sprite.get_width(),
            self.xy[1] + masked_sprite.get_height(),
        )

    def collides_with(self, other: "Actor") -> bool:
        """Check if this actor collides with another actor."""
        bounding_box = self.calculate_bounding_box()
        other_bounding_box = other.calculate_bounding_box()

        mask = self.determine_masked_sprite().mask
        other_mask = other.determine_masked_sprite().mask

        if intersect(*bounding_box, *other_bounding_box):
            xmin = bounding_box[0]
            ymin = bounding_box[1]

            other_xmin = other_bounding_box[0]
            other_ymin = other_bounding_box[1]

            offset = (round(other_xmin - xmin), round(other_ymin - ymin))

            collision_xy = mask.overlap(other_mask, offset)

            if collision_xy is not None:
                return True

        return False


class Chaser(Actor):
    """Model the chaser who chases the player."""

    #: In seconds since epoch
    time_for_next_sprite: float

    velocity: float

    def __init__(
        self,
        xy: Tuple[float, float],
        run_sprites: Sequence[MaskedSprite],
        time_for_next_sprite: float,
    ) -> None:
        Actor.__init__(self, xy, run_sprites)
        self.time_for_next_sprite = time_for_next_sprite
        self.velocity = INITIAL_CHASER_VELOCITY


class Runaway(Actor):
    """Model the fugitive."""

    #: In seconds since epoch
    time_for_next_sprite: Optional[float]

    #: In pixels^2 / s
    acceleration: float

    #: In pixels / s
    velocity: float

    def __init__(
        self, xy: Tuple[float, float], run_sprites: Sequence[MaskedSprite]
    ) -> None:
        Actor.__init__(self, xy, run_sprites)
        self.time_for_next_sprite = None
        self.acceleration = 0.0
        self.velocity = 0.0


#: In pixels/s
INITIAL_CHASER_VELOCITY = 17.0
MAX_CHASER_VELOCITY = 40.0

#: In seconds
CHASER_FRAME_TIME_DELTA = 0.1

RUNAWAY_VELOCITY_ADDITION_AT_STEP = 6.0

RUNAWAY_MAX_VELOCITY = 45.0

RUNAWAY_FRICTION = 20.0

RUNAWAY_FRAME_TIME_DELTA = 0.1


class State:
    """Capture the global state of the game excluding the dialogues."""

    #: Timestamp when the game started, seconds since epoch
    game_start: float

    #: Current clock in the game, seconds since epoch
    now: float

    #: Set when the game finishes
    game_over: Optional[dancerunaway.events.GameOver]

    #: State of the runaway player
    runaway: Runaway

    #: State of the chaser non-player actor
    chaser: Chaser

    next_button = None  # type: Optional[dancerunaway.events.Button]

    level_index: int

    def __init__(
        self,
        game_start: float,
        runaway_sprites: List[MaskedSprite],
        chaser_sprites: List[MaskedSprite],
    ) -> None:
        """Initialize with the given values and the defaults."""
        initialize_state(self, game_start, runaway_sprites, chaser_sprites)


#: In pixels
ACTORS_Y = 330


def initialize_state(
    state: State,
    game_start: float,
    runaway_sprites: List[MaskedSprite],
    chaser_sprites: List[MaskedSprite],
) -> None:
    """Initialize the state to the start one."""
    state.game_start = game_start
    state.now = game_start
    state.game_over = None

    state.runaway = Runaway(
        xy=(3.0 * INITIAL_CHASER_VELOCITY, ACTORS_Y), run_sprites=runaway_sprites
    )

    state.chaser = Chaser(
        xy=(-chaser_sprites[0].get_width(), ACTORS_Y),
        run_sprites=chaser_sprites,
        time_for_next_sprite=state.now + 0.1,
    )

    state.next_button = None

    state.level_index = 0


@require(lambda xmin_a, xmax_a: xmin_a <= xmax_a)
@require(lambda ymin_a, ymax_a: ymin_a <= ymax_a)
@require(lambda xmin_b, xmax_b: xmin_b <= xmax_b)
@require(lambda ymin_b, ymax_b: ymin_b <= ymax_b)
def intersect(
    xmin_a: Union[int, float],
    ymin_a: Union[int, float],
    xmax_a: Union[int, float],
    ymax_a: Union[int, float],
    xmin_b: Union[int, float],
    ymin_b: Union[int, float],
    xmax_b: Union[int, float],
    ymax_b: Union[int, float],
) -> bool:
    """Return true if the two bounding boxes intersect."""
    return (xmin_a <= xmax_b and xmax_a >= xmin_b) and (
        ymin_a <= ymax_b and ymax_a >= ymin_b
    )


def handle_in_game(
    state: State, our_event_queue: List[dancerunaway.events.EventUnion], media: Media
) -> None:
    """Consume the first action in the queue during the game."""
    if len(our_event_queue) == 0:
        return

    event = our_event_queue.pop(0)

    now = pygame.time.get_ticks() / 1000

    if isinstance(event, dancerunaway.events.Tick):
        time_delta = now - state.now

        state.now = now

        # Update the chaser
        state.chaser.xy = (
            state.chaser.xy[0] + state.chaser.velocity * time_delta,
            state.chaser.xy[1],
        )

        if state.chaser.time_for_next_sprite < now:
            state.chaser.time_for_next_sprite = now + CHASER_FRAME_TIME_DELTA
            state.chaser.sprite_index = (state.chaser.sprite_index + 1) % len(
                state.chaser.run_sprites
            )

        # Check for collision
        if state.chaser.collides_with(state.runaway):
            our_event_queue.append(
                dancerunaway.events.GameOver(
                    kind=dancerunaway.events.GameOverKind.BUSTED
                )
            )
            return

        # Check for running away
        runaway_masked_xmin = (
            state.runaway.xy[0] + state.runaway.determine_masked_sprite().first_masked_x
        )
        if runaway_masked_xmin >= SCENE_WIDTH:
            if state.level_index == len(media.levels) - 1:
                our_event_queue.append(
                    dancerunaway.events.GameOver(
                        kind=dancerunaway.events.GameOverKind.HAPPY_END
                    )
                )
                return
            else:
                state.level_index += 1

                state.chaser.velocity = min(
                    MAX_CHASER_VELOCITY, 1.5 * state.chaser.velocity
                )

                # We put the runaway at the beginning of the next level ...
                state.runaway.xy = (0, ACTORS_Y)

                # ... and the chaser much more behind than where we put them in the
                # very first level. The offsets in the first level were necessary
                # so that the novice players have some time to understand what is going
                # on in the first level, but the offsets are not necessary anymore in
                # the next levels.
                state.chaser.xy = (
                    -state.chaser.determine_masked_sprite().get_width()
                    - 0.5 * state.chaser.velocity,
                    ACTORS_Y,
                )

        # Update the runaway
        state.runaway.velocity = max(
            0.0, state.runaway.velocity - RUNAWAY_FRICTION * time_delta
        )

        if state.runaway.velocity > 0:
            state.runaway.xy = (
                state.runaway.xy[0] + state.runaway.velocity * time_delta,
                state.runaway.xy[1],
            )

            if (
                state.runaway.time_for_next_sprite is None
                or state.runaway.time_for_next_sprite < now
            ):
                state.runaway.time_for_next_sprite = now + RUNAWAY_FRAME_TIME_DELTA
                state.runaway.sprite_index = (state.chaser.sprite_index + 1) % len(
                    state.chaser.run_sprites
                )

        else:
            state.runaway.time_for_next_sprite = None

    elif isinstance(event, dancerunaway.events.ButtonDown):
        should_make_step = False
        if state.next_button is None:
            if event.button is dancerunaway.events.Button.LEFT:
                should_make_step = True
                state.next_button = dancerunaway.events.Button.RIGHT
            elif event.button is dancerunaway.events.Button.RIGHT:
                should_make_step = True
                state.next_button = dancerunaway.events.Button.LEFT
            else:
                pass

        elif (
            state.next_button is dancerunaway.events.Button.RIGHT
            and event.button is dancerunaway.events.Button.RIGHT
        ):
            should_make_step = True
            state.next_button = dancerunaway.events.Button.LEFT

        elif (
            state.next_button is dancerunaway.events.Button.LEFT
            and event.button is dancerunaway.events.Button.LEFT
        ):
            should_make_step = True
            state.next_button = dancerunaway.events.Button.RIGHT

        else:
            pass

        if should_make_step:
            our_event_queue.append(dancerunaway.events.MakeStep())

    elif isinstance(event, dancerunaway.events.MakeStep):
        state.runaway.velocity = min(
            state.runaway.velocity + RUNAWAY_VELOCITY_ADDITION_AT_STEP,
            RUNAWAY_MAX_VELOCITY,
        )

    else:
        # Ignore the event
        pass


def handle(
    state: State,
    our_event_queue: List[dancerunaway.events.EventUnion],
    clock: pygame.time.Clock,
    media: Media,
) -> None:
    """Consume the first action in the queue."""
    if len(our_event_queue) == 0:
        return

    if isinstance(our_event_queue[0], dancerunaway.events.GameOver):
        event = our_event_queue[0]
        our_event_queue.pop(0)

        if state.game_over is None:
            state.game_over = event
            if state.game_over.kind is dancerunaway.events.GameOverKind.HAPPY_END:
                # Left for the future version: play victory music
                pass

            elif state.game_over.kind is dancerunaway.events.GameOverKind.BUSTED:
                # Left for the future version: play sad music
                pass

            else:
                assert_never(state.game_over)
    else:
        if state.game_over is None:
            handle_in_game(state, our_event_queue, media)
        else:
            # Just consume the event, but leave the game state frozen at the game over.
            our_event_queue.pop(0)


def render_game_over(state: State, media: Media) -> pygame.surface.Surface:
    """Render the "game over" dialogue as a scene."""
    scene = pygame.surface.Surface((SCENE_WIDTH, SCENE_HEIGHT))
    scene.fill((0, 0, 0))

    assert state.game_over is not None

    if state.game_over.kind is dancerunaway.events.GameOverKind.HAPPY_END:
        media.font.render_to(scene, (20, 20), "You made it!", (255, 255, 255), size=16)

        runaway_left = pygame.transform.flip(
            state.runaway.run_sprites[0].sprite, True, False
        )
        scene.blit(runaway_left, (280, 270))
        scene.blit(media.ship, (300, 100))

        scene.blit(state.chaser.run_sprites[0].sprite, (10, ACTORS_Y))

    elif state.game_over.kind is dancerunaway.events.GameOverKind.BUSTED:
        media.font.render_to(
            scene, (20, 20), "You have been caught :(", (255, 255, 255), size=16
        )

        scene.blit(state.runaway.determine_masked_sprite().sprite, state.runaway.xy)

        scene.blit(state.chaser.determine_masked_sprite().sprite, state.chaser.xy)
    else:
        assert_never(state.game_over.kind)

    media.font.render_to(
        scene,
        (20, SCENE_HEIGHT - 20),
        'Press "q" to quit and "r" to restart',
        (255, 255, 255),
        size=16,
    )

    return scene


def render_quit(media: Media) -> pygame.surface.Surface:
    """Render the "Quitting..." dialogue as a scene."""
    scene = pygame.surface.Surface((SCENE_WIDTH, SCENE_HEIGHT))
    scene.fill((0, 0, 0))

    media.font.render_to(scene, (20, 20), "Quitting...", (255, 255, 255), size=32)

    return scene


def render_game(state: State, media: Media) -> pygame.surface.Surface:
    """Render the game scene."""
    level = media.levels[state.level_index]
    scene = level.sky.copy()
    scene.blit(level.middle_decor, (0, 0))
    scene.blit(level.foreground, (0, 0))

    scene.blit(state.runaway.determine_masked_sprite().sprite, state.runaway.xy)

    scene.blit(state.chaser.determine_masked_sprite().sprite, state.chaser.xy)

    scene.blit(level.ground, (0, 0))

    media.font.render_to(
        scene, (10, 490), 'Press "q" to quit and "r" to restart', (0, 0, 0), size=12
    )

    return scene


def resize_scene_to_surface_and_blit(
    scene: pygame.surface.Surface, surface: pygame.surface.Surface
) -> None:
    """Draw the scene on surface resizing it to maximum at constant aspect ratio."""
    surface.fill((0, 0, 0))

    surface_aspect_ratio = fractions.Fraction(surface.get_width(), surface.get_height())
    scene_aspect_ratio = fractions.Fraction(scene.get_width(), scene.get_height())

    if scene_aspect_ratio < surface_aspect_ratio:
        new_scene_height = surface.get_height()
        new_scene_width = scene.get_width() * (new_scene_height / scene.get_height())

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        margin = int((surface.get_width() - scene.get_width()) / 2)

        surface.blit(scene, (margin, 0))

    elif scene_aspect_ratio == surface_aspect_ratio:
        new_scene_width = surface.get_width()
        new_scene_height = scene.get_height()

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        surface.blit(scene, (0, 0))
    else:
        new_scene_width = surface.get_width()
        new_scene_height = int(
            scene.get_height() * (new_scene_width / scene.get_width())
        )

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        margin = int((surface.get_height() - scene.get_height()) / 2)

        surface.blit(scene, (0, margin))


# fmt: off
@ensure(
    lambda result:
    (result[0] is not None and result[1] is not None and not result[2])
    ^
    (result[0] is None and result[1] is None and result[2])
)
# fmt: on
def select_actors(
    surface: pygame.surface.Surface, media: Media
) -> Tuple[Optional[List[MaskedSprite]], Optional[List[MaskedSprite]], bool]:
    """Handle the dialogue where the player chooses the runaway and the chaser."""
    runaway_sprites = None  # type: Optional[List[MaskedSprite]]
    chaser_sprites = None  # type: Optional[List[MaskedSprite]]
    should_quit = False

    key_to_runaway_i = dict()  # type: MutableMapping[int, int]
    runaway_chars = []  # type: List[str]
    key_to_chaser_i = dict()  # type: MutableMapping[int, int]
    chaser_chars = []  # type: List[str]

    actor_i = 0

    max_actors = ord("q") - ord("a")

    for runaway_i in range(len(media.runaways)):
        assert actor_i < max_actors
        key_to_runaway_i[pygame.K_a + actor_i] = runaway_i
        runaway_chars.append(chr(ord("a") + actor_i))

        actor_i += 1

    selected_runaway_i = 0
    selected_chaser_i = 0

    for chaser_i in range(len(media.chasers)):
        assert actor_i < max_actors
        key_to_chaser_i[pygame.K_a + actor_i] = chaser_i
        chaser_chars.append(chr(ord("a") + actor_i))

        actor_i += 1

    should_quit = False
    should_start = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                should_quit = True
                break

            elif event.type == pygame.KEYDOWN:
                if event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_q,
                ):
                    should_quit = True
                    break

                elif event.key in key_to_runaway_i:
                    selected_runaway_i = key_to_runaway_i[event.key]

                elif event.key in key_to_chaser_i:
                    selected_chaser_i = key_to_chaser_i[event.key]

                elif event.key == pygame.K_s:
                    should_start = True
                    break

                else:
                    pass

            else:
                pass

        assert (not should_quit and not should_start) or (
            should_quit ^ should_start
        ), f"{should_quit=}, {should_start=}"

        if should_quit or should_start:
            break

        scene = pygame.surface.Surface((SCENE_WIDTH, SCENE_HEIGHT))
        scene.fill((0, 0, 0))

        media.font.render_to(
            scene,
            (20, 20),
            "Please select the runaway and the chaser:",
            (255, 255, 255),
            size=16,
        )

        offset_x = 20
        offset_y = 60
        for runaway_i, runaway_sprites in enumerate(media.runaways):
            sprite = runaway_sprites[runaway_i].sprite
            scene.blit(sprite, (offset_x, offset_y))

            media.font.render_to(
                scene,
                (
                    offset_x + round(sprite.get_width() / 2),
                    offset_y + sprite.get_height() + 5,
                ),
                runaway_chars[runaway_i],
                (255, 255, 255),
                size=32,
            )

            if runaway_i == selected_runaway_i:
                pygame.draw.rect(
                    scene,
                    (255, 255, 255),
                    (offset_x, offset_y, sprite.get_width(), sprite.get_height()),
                    3,
                )

            offset_x += sprite.get_width() + 10

        offset_x = 20
        offset_y = 60 + runaway_sprites[0].sprite.get_height() + 50

        for chaser_i, chaser_sprites in enumerate(media.chasers):
            sprite = chaser_sprites[chaser_i].sprite
            scene.blit(sprite, (offset_x, offset_y))

            media.font.render_to(
                scene,
                (
                    offset_x + round(sprite.get_width() / 2),
                    offset_y + sprite.get_height() + 5,
                ),
                chaser_chars[chaser_i],
                (255, 255, 255),
                size=32,
            )

            if chaser_i == selected_chaser_i:
                pygame.draw.rect(
                    scene,
                    (255, 255, 255),
                    (offset_x, offset_y, sprite.get_width(), sprite.get_height()),
                    3,
                )

            offset_x += sprite.get_width() + 10

        media.font.render_to(
            scene,
            (20, SCENE_HEIGHT - 20),
            'Press "s" to start and "q" to quit',
            (255, 255, 255),
            size=16,
        )

        resize_scene_to_surface_and_blit(scene, surface)
        pygame.display.flip()

    if not should_quit:
        runaway_sprites = media.runaways[selected_runaway_i]
        chaser_sprites = media.chasers[selected_chaser_i]
        return runaway_sprites, chaser_sprites, False

    return None, None, True


def main(prog: str) -> int:
    """
    Execute the main routine.

    :param prog: name of the program to be displayed in the help
    :return: exit code
    """
    pygame.joystick.init()
    joysticks = [
        pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
    ]

    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument(
        "--window", help="If set, run the game in a window", action="store_true"
    )

    parser.add_argument(
        "--version", help="Show the current version and exit", action="store_true"
    )

    parser.add_argument(
        "--list_joysticks", help="List joystick GUIDs and exit", action="store_true"
    )
    if len(joysticks) >= 1:
        parser.add_argument(
            "--joystick",
            help="Joystick to use for the game",
            choices=[joystick.get_guid() for joystick in joysticks],
            default=joysticks[0].get_guid(),
        )

    # The module ``argparse`` is not flexible enough to understand special options such
    # as ``--version`` so we manually hard-wire.
    if "--version" in sys.argv and "--help" not in sys.argv:
        print(dancerunaway.__version__)
        return 0

    if "--list_joysticks" in sys.argv and "--help" not in sys.argv:
        for joystick in joysticks:
            print(f"Joystick {joystick.get_name()}, GUID: {joystick.get_guid()}")
        return 0

    args = parser.parse_args()
    run_in_window = bool(args.window is not None and args.window)

    # noinspection PyUnusedLocal
    active_joystick = None  # type: Any

    DEBUG = False

    if not DEBUG:
        if len(joysticks) == 0:
            print(
                f"There are no joysticks plugged in. "
                f"{prog.capitalize()} requires a joystick.",
                file=sys.stderr,
            )
            return 1

        else:
            active_joystick = next(
                joystick
                for joystick in joysticks
                if joystick.get_guid() == args.joystick
            )

        assert active_joystick is not None
        print(
            f"Using the joystick: {active_joystick.get_name()} {active_joystick.get_guid()}"
        )

    # NOTE (mristin, 2023-03-26):
    # We have to think a bit better about how to deal with keyboard and joystick input.
    # For rapid development, we simply map the buttons of our concrete dance mat to
    # button numbers.
    button_map = {
        6: dancerunaway.events.Button.CROSS,
        2: dancerunaway.events.Button.UP,
        7: dancerunaway.events.Button.CIRCLE,
        3: dancerunaway.events.Button.RIGHT,
        5: dancerunaway.events.Button.SQUARE,
        1: dancerunaway.events.Button.DOWN,
        4: dancerunaway.events.Button.TRIANGLE,
        0: dancerunaway.events.Button.LEFT,
    }

    pygame.init()
    pygame.mixer.pre_init()
    pygame.mixer.init()

    pygame.display.set_caption("dance-runaway-desktop")

    if not run_in_window:
        surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        surface = pygame.display.set_mode((640, 480))

    media, error = load_media()
    if error is not None:
        print(
            f"Failed to load the media: {error}",
            file=sys.stderr,
        )
        return 1

    assert media is not None

    clock = pygame.time.Clock()

    should_quit = False
    while not should_quit:
        # fmt: off
        runaway_sprites, chaser_sprites, should_quit = (
            select_actors(
                surface,
                media
            )
        )
        # fmt: on

        if should_quit:
            break

        assert runaway_sprites is not None
        assert chaser_sprites is not None

        now = pygame.time.get_ticks() / 1000

        state = State(
            game_start=now,
            runaway_sprites=runaway_sprites,
            chaser_sprites=chaser_sprites,
        )

        our_event_queue = []  # type: List[dancerunaway.events.EventUnion]

        # Reuse the tick object so that we don't have to create it every time
        tick_event = dancerunaway.events.Tick()

        pygame.mixer.music.load(media.music_path)
        pygame.mixer.music.play()

        while not should_quit:
            old_state_game_over = state.game_over

            should_restart = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    should_quit = True
                    break

                elif (
                    event.type == pygame.JOYBUTTONDOWN
                    and joysticks[event.instance_id] is active_joystick
                ):
                    # NOTE (mristin, 2023-03-26):
                    # Map joystick buttons to our canonical buttons;
                    # This is necessary if we ever want to support other dance mats.
                    our_button = button_map.get(event.button, None)
                    if our_button is not None:
                        our_event_queue.append(
                            dancerunaway.events.ButtonDown(our_button)
                        )

                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_q,
                ):
                    should_quit = True
                    break

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # Leave the inner-game loop and start the game totally from anew
                    should_restart = True
                    break

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                    if DEBUG:
                        our_event_queue.append(
                            dancerunaway.events.ButtonDown(
                                button=dancerunaway.events.Button.LEFT
                            )
                        )

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                    if DEBUG:
                        our_event_queue.append(
                            dancerunaway.events.ButtonDown(
                                button=dancerunaway.events.Button.RIGHT
                            )
                        )

                else:
                    # Ignore the event that we do not handle
                    pass

            if should_quit or should_restart:
                pygame.mixer.music.stop()
                break

            our_event_queue.append(tick_event)

            while len(our_event_queue) > 0:
                handle(state, our_event_queue, clock, media)

            scene = None  # type: Optional[pygame.surface.Surface]

            if old_state_game_over is None and state.game_over is not None:
                scene = render_game_over(state, media)

            elif old_state_game_over is not None and state.game_over is not None:
                # Do not render again as the game over screen does not change.
                scene = None

            elif state.game_over is None:
                scene = render_game(state, media)

            else:
                raise AssertionError("Unhandled case")

            if scene is not None:
                resize_scene_to_surface_and_blit(scene, surface)
                pygame.display.flip()

            # Enforce 30 frames per second
            clock.tick(30)

    scene = render_quit(media)
    resize_scene_to_surface_and_blit(scene, surface)
    pygame.display.flip()

    print("Quitting the game...")
    tic = time.time()
    pygame.joystick.quit()
    pygame.quit()
    print(f"Quit the game after: {time.time() - tic:.2f} seconds")

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="dance-runaway-desktop")


if __name__ == "__main__":
    sys.exit(main(prog="dance-runaway-desktop"))
