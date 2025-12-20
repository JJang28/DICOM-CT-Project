"""UI panel definitions for the DICOMator add-on (CT-only research build)."""
from __future__ import annotations

import math
import os

import bpy
from bpy.types import Context, Panel
from mathutils import Vector

from .constants import PYDICOM_AVAILABLE
from .utils import get_float_prop, get_str_prop


class VIEW3D_PT_dicomator_panel(Panel):
    """Root panel that hosts the add-on UI."""

    bl_label = "DICOMator (CT)"
    bl_idname = "VIEW3D_PT_dicomator_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DICOMator"

    def draw(self, context: Context) -> None:  # pragma: no cover
        layout = self.layout
        if not (context.active_object and context.active_object.type == 'MESH'):
            layout.label(text="Select a mesh object to export", icon='INFO')
        else:
            layout.label(text="CT export configuration", icon='TRIA_DOWN')


class VIEW3D_PT_dicomator_selection_info(Panel):
    bl_label = "Selection Info"
    bl_idname = "VIEW3D_PT_dicomator_selection_info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DICOMator"
    bl_parent_id = "VIEW3D_PT_dicomator_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:  # pragma: no cover
        layout = self.layout
        props = context.scene.dicomator_props

        if not (context.active_object and context.active_object.type == 'MESH'):
            layout.label(text="No mesh selected", icon='INFO')
            return

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        active_obj = context.active_object
        if not selected_meshes:
            selected_meshes = [active_obj]

        layout.label(
            text=f"Selected: {len(selected_meshes)} mesh(es)",
            icon='MESH_DATA'
        )

        bbox_corners = []
        for obj in selected_meshes:
            bbox_corners.extend(obj.matrix_world @ Vector(c) for c in obj.bound_box)

        min_x, max_x = min(c.x for c in bbox_corners), max(c.x for c in bbox_corners)
        min_y, max_y = min(c.y for c in bbox_corners), max(c.y for c in bbox_corners)
        min_z, max_z = min(c.z for c in bbox_corners), max(c.z for c in bbox_corners)

        width, height, depth = max_x - min_x, max_y - min_y, max_z - min_z

        box = layout.box()
        box.label(text="Bounding Box (m)", icon='INFO')
        box.label(text=f"{width:.2f} × {height:.2f} × {depth:.2f}")

        lateral_mm = get_float_prop(props, "lateral_resolution_mm", 2.0)
        axial_mm = get_float_prop(props, "axial_resolution_mm", 2.0)

        if lateral_mm > 0.0 and axial_mm > 0.0:
            vx = lateral_mm * 0.001
            vz = axial_mm * 0.001
            est = (
                math.ceil(width / vx)
                * math.ceil(height / vx)
                * math.ceil(depth / vz)
            )

            box.label(text=f"Estimated voxels: {est:,}")
            box.label(text=f"Estimated memory: {(est * 2) / (1024**2):.1f} MB")

            if est > 100_000_000:
                box.label(text="Grid too large!", icon='ERROR')


class VIEW3D_PT_dicomator_per_object_hu(Panel):
    bl_label = "Per-Object HU (CT)"
    bl_idname = "VIEW3D_PT_dicomator_per_object_hu"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DICOMator"
    bl_parent_id = "VIEW3D_PT_dicomator_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:  # pragma: no cover
        layout = self.layout
        if not (context.active_object and context.active_object.type == 'MESH'):
            layout.label(text="No mesh selected", icon='INFO')
            return

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        box = layout.box()
        box.label(text="CT Hounsfield Units", icon='MOD_PHYSICS')

        for obj in selected_meshes:
            col = box.column(align=True)
            col.label(text=obj.name, icon='MESH_DATA')
            row = col.row(align=True)
            row.prop(obj, "dicomator_material", text="Material")
            row.prop(obj, "dicomator_hu", text="HU")


class VIEW3D_PT_dicomator_patient_info(Panel):
    bl_label = "Patient Information"
    bl_idname = "VIEW3D_PT_dicomator_patient_info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DICOMator"
    bl_parent_id = "VIEW3D_PT_dicomator_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:  # pragma: no cover
        box = self.layout.box()
        props = context.scene.dicomator_props
        box.label(text="Patient Metadata", icon='USER')
        box.prop(props, "patient_name")
        box.prop(props, "patient_id")
        box.prop(props, "patient_sex")


class VIEW3D_PT_dicomator_orientation(Panel):
    bl_label = "Image Orientation"
    bl_idname = "VIEW3D_PT_dicomator_orientation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DICOMator"
    bl_parent_id = "VIEW3D_PT_dicomator_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:  # pragma: no cover
        box = self.layout.box()
        box.label(text="CT Patient Orientation", icon='ORIENTATION_GIMBAL')
        box.prop(context.scene.dicomator_props, "patient_position")


class VIEW3D_PT_dicomator_export_settings(Panel):
    bl_label = "Export Settings (CT)"
    bl_idname = "VIEW3D_PT_dicomator_export_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DICOMator"
    bl_parent_id = "VIEW3D_PT_dicomator_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:  # pragma: no cover
        layout = self.layout
        props = context.scene.dicomator_props

        box = layout.box()
        box.label(text="CT Export Settings", icon='SETTINGS')

        row = box.row(align=True)
        row.prop(props, "lateral_resolution_mm", text="Lateral (mm)")
        row.prop(props, "axial_resolution_mm", text="Axial (mm)")

        box.prop(props, "apply_modifiers")
        box.prop(props, "export_directory")
        box.prop(props, "series_description")

        artifact_box = box.box()
        artifact_box.label(text="CT Artifacts", icon='SHADERFX')

        artifact_box.prop(props, "enable_partial_volume")
        artifact_box.prop(props, "enable_metal_artifacts")
        artifact_box.prop(props, "enable_ring_artifacts")
        artifact_box.prop(props, "enable_noise")
        artifact_box.prop(props, "enable_poisson_noise")
        artifact_box.prop(props, "enable_motion_artifact")

        if PYDICOM_AVAILABLE:
            layout.operator("mesh.export_dicom", icon='EXPORT')
        else:
            layout.label(text="pydicom not available", icon='ERROR')


__all__ = [
    "VIEW3D_PT_dicomator_panel",
    "VIEW3D_PT_dicomator_selection_info",
    "VIEW3D_PT_dicomator_per_object_hu",
    "VIEW3D_PT_dicomator_patient_info",
    "VIEW3D_PT_dicomator_orientation",
    "VIEW3D_PT_dicomator_export_settings",
]
