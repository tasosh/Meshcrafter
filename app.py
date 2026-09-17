import json
import os
import re
import tempfile

import gradio as gr
import requests
import trimesh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def endpoint_for(model_id_or_url: str) -> str:
    """Turn a bare repo id into an HF Inference URL; pass full URLs through.

    Note: the old api-inference.huggingface.co domain was retired — serverless
    inference now goes through router.huggingface.co/hf-inference.
    """
    v = (model_id_or_url or "").strip()
    if v.startswith("http://") or v.startswith("https://"):
        return v
    return f"https://router.huggingface.co/hf-inference/models/{v}"


def friendly_http_error(status: int, text: str) -> str:
    if status == 503:
        return "The model is still loading on Hugging Face's servers. Wait a moment and try again."
    if status in (401, 403):
        return "Hugging Face rejected the API key. Check it's correct and has inference access."
    if status == 404:
        return (
            "Model or endpoint not found. Check the id or URL — or the model isn't "
            "deployed on HF serverless inference; check its model card, or paste a "
            "dedicated Inference Endpoint URL instead."
        )
    if status == 429:
        return "Rate limited by Hugging Face. Wait a moment and try again."
    return f"Request failed with status {status} — {text[:160]}"


def call_hf(model_id_or_url, api_key, data, content_type):
    if not api_key:
        raise gr.Error("Enter your Hugging Face API key first.")
    if not model_id_or_url:
        raise gr.Error("Enter a model repo id or endpoint URL.")

    url = endpoint_for(model_id_or_url)
    headers = {"Authorization": f"Bearer {api_key}"}
    if content_type:
        headers["Content-Type"] = content_type

    try:
        resp = requests.post(url, headers=headers, data=data, timeout=180)
    except requests.RequestException as e:
        raise gr.Error(f"Couldn't reach that endpoint: {e}")

    if not resp.ok:
        raise gr.Error(friendly_http_error(resp.status_code, resp.text))
    return resp.content


def sniff_extension(data):
    """Identify a mesh file from raw bytes, or raise a friendly gr.Error."""
    if data[:4] == b"glTF":
        return ".glb"

    if len(data) >= 84:
        tri_count = int.from_bytes(data[80:84], "little")
        if 84 + tri_count * 50 == len(data) and tri_count > 0:
            return ".stl"

    head = data[:2048].decode("utf-8", errors="ignore").strip()
    head_lower = head.lower()

    if head_lower.startswith("{"):
        try:
            payload = json.loads(data.decode("utf-8", errors="ignore"))
        except Exception:
            raise gr.Error("The model returned data this app can't parse.")
        if isinstance(payload, dict) and payload.get("error"):
            extra = f" (~{round(payload['estimated_time'])}s)" if payload.get("estimated_time") else ""
            raise gr.Error(f"{payload['error']}{extra}")
        if isinstance(payload, dict) and payload.get("asset"):
            return ".gltf"
        raise gr.Error("This model returned JSON without mesh data — check its output type on the model card.")

    if head_lower.startswith("solid"):
        return ".stl"
    if head_lower.startswith("ply"):
        return ".ply"
    if re.search(r"(^|\n)\s*v\s+-?[\d.]", head) and re.search(r"(^|\n)\s*f\s+\d", head_lower):
        return ".obj"

    raise gr.Error("Format not recognized. Expected GLB, OBJ, STL, or PLY.")


def save_and_prepare(raw_bytes, forced_ext=None):
    """Write raw bytes to a temp file, then try to normalize an STL export via trimesh."""
    ext = forced_ext or sniff_extension(raw_bytes)
    tmp_dir = tempfile.mkdtemp()
    src_path = os.path.join(tmp_dir, "model" + ext)
    with open(src_path, "wb") as f:
        f.write(raw_bytes)

    stl_path = None
    try:
        mesh = trimesh.load(src_path, force="mesh")
        if hasattr(mesh, "vertices") and hasattr(mesh, "faces") and len(mesh.faces) > 0:
            stl_path = os.path.join(tmp_dir, "export.stl")
            mesh.export(stl_path)
    except Exception:
        stl_path = None  # point clouds / unsupported geometry: viewer still works, export doesn't

    return src_path, stl_path


