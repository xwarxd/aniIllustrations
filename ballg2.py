import pygame
import math
import random
import os
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip

# Constants
WIDTH, HEIGHT = 1080, 1920  # Dimensions of the simulation window (vertical orientation)
BLACK, WHITE = (0, 0, 0), (255, 255, 255)  # Color definitions for black and white
BOUNDARY_RADIUS = 528  # Radius of the circular boundary within which balls move
BOUNDARY_CENTER = (WIDTH // 2, HEIGHT // 2)  # Center point of the circular boundary
BOUNDARY_LIFETIME, COLOR_CHANGE_INTERVAL = 5, 0.05  # Duration of boundary visibility and color change frequency

class Ball:
    """
    Represents a ball in the simulation.
    
    This class encapsulates all properties and behaviors of a ball, including its
    position, size, color, movement, and collision detection.
    """
    
    def __init__(self, x, y, radius=None, speed=4.8, is_on_top=False):
        """
        Initialize a new Ball instance.
        
        Args:
            x (float): Initial x-coordinate of the ball's center.
            y (float): Initial y-coordinate of the ball's center.
            radius (float, optional): Radius of the ball. If None, a random radius between 4.8 and 24 is assigned.
            speed (float): Initial speed of the ball.
            is_on_top (bool): Flag indicating if the ball should be rendered on top of others.
        """
        self.x, self.y = x, y
        self.radius = radius if radius is not None else random.uniform(4.8, 24)
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))  # Random RGB color
        self.speed = speed
        self.angle = random.random() * math.pi * 2  # Random initial movement angle
        self.is_on_top = is_on_top
        self.active = True  # Flag to determine if the ball is within the screen boundaries

    def move(self):
        """
        Update the ball's position based on its current angle and speed.
        
        This method also checks if the ball is still within the screen boundaries
        and updates the 'active' flag accordingly.
        """
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.active = 0 < self.x < WIDTH and 0 < self.y < HEIGHT

    def draw(self, screen):
        """
        Draw the ball on the given Pygame screen.
        
        Args:
            screen (pygame.Surface): The surface on which to draw the ball.
        """
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))

    def check_boundary_collision(self, boundary_active):
        """
        Check and handle collision with the circular boundary.
        
        Args:
            boundary_active (bool): Flag indicating if the boundary is currently active.
        
        Returns:
            bool: True if a collision occurred, False otherwise.
        """
        if not boundary_active:
            return False
        dx, dy = self.x - BOUNDARY_CENTER[0], self.y - BOUNDARY_CENTER[1]
        distance = math.hypot(dx, dy)
        if distance + self.radius > BOUNDARY_RADIUS:
            # Collision detected, adjust position and randomize new direction
            normal_angle = math.atan2(dy, dx)
            self.x = BOUNDARY_CENTER[0] + (BOUNDARY_RADIUS - self.radius) * math.cos(normal_angle)
            self.y = BOUNDARY_CENTER[1] + (BOUNDARY_RADIUS - self.radius) * math.sin(normal_angle)
            self.angle = random.random() * math.pi * 2
            return True
        return False

    def check_ball_collision(self, other):
        """
        Check and handle collision with another ball.
        
        Args:
            other (Ball): The other ball to check collision against.
        
        Returns:
            bool: True if a collision occurred, False otherwise.
        """
        if not self.active or not other.active:
            return False
        dx, dy = self.x - other.x, self.y - other.y
        distance = math.hypot(dx, dy)
        if distance < self.radius + other.radius or (self.is_on_top and other.is_on_top):
            # Collision detected, randomize new directions for both balls
            self.angle = random.random() * math.pi * 2
            other.angle = random.random() * math.pi * 2
            if not self.is_on_top and not other.is_on_top:
                # Adjust positions to prevent overlap
                angle = math.atan2(dy, dx)
                overlap = self.radius + other.radius - distance
                self.x += overlap * math.cos(angle) / 2
                self.y += overlap * math.sin(angle) / 2
                other.x -= overlap * math.cos(angle) / 2
                other.y -= overlap * math.sin(angle) / 2
            self.is_on_top = other.is_on_top = False
            return True
        return False

    def set_speed(self, new_speed):
        """
        Set a new speed for the ball.
        
        Args:
            new_speed (float): The new speed value to set.
        """
        self.speed = new_speed

def flow_color(start_color, end_color, progress):
    """
    Interpolate between two colors based on a progress value.
    
    Args:
        start_color (tuple): The starting RGB color.
        end_color (tuple): The ending RGB color.
        progress (float): A value between 0 and 1 indicating the interpolation progress.
    
    Returns:
        tuple: The interpolated RGB color.
    """
    return tuple(int(start + (end - start) * progress) for start, end in zip(start_color, end_color))

