#!/usr/bin/env python3
"""
DICOMator CLI (non-Blender research version)

Derived from DICOMator by Michael Douglass (MIT License).
"""

import argparse
import json
import os
import sys
import trimesh
import numpy as np

from dicomator.voxelization import voxelize_meshes_to_hu
from dicomator.dicom_export import export_voxel_grid_to_dicom
from dicomator.artifacts import (
    add_gaussian_noise,
    add_poisson_noise,
    add_ring_artifacts,
    add_motion_artifact,
    add_metal_artifacts,
    apply_partial_volume_effect,
)
from dicomator.constants import AIR_DENSITY


# -----------------------------
# Argument parsing
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert 3D meshes into DICOM CT (research CLI version)"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="JSON configuration file describing meshes, HU values, and artifacts",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for DICOM series",
    )

    return parser.parse_args()


# -----------------------------
# Load configuration
# -----------------------------
def load_config(path):
    with open(path, "r") as f:
        return json.load(f)


# -----------------------------
# Main pipeline
# -----------------------------
def main():
    args = parse_args()
    config = load_config(args.config)

    voxel_size = config.get("voxel_size", 1.0)
    padding = config.get("padding", 1)

    # ---- Load meshes ----
    meshes = []
    for entry in config["meshes"]:
        name = entry["name"]
        path = entry["path"]
        hu = int(entry["hu"])

        if not os.path.exists(path):
            raise FileNotFoundError(path)

        mesh = trimesh.load(path, force="mesh")

        if not mesh.is_watertight:
            print(f"WARNING: Mesh '{name}' is not watertight")

        meshes.append((name, mesh, hu))

    # ---- Voxelization ----
    print("Voxelizing meshes...")
    hu_grid, origin, shape = voxelize_meshes_to_hu(
        meshes=meshes,
        voxel_size=voxel_size,
        padding=padding,
        air_hu=AIR_DENSITY,
    )

    # ---- Optional artifacts ----
    artifacts = config.get("artifacts", {})

    if artifacts.get("partial_volume", False):
        hu_grid = apply_partial_volume_effect(hu_grid)

    if "gaussian_noise" in artifacts:
        hu_grid = add_gaussian_noise(
            hu_grid,
            sigma=artifacts["gaussian_noise"].get("sigma", 10),
        )

    if "poisson_noise" in artifacts:
        hu_grid = add_poisson_noise(hu_grid)

    if "ring_artifacts" in artifacts:
        hu_grid = add_ring_artifacts(
            hu_grid,
            strength=artifacts["ring_artifacts"].get("strength", 0.05),
        )

    if "motion_artifact" in artifacts:
        hu_grid = add_motion_artifact(
            hu_grid,
            shift_voxels=artifacts["motion_artifact"].get("shift_voxels", 2),
        )

    if "metal_artifacts" in artifacts:
        hu_grid = add_metal_artifacts(
            hu_grid,
            threshold=artifacts["metal_artifacts"].get("threshold", 2000),
        )

    # ---- Export DICOM ----
    os.makedirs(args.output, exist_ok=True)

    print("Exporting DICOM series...")
    export_voxel_grid_to_dicom(
        voxel_grid=hu_grid,
        origin=origin,
        voxel_size=voxel_size,
        output_dir=args.output,
        patient_info=config.get("patient", {}),
        study_info=config.get("study", {}),
    )

    print("Done.")


if __name__ == "__main__":
    main()




