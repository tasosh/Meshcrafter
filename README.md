---
title: Meshcrafter
emoji: 🧊
colorFrom: gray
colorTo: yellow
sdk: gradio
sdk_version: 6.27.0
app_file: app.py
pinned: false
---

# Meshcrafter

Connect a Hugging Face API key to a text, image, or upload-based 3D workflow, view the
result, and export a clean STL for CAD or 3D printing.

# I will revisit this in 3 months.

<p><small><em>
  Note: As of 9/16/2026, Text‑to‑3D Models Don’t Have HF Inference Support.  Text‑to‑3D models (Zero123, Shap‑E, LGM, TRELLIS, LLaMA‑Mesh, HY‑Motion, etc.) are:  1. Too heavy for HF free/hosted inference.  Most require: 8–24 GB VRAM, Multi‑stage pipelines (depth → NeRF → mesh → cleanup), GPU‑resident marching cubes or mesh extraction, HF Inference API doesn’t support these pipelines.  2. Many require external engines, examples: Blender (LLaMA‑Mesh, BlenderLLM), ComfyUI (TripoSR pipelines), Custom CUDA kernels (Zero123, LGM), HF cannot host these.  3. Some models are research-only: TRELLIS, HY‑Motion, Arbor, MeshGPT-preview — all require custom runtimes.
 smaller
</em></small></p>

- **Text** — prompt a text-to-3D model
- **Image** — send an image to an image-to-3D model
- **Upload** — load an existing STL/OBJ/PLY/GLB and optionally send it to a model for
  refinement or detailing

When available, paste either a Hugging Face model repo id (e.g. `org/model-name`) or a full Inference Endpoint / Space API URL. As of 9/16/2026 no 3D-generation model is available on the free serverless Inference API — check the model card, or deploy a dedicated Inference Endpoint and paste its URL instead.

Your API key is used only for the request you trigger; it is not stored by this Space.
