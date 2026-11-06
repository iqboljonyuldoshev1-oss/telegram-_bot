"""
Video Maker Engine - Professional slideshow & montage generator from photos and video clips.
100% original quality: no AI distortion, with cinematic romantic transitions & blurred background.
"""

import os
import cv2
import numpy as np
import subprocess
import imageio_ffmpeg
from PIL import Image


def get_ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def create_canvas_frame_from_img(img: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
    """
    Fits any image/video frame into target_width x target_height canvas.
    Blurs and darkens background if aspect ratios differ, keeping foreground sharp and centered.
    """
    orig_h, orig_w = img.shape[:2]
    target_aspect = target_width / target_height
    orig_aspect = orig_w / orig_h

    # 1. Background covering target canvas
    if orig_aspect > target_aspect:
        new_h = target_height
        new_w = int(orig_w * (target_height / orig_h))
    else:
        new_w = target_width
        new_h = int(orig_h * (target_width / orig_w))

    resized_bg = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    start_x = max(0, (new_w - target_width) // 2)
    start_y = max(0, (new_h - target_height) // 2)
    bg_cropped = resized_bg[start_y:start_y + target_height, start_x:start_x + target_width]

    if bg_cropped.shape[0] != target_height or bg_cropped.shape[1] != target_width:
        bg_cropped = cv2.resize(bg_cropped, (target_width, target_height))

    blur_ksize = max(51, (min(target_width, target_height) // 15) | 1)
    blurred_bg = cv2.GaussianBlur(bg_cropped, (blur_ksize, blur_ksize), 0)
    blurred_bg = (blurred_bg.astype(np.float32) * 0.55).astype(np.uint8)

    # 2. Fit sharp foreground image inside canvas
    scale = min(target_width / orig_w, target_height / orig_h)
    fit_w = int(orig_w * scale)
    fit_h = int(orig_h * scale)
    fit_fg = cv2.resize(img, (fit_w, fit_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)

    x_offset = (target_width - fit_w) // 2
    y_offset = (target_height - fit_h) // 2

    canvas = blurred_bg.copy()
    canvas[y_offset:y_offset + fit_h, x_offset:x_offset + fit_w] = fit_fg
    return canvas


def load_media_frames(media_item: dict, target_width: int, target_height: int, num_frames: int) -> list[np.ndarray]:
    """
    Extracts or creates `num_frames` canvas frames for a media item (photo or video).
    """
    m_type = media_item.get("type", "photo")
    m_path = media_item.get("path", "")

    if m_type == "video":
        cap = cv2.VideoCapture(m_path)
        frames = []
        total_vid_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

        # Determine frame skip to span across video or fit num_frames
        step = max(1.0, total_vid_frames / max(1, num_frames))
        curr_f = 0.0

        for _ in range(num_frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(curr_f % total_vid_frames))
            ret, frame = cap.read()
            if not ret or frame is None:
                if frames:
                    frames.append(frames[-1].copy())
                else:
                    blank = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                    frames.append(blank)
            else:
                canvas = create_canvas_frame_from_img(frame, target_width, target_height)
                frames.append(canvas)
            curr_f += step

        cap.release()
        return frames

    else:
        # Static photo
        img = cv2.imread(m_path)
        if img is None:
            pil_img = Image.open(m_path).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        canvas = create_canvas_frame_from_img(img, target_width, target_height)
        # Return list with single base frame
        return [canvas]


def render_slideshow(
    media_items: list[dict],
    output_path: str,
    audio_path: str = None,
    aspect_ratio: str = "9:16",
    style: str = "ken_burns",
    slide_duration: float = 3.0,
    transition_duration: float = 0.6,
    fps: int = 30
) -> str:
    """
    Renders video montage from a list of photo and video media items.
    """
    if not media_items:
        raise ValueError("Kamida 1 ta rasm yoki video kerak!")

    resolutions = {
        "9:16": (720, 1280),   # Reels, TikTok, Shorts
        "16:9": (1280, 720),   # YouTube Landscape
        "1:1": (1080, 1080),   # Square
    }
    width, height = resolutions.get(aspect_ratio, (720, 1280))
    width = (width // 2) * 2
    height = (height // 2) * 2

    total_slide_frames = int(slide_duration * fps)
    trans_frames = int(transition_duration * fps) if len(media_items) > 1 else 0
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

    num_items = len(media_items)

    try:
        # Pre-cache or load items
        loaded_items = []
        for item in media_items:
            frames = load_media_frames(item, width, height, total_slide_frames)
            loaded_items.append({"type": item.get("type", "photo"), "frames": frames})

        for idx in range(num_items):
            cur_item = loaded_items[idx]
            next_item = loaded_items[(idx + 1) % num_items] if num_items > 1 else cur_item
            is_last = (idx == num_items - 1)

            cur_is_video = (cur_item["type"] == "video")
            next_is_video = (next_item["type"] == "video")

            # 1. Hold segment
            if cur_is_video:
                # Video has its own motion, write sequential video frames
                v_frames = cur_item["frames"]
                for f_idx in range(hold_frames):
                    frame = v_frames[min(f_idx, len(v_frames) - 1)]
                    write_frame(frame)
                cur_end_frame = v_frames[min(hold_frames - 1, len(v_frames) - 1)]
            else:
                base_img = cur_item["frames"][0]
                zoom_in = (idx % 2 == 0)

                if style == "ken_burns":
                    for f_idx in range(hold_frames):
                        progress = f_idx / max(1, total_slide_frames)
                        scale = 1.0 + (0.12 * progress if zoom_in else 0.12 * (1.0 - progress))
                        cw, ch = int(width / scale), int(height / scale)
                        cx1 = (width - cw) // 2
                        cy1 = (height - ch) // 2
                        cropped = base_img[cy1:cy1 + ch, cx1:cx1 + cw]
                        frame = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)
                        write_frame(frame)
                    cur_end_frame = frame
                else:
                    for _ in range(hold_frames):
                        write_frame(base_img)
                    cur_end_frame = base_img

            # 2. Transition segment into next item
            if not is_last:
                # First frame of next item
                if next_is_video:
                    next_start_frame = next_item["frames"][0]
                else:
                    next_start_frame = next_item["frames"][0]

                if style == "slide_left":
                    for t_idx in range(trans_frames):
                        alpha = t_idx / float(trans_frames)
                        t = alpha * alpha * (3 - 2 * alpha)
                        shift = int(width * t)

                        combined = np.zeros_like(cur_end_frame)
                        combined[:, :width - shift] = cur_end_frame[:, shift:]
                        combined[:, width - shift:] = next_start_frame[:, :shift]
                        write_frame(combined)

                elif style == "zoom_flash":
                    flash_len = min(6, trans_frames // 2)
                    for t_idx in range(trans_frames):
                        if t_idx < flash_len:
                            brightness = int(120 * (1.0 - t_idx / flash_len))
                            flash_f = cv2.add(cur_end_frame, np.full_like(cur_end_frame, brightness))
                            write_frame(flash_f)
                        else:
                            sub_alpha = (t_idx - flash_len) / float(trans_frames - flash_len)
                            blended = cv2.addWeighted(cur_end_frame, 1.0 - sub_alpha, next_start_frame, sub_alpha, 0)
                            write_frame(blended)

                else:
                    # Smooth crossfade
                    for t_idx in range(trans_frames):
                        alpha = t_idx / float(trans_frames)
                        blended = cv2.addWeighted(cur_end_frame, 1.0 - alpha, next_start_frame, alpha, 0)
                        write_frame(blended)

        proc.stdin.close()
        proc.wait()
    except Exception as e:
        if proc.stdin:
            proc.stdin.close()
        proc.kill()
        raise e

    # Merge audio if specified
    if audio_path and os.path.exists(audio_path):
        try:
            total_duration = (num_items * hold_frames + (num_items - 1) * trans_frames) / fps
            fade_start = max(0, total_duration - 1.5)

            audio_cmd = [
                ffmpeg_exe, "-y",
                "-loglevel", "error",
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
                if os.path.exists(temp_video) and temp_video != output_path:
                    os.replace(temp_video, output_path)
        except Exception:
            if os.path.exists(temp_video) and temp_video != output_path:
                os.replace(temp_video, output_path)

    return output_path
