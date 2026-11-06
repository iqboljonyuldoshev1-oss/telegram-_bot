"""
Video Maker Engine - Professional slideshow & transition video generator from photos.
No AI hallucinations or weird AI morphing: 100% real photo quality with cinematic transitions.
"""

import os
import cv2
import numpy as np
import subprocess
import imageio_ffmpeg
from PIL import Image, ImageFilter


def get_ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def create_canvas_frame(image_path: str, target_width: int, target_height: int) -> np.ndarray:
    """
    Takes an image path and creates a target_width x target_height frame.
    If the image aspect ratio doesn't match target, the background is filled
    with a heavily blurred and darkened version of the photo, and the sharp
    original photo is centered in the foreground.
    """
    img = cv2.imread(image_path)
    if img is None:
        # Fallback with PIL in case OpenCV fails on some color spaces/formats
        pil_img = Image.open(image_path).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    orig_h, orig_w = img.shape[:2]
    target_aspect = target_width / target_height
    orig_aspect = orig_w / orig_h

    # 1. Create blurred background covering entire target canvas
    if orig_aspect > target_aspect:
        # Image is wider: scale height to target_height, crop width
        new_h = target_height
        new_w = int(orig_w * (target_height / orig_h))
    else:
        # Image is taller: scale width to target_width, crop height
        new_w = target_width
        new_h = int(orig_h * (target_width / orig_w))

    resized_bg = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    # Center crop
    start_x = max(0, (new_w - target_width) // 2)
    start_y = max(0, (new_h - target_height) // 2)
    bg_cropped = resized_bg[start_y:start_y + target_height, start_x:start_x + target_width]
    
    # Ensure exact dimensions
    if bg_cropped.shape[0] != target_height or bg_cropped.shape[1] != target_width:
        bg_cropped = cv2.resize(bg_cropped, (target_width, target_height))

    # Apply heavy blur and darken
    blur_ksize = max(51, (min(target_width, target_height) // 15) | 1)
    blurred_bg = cv2.GaussianBlur(bg_cropped, (blur_ksize, blur_ksize), 0)
    blurred_bg = (blurred_bg.astype(np.float32) * 0.6).astype(np.uint8)

    # 2. Fit foreground image inside canvas
    scale = min(target_width / orig_w, target_height / orig_h)
    fit_w = int(orig_w * scale)
    fit_h = int(orig_h * scale)
    fit_fg = cv2.resize(img, (fit_w, fit_h), interpolation=cv2.INTER_CUBIC)

    # Place foreground onto blurred background
    x_offset = (target_width - fit_w) // 2
    y_offset = (target_height - fit_h) // 2

    canvas = blurred_bg.copy()
    canvas[y_offset:y_offset + fit_h, x_offset:x_offset + fit_w] = fit_fg

    return canvas


def render_slideshow(
    image_paths: list[str],
    output_path: str,
    audio_path: str = None,
    aspect_ratio: str = "9:16",
    style: str = "ken_burns",
    slide_duration: float = 3.0,
    transition_duration: float = 0.6,
    fps: int = 30
) -> str:
    """
    Renders a video from images with specified style and parameters.
    Styles:
      - 'ken_burns': Cinematic slow zoom in / out with crossfade transitions
      - 'crossfade': Elegant smooth dissolve between pictures
      - 'slide_left': Dynamic left slide transition
      - 'zoom_flash': Rhythmic cut with zoom punch & light flash
    """
    if not image_paths:
        raise ValueError("Kamida 1 ta rasm kerak!")

    # Resolution mapping
    resolutions = {
        "9:16": (720, 1280),   # Vertical (Stories, Reels, Shorts)
        "16:9": (1280, 720),   # Landscape (YouTube, TV)
        "1:1": (1080, 1080),   # Square (Instagram)
    }
    width, height = resolutions.get(aspect_ratio, (720, 1280))

    # Ensure even dimensions for H.264
    width = (width // 2) * 2
    height = (height // 2) * 2

    # Pre-render base frames
    base_frames = [create_canvas_frame(p, width, height) for p in image_paths]
    num_images = len(base_frames)

    total_slide_frames = int(slide_duration * fps)
    trans_frames = int(transition_duration * fps) if num_images > 1 else 0
    hold_frames = max(1, total_slide_frames - trans_frames)

    ffmpeg_exe = get_ffmpeg_path()
    temp_video = output_path if not audio_path else output_path + ".temp.mp4"

    cmd = [
        ffmpeg_exe, "-y",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "faster",
        "-crf", "20",
        temp_video
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def write_frame(f: np.ndarray):
        proc.stdin.write(f.tobytes())

    try:
        for idx in range(num_images):
            cur_img = base_frames[idx]
            next_img = base_frames[(idx + 1) % num_images] if num_images > 1 else cur_img
            is_last = (idx == num_images - 1)

            # Style-specific generation
            if style == "ken_burns":
                # Zoom in on even, zoom out on odd
                zoom_in = (idx % 2 == 0)
                
                # Pre-calculate zoomed frames
                for f_idx in range(hold_frames):
                    progress = f_idx / max(1, total_slide_frames)
                    scale = 1.0 + (0.12 * progress if zoom_in else 0.12 * (1.0 - progress))
                    
                    # Crop center and resize to width x height
                    cw, ch = int(width / scale), int(height / scale)
                    cx1 = (width - cw) // 2
                    cy1 = (height - ch) // 2
                    cropped = cur_img[cy1:cy1 + ch, cx1:cx1 + cw]
                    frame = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)
                    write_frame(frame)

                # Transition frames
                if not is_last:
                    for t_idx in range(trans_frames):
                        progress = (hold_frames + t_idx) / max(1, total_slide_frames)
                        scale = 1.0 + (0.12 * progress if zoom_in else 0.12 * (1.0 - progress))
                        cw, ch = int(width / scale), int(height / scale)
                        cx1 = (width - cw) // 2
                        cy1 = (height - ch) // 2
                        cropped = cur_img[cy1:cy1 + ch, cx1:cx1 + cw]
                        f1 = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)

                        # Starting scale for next image
                        next_zoom_in = ((idx + 1) % 2 == 0)
                        n_scale = 1.0 if next_zoom_in else 1.12
                        ncw, nch = int(width / n_scale), int(height / n_scale)
                        ncx1 = (width - ncw) // 2
                        ncy1 = (height - nch) // 2
                        ncropped = next_img[ncy1:ncy1 + nch, ncx1:ncx1 + ncw]
                        f2 = cv2.resize(ncropped, (width, height), interpolation=cv2.INTER_LINEAR)

                        alpha = t_idx / float(trans_frames)
                        blended = cv2.addWeighted(f1, 1.0 - alpha, f2, alpha, 0)
                        write_frame(blended)

            elif style == "slide_left":
                # Static hold
                for _ in range(hold_frames):
                    write_frame(cur_img)

                # Slide left transition
                if not is_last:
                    for t_idx in range(trans_frames):
                        alpha = t_idx / float(trans_frames)
                        # Smoothstep easing
                        t = alpha * alpha * (3 - 2 * alpha)
                        shift = int(width * t)

                        combined = np.zeros_like(cur_img)
                        combined[:, :width - shift] = cur_img[:, shift:]
                        combined[:, width - shift:] = next_img[:, :shift]
                        write_frame(combined)

            elif style == "zoom_flash":
                # Hold with slight pulse
                flash_len = min(6, trans_frames // 2)
                for f_idx in range(hold_frames):
                    write_frame(cur_img)

                if not is_last:
                    # Flash & Quick Zoom
                    for t_idx in range(trans_frames):
                        alpha = t_idx / float(trans_frames)
                        if t_idx < flash_len:
                            # Brightness flash
                            brightness = int(120 * (1.0 - t_idx / flash_len))
                            flash_frame = cv2.add(cur_img, np.full_like(cur_img, brightness))
                            write_frame(flash_frame)
                        else:
                            # Quick fade into next image
                            sub_alpha = (t_idx - flash_len) / float(trans_frames - flash_len)
                            blended = cv2.addWeighted(cur_img, 1.0 - sub_alpha, next_img, sub_alpha, 0)
                            write_frame(blended)

            else:
                # Default: Clean, elegant crossfade
                for _ in range(hold_frames):
                    write_frame(cur_img)

                if not is_last:
                    for t_idx in range(trans_frames):
                        alpha = t_idx / float(trans_frames)
                        blended = cv2.addWeighted(cur_img, 1.0 - alpha, next_img, alpha, 0)
                        write_frame(blended)

        proc.stdin.close()
        proc.wait()
    except Exception as e:
        if proc.stdin:
            proc.stdin.close()
        proc.kill()
        raise e

    # If audio is attached, merge audio using ffmpeg with smooth fade-out
    if audio_path and os.path.exists(audio_path):
        try:
            total_duration = (num_images * hold_frames + (num_images - 1) * trans_frames) / fps
            fade_start = max(0, total_duration - 1.5)
            
            audio_cmd = [
                ffmpeg_exe, "-y",
                "-i", temp_video,
                "-stream_loop", "-1",
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-filter:a", f"afade=t=out:st={fade_start:.2f}:d=1.5",
                "-t", f"{total_duration:.2f}",
                output_path
            ]
            sub_res = subprocess.run(audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if sub_res.returncode == 0:
                if os.path.exists(temp_video) and temp_video != output_path:
                    os.remove(temp_video)
            else:
                # Fallback to silent video if audio merge failed
                if os.path.exists(temp_video) and temp_video != output_path:
                    os.replace(temp_video, output_path)
        except Exception:
            if os.path.exists(temp_video) and temp_video != output_path:
                os.replace(temp_video, output_path)

    return output_path
