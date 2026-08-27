"""MiniMax H3 Video To Latent.

Encode an existing video's frames into the audio+video ("AV") latent that
MiniMax-H3 video nodes consume, so an H3 tiled-upscale / re-sampling workflow can
start from a video file instead of a freshly generated first pass.

The node mirrors how ComfyUI core encodes MiniMax H3 reference videos
(``comfy_extras/nodes_minimax_h3.py``):

* frames are padded up to the H3 temporal grid  (frame_count % 17 == 5);
* spatial size is floored to a multiple of 16 for the H3 video VAE;
* ``vae.encode`` produces the video latent ``[1, 24, T, H/16, W/16]``;
* a silent audio latent ``[1, 32, 2, round(frames * 40 / 24)]`` is paired with it
  in a ``NestedTensor``. The source soundtrack should be routed to the final
  "Create Video" node directly, because the carried audio is silent.
"""

import torch

import comfy
import comfy.nested_tensor

FPS = 24
AUDIO_LATENT_FPS = 40
VIDEO_LATENT_CHANNELS = 24
AUDIO_LATENT_CHANNELS = 32
MIN_FRAMES = 5


def _align_to_h3_grid(n):
    """Smallest frame count >= n that satisfies the H3 grid (n % 17 == 5)."""
    while n % 17 != 5:
        n += 1
    return n


class MiniMaxH3VideoToLatent:
    """Encode a video frame batch (IMAGE) into a MiniMax H3 AV latent."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": (
                    "IMAGE",
                    {
                        "tooltip": (
                            "Video frames at 24 fps, e.g. Load Video -> "
                            "Get Video Components (images), or a VHS Load Video output."
                        ),
                    },
                ),
                "vae": (
                    "VAE",
                    {
                        "tooltip": (
                            "MiniMax H3 VIDEO VAE "
                            "(minimax_h3_video_vae...). The same one used to decode H3 video."
                        ),
                    },
                ),
            },
        }

    RETURN_TYPES = ("LATENT", "INT")
    RETURN_NAMES = ("latent", "frame_count")
    FUNCTION = "encode"
    CATEGORY = "MiniMax H3"
    DESCRIPTION = (
        "Encode an existing video's frames into a MiniMax H3 AV latent "
        "(video + silent audio), so an H3 upscale/re-sample node can start from a "
        "video file instead of a first-generation pass. Also outputs the aligned "
        "frame count (17k+5) for the reference node's length."
    )

    def encode(self, images, vae):
        frames = images[..., :3]
        n = int(frames.shape[0])
        if n < MIN_FRAMES:
            raise ValueError(
                f"MiniMaxH3VideoToLatent needs at least {MIN_FRAMES} frames "
                f"(~{MIN_FRAMES / FPS:.1f}s at {FPS} fps), got {n}."
            )

        # Spatial dims must be multiples of 16 for the H3 video VAE.
        h = (int(frames.shape[1]) // 16) * 16
        w = (int(frames.shape[2]) // 16) * 16
        if h < 16 or w < 16:
            raise ValueError(
                f"MiniMaxH3VideoToLatent: frames too small to encode ({w}x{h})."
            )
        frames = frames[:, :h, :w, :].contiguous()

        # Temporal: pad UP to the H3 grid (frame_count % 17 == 5) by repeating
        # the last frame, so no content is dropped.
        target = _align_to_h3_grid(n)
        if target > n:
            pad = frames[-1:].repeat(target - n, 1, 1, 1)
            frames = torch.cat([frames, pad], dim=0)

        z = vae.encode(frames)  # -> [1, 24, T, h/16, w/16]
        if z.ndim != 5 or z.shape[1] != VIDEO_LATENT_CHANNELS:
            raise ValueError(
                "MiniMaxH3VideoToLatent: expected a MiniMax H3 video latent "
                f"[1, {VIDEO_LATENT_CHANNELS}, T, H, W], got {tuple(z.shape)}. "
                "Make sure the VAE is a MiniMax H3 VIDEO VAE "
                "(minimax_h3_video_vae...), not an image or audio VAE."
            )

        audio_t = round(target / FPS * AUDIO_LATENT_FPS)
        audio = torch.zeros(
            [1, AUDIO_LATENT_CHANNELS, 2, audio_t], device=z.device, dtype=z.dtype
        )
        latent = {"samples": comfy.nested_tensor.NestedTensor((z, audio))}

        print(
            f"[MiniMaxH3VideoToLatent] {n} frames -> aligned {target} "
            f"({w}x{h}); video latent {tuple(z.shape)}; silent audio T={audio_t}.",
            flush=True,
        )
        return (latent, target)


NODE_CLASS_MAPPINGS = {
    "MiniMaxH3VideoToLatent": MiniMaxH3VideoToLatent,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxH3VideoToLatent": "MiniMax H3 Video To Latent",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