def init_pygame():
    """
    Initialize Pygame and create the game window.
    
    Returns:
        pygame.Surface: The main screen surface for drawing.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ball Simulation (Vertical)")
    return screen

def init_simulation():
    """
    Initialize the simulation by creating a list of starting balls.
    
    Returns:
        list: A list of Ball objects positioned randomly within the boundary.
    """
    balls = [Ball(BOUNDARY_CENTER[0] + random.uniform(-BOUNDARY_RADIUS, BOUNDARY_RADIUS),
                  BOUNDARY_CENTER[1] + random.uniform(-BOUNDARY_RADIUS, BOUNDARY_RADIUS)) for _ in range(2)]
    return balls

def update_boundary_color(current_time, last_color_change_time, current_color, target_color):
    """
    Update the boundary color by interpolating between current and target colors.
    
    Args:
        current_time (float): The current simulation time.
        last_color_change_time (float): The time when the last color change started.
        current_color (tuple): The current RGB color of the boundary.
        target_color (tuple): The target RGB color to transition towards.
    
    Returns:
        tuple: Updated new_color, target_color, and last_color_change_time.
    """
    color_transition_duration = 2.0
    color_progress = min(1, (current_time - last_color_change_time) / color_transition_duration)
    new_color = flow_color(current_color, target_color, color_progress)
    
    if color_progress >= 1:
        last_color_change_time = current_time
        current_color = target_color
        target_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    return new_color, target_color, last_color_change_time

def handle_ball_collisions(balls):
    """
    Handle collisions between all active balls in the simulation.
    
    Args:
        balls (list): List of all Ball objects in the simulation.
    """
    active_balls = [ball for ball in balls if ball.active]
    for i, ball in enumerate(active_balls):
        for other_ball in active_balls[i+1:]:
            ball.check_ball_collision(other_ball)

def handle_boundary_collision(balls, boundary_active):
    """
    Handle collisions between balls and the circular boundary.
    
    Args:
        balls (list): List of all Ball objects in the simulation.
        boundary_active (bool): Flag indicating if the boundary is currently active.
    
    Returns:
        bool: True if any new boundary collision occurred, False otherwise.
    """
    new_boundary_collision = False
    for ball in balls:
        if boundary_active and ball.check_boundary_collision(boundary_active):
            new_boundary_collision = True
    return new_boundary_collision

def spawn_new_ball(balls):
    """
    Spawn a new ball at the center of the boundary and set appropriate flags.
    
    Args:
        balls (list): List of all Ball objects in the simulation.
    """
    new_ball = Ball(BOUNDARY_CENTER[0], BOUNDARY_CENTER[1], is_on_top=True)
    balls.append(new_ball)
    for ball in balls:
        if math.hypot(ball.x - BOUNDARY_CENTER[0], ball.y - BOUNDARY_CENTER[1]) < new_ball.radius * 2:
            ball.is_on_top = True

def update_ball_speeds(balls, boundary_active, speeds_changed):
    """
    Update the speed of all balls based on the boundary state.
    
    Args:
        balls (list): List of all Ball objects in the simulation.
        boundary_active (bool): Flag indicating if the boundary is currently active.
        speeds_changed (bool): Flag indicating if speeds have already been changed.
    
    Returns:
        bool: Updated speeds_changed flag.
    """
    if not boundary_active and not speeds_changed:
        for ball in balls:
            ball.set_speed(19.2)
        return True
    return speeds_changed

def render_text(screen, font, active_balls_count):
    """
    Render text information on the screen.
    
    Args:
        screen (pygame.Surface): The surface on which to render the text.
        font (pygame.font.Font): The font to use for rendering text.
        active_balls_count (int): The current count of active balls.
    """
    active_balls_text = font.render(f"Active Balls: {active_balls_count}", True, WHITE)
    screen.blit(active_balls_text, (24, 24))
    explanation_text = font.render("Ball hitting the circle spawns a new one", True, WHITE)
    screen.blit(explanation_text, (24, 96))

def save_frame(screen, frame):
    """
    Save the current screen state as an image file.
    
    Args:
        screen (pygame.Surface): The surface to save as an image.
        frame (int): The current frame number (used for filename).
    """
    pygame.image.save(screen, f"frames/frame_{frame:04d}.png")

def main_game_loop():
    """
    The main game loop that runs the simulation and generates video frames.
    
    This function initializes the simulation, updates the state of all objects,
    renders each frame, and collects data for sound events.
    
    Returns:
        tuple: Total number of frames rendered and a list of sound events.
    """
    screen = init_pygame()
    balls = init_simulation()
    font = pygame.font.Font(None, 70)

    boundary_start_time = last_color_change_time = 0
    boundary_active = True
    speeds_changed = False
    current_boundary_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    target_boundary_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    frame = 0
    sound_events = []
    last_sound_end = 0
    sound_offset = 0
    
    extra_frames = 5 * 60  # 5 seconds of extra frames at 60 FPS
    all_balls_gone = False
    extra_frame_counter = 0

    while True:
        screen.fill(BLACK)

        current_time = frame / 60
        boundary_active = current_time - boundary_start_time <= BOUNDARY_LIFETIME

        current_boundary_color, target_boundary_color, last_color_change_time = update_boundary_color(
            current_time, last_color_change_time, current_boundary_color, target_boundary_color)

        if boundary_active:
            pygame.draw.circle(screen, current_boundary_color, BOUNDARY_CENTER, BOUNDARY_RADIUS, 6)

        new_boundary_collision = handle_boundary_collision(balls, boundary_active)
        speeds_changed = update_ball_speeds(balls, boundary_active, speeds_changed)
        handle_ball_collisions(balls)

        for ball in balls:
            ball.move()
            ball.draw(screen)

        if new_boundary_collision:
            spawn_new_ball(balls)
            sound_start = max(current_time, last_sound_end)
            sound_duration = 0.1
            sound_events.append((sound_start, sound_start + sound_duration, sound_offset))
            last_sound_end = sound_start + sound_duration
            sound_offset += sound_duration

        active_balls = [ball for ball in balls if ball.active]
        render_text(screen, font, len(active_balls))
        save_frame(screen, frame)

        if frame % 60 == 0:
            print(f"Rendered frame {frame}")

        frame += 1

        if not boundary_active and len(active_balls) == 0:
            if not all_balls_gone:
                all_balls_gone = True
                print("All balls are gone. Rendering 5 more seconds...")
            extra_frame_counter += 1

        if all_balls_gone and extra_frame_counter >= extra_frames:
            break

    return frame, sound_events

def create_video(total_frames, sound_events, fps, output_filename):
    """
    Create a video file from the rendered frames and sound events.
    
    Args:
        total_frames (int): Total number of frames in the video.
        sound_events (list): List of sound events to be added to the video.
        fps (int): Frames per second for the output video.
        output_filename (str): Name of the output video file.
    """
    clip = ImageSequenceClip("frames", fps=fps)
    video_duration = total_frames / fps
    audio = AudioFileClip("sound.wav")
    
    audio_clips = []
    for start, end, offset in sound_events:
        if start < video_duration:
            clip_end = min(end, video_duration)
            clip_duration = clip_end - start
            if clip_duration > 0:
                audio_clip = audio.subclip(offset, offset + clip_duration).set_start(start)
                audio_clips.append(audio_clip)
    
    if audio_clips:
        final_audio = CompositeAudioClip(audio_clips)
        final_clip = clip.set_audio(final_audio)
    else:
        final_clip = clip
    
    final_clip.write_videofile(output_filename, fps=fps)
    # Write the final video file to disk, including both video and audio

def cleanup_frames():
    """
    Remove all temporary frame images and the frames directory.
    
    This function is called after the video creation process to clean up
    the individual frame images that were used to create the video.
    """
    for file in os.listdir("frames"):
        os.remove(os.path.join("frames", file))
    os.rmdir("frames")

if __name__ == "__main__":
    fps = 60  # Set the frames per second for the simulation and output video
    random.seed(12)  # Set a fixed random seed for reproducibility

    # Create the frames directory if it doesn't exist
    if not os.path.exists("frames"):
        os.makedirs("frames")

    print("Simulating and rendering frames...")
    total_frames, sound_events = main_game_loop()
    # Run the main simulation loop, which generates frame images and collects sound event data

    print("Creating video...")
    create_video(total_frames, sound_events, fps, "vertical_ball_simulation.mp4")
    # Combine the rendered frames and sound events into a single video file

    print("Video creation complete!")

    cleanup_frames()
    # Remove the temporary frame images and directory

pygame.quit()
# Properly close the Pygame library

# Additional notes on the overall structure and flow of the program:

# 1. The program starts by importing necessary libraries and defining constants.

# 2. The Ball class is defined, encapsulating all properties and behaviors of the balls in the simulation.

# 3. Several utility functions are defined to handle various aspects of the simulation:
#    - flow_color: for smooth color transitions
#    - init_pygame: to set up the Pygame environment
#    - init_simulation: to create the initial set of balls
#    - update_boundary_color: to manage the changing boundary color
#    - handle_ball_collisions: to detect and respond to collisions between balls
#    - handle_boundary_collision: to manage collisions with the circular boundary
#    - spawn_new_ball: to add new balls to the simulation
#    - update_ball_speeds: to adjust ball speeds based on simulation state
#    - render_text: to display information on the screen
#    - save_frame: to save each frame as an image

# 4. The main_game_loop function is the core of the simulation:
#    - It initializes the simulation state
#    - Runs a loop that updates the state of all objects for each frame
#    - Renders each frame and saves it as an image
#    - Collects data on sound events for later audio generation
#    - Continues until all balls are gone and extra frames have been rendered

# 5. The create_video function takes the rendered frames and sound event data:
#    - It uses moviepy to create a video from the frame images
#    - Adds audio based on the collected sound events
#    - Outputs the final video file

# 6. The cleanup_frames function removes all temporary files after video creation

# 7. The main block of the script:
#    - Sets up initial conditions (fps, random seed)
#    - Runs the main simulation loop
#    - Creates the video from the simulation results
#    - Cleans up temporary files

# This structure allows for a clear separation of concerns, with each function
# handling a specific aspect of the simulation or video creation process. The use
# of a class for the balls encapsulates their behavior, making the code more
# organized and easier to maintain or extend.