[English](README.md) | **简体中文**

# ComfyUI — MiniMax H3 Video To Latent（视频转 H3 Latent）

一个独立的 ComfyUI 节点：把**已有的视频文件**编码成 MiniMax-H3 节点所需的
**音视频（AV）latent**。

它让 H3 分块放大 / 二次采样工作流可以直接从一段视频开始，而不必先跑一遍第一次
生成。当你低分辨率的"一采"已经满意、只想对它重跑放大/二采阶段时，尤其有用。

- 节点名：**MiniMax H3 Video To Latent**
- 分类：`MiniMax H3`
- 输出：`latent`（H3 AV latent）与 `frame_count`（对齐后的帧数，INT）

---

## 解决什么问题

MiniMax-H3 的放大节点（例如分块版 "MMH3 Ultimate Upscale"）要求 `latent` 输入是
一个 H3 **AV latent**——即一个 `NestedTensor`，里面是视频 latent
`[1, 24, T, H/16, W/16]` 加音频 latent `[1, 32, 2, T_a]`。

通常这个 latent 只来自"第一次采样"的输出。可如果你已经有一段成片，就没有 latent
可接。本节点完成反向步骤：**视频帧 → H3 AV latent**，编码方式与 ComfyUI 官方核心
编码 H3 参考视频完全一致。

## 环境要求

- 支持 **MiniMax H3** 的 ComfyUI 版本。
- MiniMax H3 **视频 VAE** 模型（`minimax_h3_video_vae...`）。
- 一个把视频读成帧的途径：
  - 官方 **Load Video** → **Get Video Components**（输出 images + audio），或
  - **Video Helper Suite / VHS** 的 Load Video。

除 ComfyUI 自带内容外无需额外 pip 依赖。

## 安装

### ComfyUI Manager

用 git URL 安装：
`https://github.com/hello-jiabin/Comfyui_Minimax_H3_Video_To_Latent`

### 手动

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hello-jiabin/Comfyui_Minimax_H3_Video_To_Latent.git
```

然后重启 ComfyUI。

## 输入 / 输出

| 接口 | 类型 | 说明 |
|------|------|------|
| `images`（入） | IMAGE | 24fps 视频帧（Load Video → Get Video Components 的 images，或 VHS）。 |
| `vae`（入） | VAE | MiniMax H3 **视频** VAE（`minimax_h3_video_vae...`）。 |
| `latent`（出） | LATENT | H3 AV latent（视频 + **静音**音频）→ 接放大/二采节点。 |
| `frame_count`（出） | INT | 对齐后的帧数（`17k+5`），接参考节点的 `length`。 |
| `width`（出） | INT | 源画布宽度（像素，32 的倍数），接参考节点的 `width`。 |
| `height`（出） | INT | 源画布高度（像素，32 的倍数），接参考节点的 `height`。 |

## 推荐接线

```
Load Video ──► Get Video Components ──images──► MiniMax H3 Video To Latent ──latent──────► MMH3 Ultimate Upscale.latent
                             │                  (vae ◄── H3 视频 VAE)       ├─frame_count─► H3 Reference-to-Video.length
                             │                                               ├─width──────► H3 Reference-to-Video.width
                             │                                               └─height─────► H3 Reference-to-Video.height
                             └──audio──────────────────────────────────────────────────► Create Video.audio
```

说明：

- 把 `frame_count` 接到参考/条件节点的 **length**，让条件长度与（对齐后的）视频一致。
- latent 里的音频**故意是静音**。请把 Get Video Components 输出的源 `audio` 直接接到
  **Create Video**，以保留原声。

## 工作原理

1. 去掉 alpha 通道，并把宽高向下取整到 **16** 的倍数，满足 H3 视频 VAE。
2. 把帧数向上补齐到 H3 时间网格（`frame_count % 17 == 5`），用最后一帧重复填充，
   **不丢帧**。
3. `vae.encode(frames)` → 视频 latent `[1, 24, T, H/16, W/16]`。
4. 构造匹配的静音音频 latent `[1, 32, 2, round(帧数 * 40 / 24)]`。
5. 两者打包成 `NestedTensor` 放进 `{"samples": ...}` 返回，同时返回对齐帧数。

控制台会打印类似：

```
[MiniMaxH3VideoToLatent] 144 frames -> aligned 145 (864x480); video latent torch.Size([1, 24, 42, 30, 54]); silent audio T=242.
```

## 小贴士

- 源视频建议为 **24fps**（H3 的帧率）。
- 一定要用**视频** VAE，不是图像或音频 VAE；若编码结果不像 H3 视频（不是 24 通道），
  节点会报出明确错误。
- 至少需要 5 帧（约 0.2 秒）。

## 免责声明

这是一个独立的社区工具，与 MiniMax 官方无隶属或背书关系。相关模型与商标归其各自
所有者所有。

## 许可证

[MIT](LICENSE)