def result_status(stl_path, verb="Model generated"):
    if stl_path:
        return f"{verb}. STL export ready below."
    return f"{verb} — loaded as a point cloud or non-mesh geometry, so there's no surface to export as STL."


# ---------------------------------------------------------------------------
# Tab actions
# ---------------------------------------------------------------------------

def generate_from_text(prompt, model_id, api_key):
    if not prompt or not prompt.strip():
        raise gr.Error("Describe what you want to generate.")
    raw = call_hf(model_id, api_key, json.dumps({"inputs": prompt}).encode("utf-8"), "application/json")
    src_path, stl_path = save_and_prepare(raw)
    return src_path, stl_path, result_status(stl_path)


def generate_from_image(image_path, model_id, api_key):
    if not image_path:
        raise gr.Error("Upload an image first.")
    with open(image_path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(image_path)[1].lower()
    content_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")
    raw = call_hf(model_id, api_key, data, content_type)
    src_path, stl_path = save_and_prepare(raw)
    return src_path, stl_path, result_status(stl_path)


def load_upload(file_path):
    if not file_path:
        return None, None, ""
    with open(file_path, "rb") as f:
        raw = f.read()
    ext = os.path.splitext(file_path)[1].lower() or ".obj"
    src_path, stl_path = save_and_prepare(raw, forced_ext=ext)
    return src_path, stl_path, result_status(stl_path, verb="Loaded")


def refine_upload(file_path, model_id, api_key):
    if not file_path:
        raise gr.Error("Load a file first.")
    with open(file_path, "rb") as f:
        data = f.read()
    raw = call_hf(model_id, api_key, data, "application/octet-stream")
    src_path, stl_path = save_and_prepare(raw)
    return src_path, stl_path, result_status(stl_path, verb="Refined model ready")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="Meshcrafter") as demo:
    gr.Markdown(
        "# Meshcrafter\n"
        "Generate or load a 3D mesh through a Hugging Face model, view it, and export a clean STL for CAD or printing."
    )

    api_key = gr.Textbox(
        label="Hugging Face API key",
        type="password",
        placeholder="hf_...",
    )
    gr.Markdown(
        "Your key is only used for the request you trigger below — it isn't stored by this Space. "
        "Not every 3D-generation model is served on the free Inference API; check the model card first, "
        "or paste a full Inference Endpoint URL instead of a repo id."
    )

    with gr.Tabs():
        with gr.Tab("Text"):
            prompt = gr.Textbox(
                label="Describe the object",
                lines=3,
                placeholder="a low-poly mechanical gear, 40mm diameter",
            )
            text_model = gr.Textbox(
                label="Model repo id or endpoint URL",
                placeholder="org/model-name or https://your-endpoint",
            )
            text_btn = gr.Button("Generate model", variant="primary")

        with gr.Tab("Image"):
            image_in = gr.Image(label="Source image", type="filepath")
            image_model = gr.Textbox(
                label="Model repo id or endpoint URL",
                placeholder="org/model-name or https://your-endpoint",
            )
            image_btn = gr.Button("Generate model", variant="primary")

        with gr.Tab("Upload"):
            upload_in = gr.File(
                label="3D file",
                file_types=[".stl", ".obj", ".ply", ".glb", ".gltf"],
            )
            upload_model = gr.Textbox(
                label="Optional: send to a model to refine or add detail",
                placeholder="org/model-name or https://your-endpoint",
            )
            refine_btn = gr.Button("Send to model")

    status = gr.Markdown()
    viewer = gr.Model3D(label="Viewer")
    stl_out = gr.File(label="Export STL")

    text_btn.click(generate_from_text, [prompt, text_model, api_key], [viewer, stl_out, status])
    image_btn.click(generate_from_image, [image_in, image_model, api_key], [viewer, stl_out, status])
    upload_in.change(load_upload, [upload_in], [viewer, stl_out, status])
    refine_btn.click(refine_upload, [upload_in, upload_model, api_key], [viewer, stl_out, status])

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="orange", neutral_hue="slate"))
