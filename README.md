**English** | [简体中文](README_CN.md)

# ComfyUI — MiniMax H3 Video To Latent

A single ComfyUI node that encodes an **existing video file** into the
**audio+video (AV) latent** that MiniMax-H3 video nodes consume.

It lets an H3 tiled-upscale / re-sampling workflow start from a video you already
generated (or any video), instead of being forced to run a first-generation pass
first. This is especially useful when your first pass at low resolution looks
good but you want to re-run only the upscale/second-pass stage on it.

- Node name: **MiniMax H3 Video To Latent**
- Category: `MiniMax H3`
- Outputs: `latent` (H3 AV latent) and `frame_count` (aligned frame count, INT)

---

## Why

MiniMax-H3 upscale nodes (for example the tiled "MMH3 Ultimate Upscale") expect
their `latent` input to be an H3 **AV latent** — a `NestedTensor` of a video
latent `[1, 24, T, H/16, W/16]` plus an audio latent `[1, 32, 2, T_a]`.

Normally that latent only exists as the output of a first-pass H3 sampler. If you
already have a finished video, there is no latent to feed in. This node performs
the inverse step: video frames → H3 AV latent, following exactly how ComfyUI core
encodes H3 reference videos.

## Requirements

- A ComfyUI build with **MiniMax H3** support.
- The MiniMax H3 **video VAE** model (`minimax_h3_video_vae...`).
- A way to load a video into frames:
  - core **Load Video** → **Get Video Components** (images + audio), or
  - **Video Helper Suite** / VHS **Load Video** (images + audio).

No pip dependencies are required beyond what ComfyUI already ships.

## Installation

### ComfyUI Manager

Install via git URL:
`https://github.com/hello-jiabin/Comfyui_Minimax_H3_Video_To_Latent`

### Manual

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hello-jiabin/Comfyui_Minimax_H3_Video_To_Latent.git
```

Then restart ComfyUI.

## Inputs / Outputs

| Slot | Type | Description |
|------|------|-------------|
| `images` (in) | IMAGE | Video frames at 24 fps (Load Video → Get Video Components → images, or VHS). |
| `vae` (in) | VAE | MiniMax H3 **video** VAE (`minimax_h3_video_vae...`). |
| `latent` (out) | LATENT | H3 AV latent (video + **silent** audio) → upscale/re-sample node. |
| `frame_count` (out) | INT | Aligned frame count (`17k+5`); wire to the reference node's `length`. |

## Example wiring

```
Load Video ──► Get Video Components ──images──► MiniMax H3 Video To Latent ──latent──────► MMH3 Ultimate Upscale.latent
                             │                  (vae ◄── H3 video VAE)     └─frame_count─► H3 Reference-to-Video.length
                             └──audio──────────────────────────────────────────────────► Create Video.audio
```

Notes:

- Feed `frame_count` to the reference/conditioning node's **length** so the
  conditioning matches the (aligned) video length.
- The latent carries **silent** audio on purpose. Route the source `audio` from
  **Get Video Components** straight to **Create Video** to keep the original
  soundtrack.

## How it works

1. Drops the alpha channel and floors width/height to a multiple of **16** for
   the H3 video VAE.
2. Pads the frame count **up** to the H3 temporal grid (`frame_count % 17 == 5`)
   by repeating the last frame — no frames are dropped.
3. `vae.encode(frames)` → video latent `[1, 24, T, H/16, W/16]`.
4. Builds a matching silent audio latent `[1, 32, 2, round(frames * 40 / 24)]`.
5. Returns both as a `NestedTensor` inside `{"samples": ...}`, plus the aligned
   frame count.

The console prints a line such as:

```
[MiniMaxH3VideoToLatent] 144 frames -> aligned 145 (864x480); video latent torch.Size([1, 24, 42, 30, 54]); silent audio T=242.
```

## Tips

- Source video is expected at **24 fps** (H3's frame rate).
- Use the **video** VAE, not an image or audio VAE; the node raises a clear error
  if the encoded latent does not look like H3 video (24 channels).
- At least 5 frames (~0.2 s) are required.

## Disclaimer

This project is an independent community tool. It is not affiliated with or
endorsed by MiniMax. Model and trademark belong to their respective owners.

## License

[MIT](LICENSE)
