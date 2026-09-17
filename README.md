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
Note: most text-to-3D models are too heavy for free HF inference and require custom runtimes, GPUs, or external tools such as Blender or ComfyUI.
</em></small></p>

- **Text** — prompt a text-to-3D model
- **Image** — send an image to an image-to-3D model
- **Upload** — load an existing STL/OBJ/PLY/GLB and optionally send it to a model for
  refinement or detailing

When available, paste either a Hugging Face model repo id (e.g. `org/model-name`) or a full Inference Endpoint / Space API URL. As of 9/16/2026 no 3D-generation model is available on the free serverless Inference API — check the model card, or deploy a dedicated Inference Endpoint and paste its URL instead.

Your API key is used only for the request you trigger; it is not stored by this Space.
