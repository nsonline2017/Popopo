import os
import io
import json
import numpy as np
import pydicom
from PIL import Image

MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
os.makedirs(MEDIA_ROOT, exist_ok=True)

def _to_uint8(arr):
    arr = np.asarray(arr)
    if arr.dtype == np.uint8:
        return arr
    # handle multi-frame: take first? caller handles
    arr = arr.astype(np.float64)
    # windowing if possible
    mn = arr.min()
    mx = arr.max()
    if mx - mn == 0:
        out = np.zeros_like(arr, dtype=np.uint8)
    else:
        out = (arr - mn) / (mx - mn) * 255.0
    return out.astype(np.uint8)

def convert_dicom_to_png(ds, out_path):
    arr = ds.pixel_array
    # if 3D (series of frames in one file), take first frame
    if arr.ndim == 3 and arr.shape[0] > 1 and arr.shape[-1] not in (3,4):
        # could be (frames, H, W)
        arr = arr[0]
    if arr.ndim == 3 and arr.shape[-1] in (3,4):
        img = Image.fromarray(arr.astype(np.uint8) if arr.dtype!=np.uint8 else arr)
    else:
        u8 = _to_uint8(arr)
        # apply photometric interpretation inversion if MONOCHROME1
        pi = getattr(ds, "PhotometricInterpretation", "")
        if pi == "MONOCHROME1":
            u8 = 255 - u8
        img = Image.fromarray(u8)
    img.save(out_path, "PNG")
    return out_path

def process_upload(files, study_dir):
    """files: list of (filename, bytes). Returns (study_type, list_rel_paths)."""
    os.makedirs(study_dir, exist_ok=True)
    # sort dicom files
    dicom_items = []
    for name, data in files:
        path = os.path.join(study_dir, os.path.basename(name))
        with open(path, "wb") as f:
            f.write(data)
        try:
            ds = pydicom.dcmread(path, stop_before_pixels=False)
            dicom_items.append((path, ds))
        except Exception:
            # not dicom; skip
            try:
                os.remove(path)
            except Exception:
                pass
    if not dicom_items:
        raise ValueError("No valid DICOM files found")
    # sort by InstanceNumber if present
    def key(item):
        ds = item[1]
        try:
            return int(getattr(ds, "InstanceNumber", 0))
        except Exception:
            return 0
    dicom_items.sort(key=key)

    rel_paths = []
    if len(dicom_items) == 1:
        out_name = "image_0.png"
        out_path = os.path.join(study_dir, out_name)
        convert_dicom_to_png(dicom_items[0][1], out_path)
        rel = os.path.relpath(out_path, MEDIA_ROOT)
        rel_paths.append(rel.replace(os.sep, "/"))
        study_type = "image"
    else:
        study_type = "series"
        for i, (path, ds) in enumerate(dicom_items):
            out_name = f"slice_{i:04d}.png"
            out_path = os.path.join(study_dir, out_name)
            convert_dicom_to_png(ds, out_path)
            rel = os.path.relpath(out_path, MEDIA_ROOT)
            rel_paths.append(rel.replace(os.sep, "/"))
    return study_type, rel_paths
