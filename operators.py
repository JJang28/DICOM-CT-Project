"""Operator definitions for the DICOMator add-on (CT-only research build)."""
from __future__ import annotations

import math
import os

import bpy
from bpy.types import Operator
from mathutils import Vector

from .artifacts import (
    add_gaussian_noise,
    add_metal_artifacts,
    add_motion_artifact,
    add_poisson_noise,
    add_ring_artifacts,
    apply_partial_volume_effect,
)
from .constants import PYDICOM_AVAILABLE, generate_uid
from .dicom_export import export_voxel_grid_to_dicom
from .utils import force_ui_redraw, get_float_prop
from .voxelization import voxelize_objects_to_hu


def _get_int_prop(props, name: str, default: int) -> int:
    """Safely read an integer property, falling back to ``default`` on failure."""
    try:
        return int(getattr(props, name))
    except Exception:
        return int(default)


# ─────────────────────────────────────────────────────────────
# CT-ONLY artifact pipeline
# ─────────────────────────────────────────────────────────────
def _apply_configured_artifacts(hu_array, props):
    """Apply CT artifacts configured in ``props`` to ``hu_array``."""
    result = hu_array

    if getattr(props, "enable_partial_volume", False):
        kernel = max(1, _get_int_prop(props, "partial_volume_kernel", 3))
        if kernel % 2 == 0:
            kernel += 1
        iterations = max(1, _get_int_prop(props, "partial_volume_iterations", 1))
        mix = max(0.0, min(1.0, get_float_prop(props, "partial_volume_mix", 1.0)))
        result = apply_partial_volume_effect(
            result,
            kernel_size=kernel,
            iterations=iterations,
            mix=mix,
        )

    if getattr(props, "enable_metal_artifacts", False):
        intensity = max(0.0, get_float_prop(props, "metal_intensity", 400.0))
        threshold = get_float_prop(props, "metal_density_threshold", 2000.0)
        streaks = max(0, _get_int_prop(props, "metal_num_streaks", 10))
        falloff = max(0.1, get_float_prop(props, "metal_falloff", 6.0))
        result = add_metal_artifacts(
            result,
            intensity=float(intensity),
            density_threshold=float(threshold),
            num_streaks=streaks,
            falloff=float(falloff),
        )

    if getattr(props, "enable_ring_artifacts", False):
        ring_intensity = max(0.0, get_float_prop(props, "ring_intensity", 80.0))
        ring_radius = get_float_prop(props, "ring_radius", 0.5)
        thickness = max(0.0, get_float_prop(props, "ring_thickness", 0.02))
        jitter = max(0.0, get_float_prop(props, "ring_jitter", 0.02))
        result = add_ring_artifacts(
            result,
            ring_intensity=float(ring_intensity),
            ring_radius=float(ring_radius) if ring_radius is not None else None,
            thickness=float(thickness),
            jitter=float(jitter),
        )

    if getattr(props, "enable_motion_artifact", False):
        blur_size = max(1, _get_int_prop(props, "motion_blur_size", 9))
        if blur_size % 2 == 0:
            blur_size += 1
        severity = max(0.0, min(1.0, get_float_prop(props, "motion_severity", 0.5)))
        axis_prop = getattr(props, "motion_axis", 'X')
        axis = 0 if str(axis_prop).upper() != 'Y' else 1
        result = add_motion_artifact(
            result,
            blur_size=blur_size,
            severity=float(severity),
            axis=axis,
        )

    if getattr(props, "enable_noise", False):
        std_dev = max(0.0, get_float_prop(props, "noise_std_dev_hu", 20.0))
        if std_dev > 0.0:
            result = add_gaussian_noise(result, std_dev)

    if getattr(props, "enable_poisson_noise", False):
        scale = max(1.0, get_float_prop(props, "poisson_scale", 150.0))
        result = add_poisson_noise(result, scale=scale)

    return result


# ─────────────────────────────────────────────────────────────
# CT-ONLY Export Operator
# ─────────────────────────────────────────────────────────────
class MESH_OT_export_dicom(Operator):
    """Export selected meshes to a stack of CT DICOM files."""

    bl_idname = "mesh.export_dicom"
    bl_label = "Export to DICOM (CT)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            context.active_object is not None
            and context.active_object.type == 'MESH'
            and context.active_object.mode == 'OBJECT'
        )

    def execute(self, context: bpy.types.Context):
        if not PYDICOM_AVAILABLE:
            self.report({'ERROR'}, "pydicom library not available")
            return {'CANCELLED'}

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            self.report({'ERROR'}, "Please select at least one mesh object")
            return {'CANCELLED'}

        props = context.scene.dicomator_props
        output_dir = props.export_directory
        if not output_dir:
            self.report({'ERROR'}, "Please specify an export directory")
            return {'CANCELLED'}

        output_dir = os.path.abspath(bpy.path.abspath(output_dir))
        os.makedirs(output_dir, exist_ok=True)

        lateral_mm = get_float_prop(props, "lateral_resolution_mm", 2.0)
        axial_mm = get_float_prop(props, "axial_resolution_mm", 2.0)

        vx_m = vy_m = float(lateral_mm) * 0.001
        vz_m = float(axial_mm) * 0.001

        hu_array, origin, _ = voxelize_objects_to_hu(
            selected_meshes,
            voxel_size=(vx_m, vy_m, vz_m),
            padding=1,
            apply_modifiers=True,
            depsgraph=context.evaluated_depsgraph_get(),
        )

        hu_array = _apply_configured_artifacts(hu_array, props)

        result = export_voxel_grid_to_dicom(
            hu_array,
            (vx_m, vy_m, vz_m),
            output_dir,
            origin,
            patient_name=props.patient_name,
            patient_id=props.patient_id,
            patient_sex=props.patient_sex,
            series_description=props.series_description,
            direct_hu=True,
            dicom_modality="CT",  # CT-ONLY
        )

        if 'error' in result:
            self.report({'ERROR'}, result['error'])
            return {'CANCELLED'}

        self.report({'INFO'}, result['success'])
        return {'FINISHED'}


__all__ = ["MESH_OT_export_dicom"]
