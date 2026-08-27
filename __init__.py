"""Comfyui_Minimax_H3_Video_To_Latent.

A single node that encodes an existing video's frames into a MiniMax H3 AV
latent, so H3 tiled-upscale / re-sampling workflows can start from a video file
instead of a first-generation pass.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
__version__ = "1.1.0"

WEB_DIRECTORY = None
