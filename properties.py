"""Property group definitions for the DICOMator add-on (CT-only)."""
from __future__ import annotations
import bpy
from .constants import get_material_intensity


def apply_material_intensity(obj: bpy.types.Object) -> None:
    """Assign the CT HU for ``obj`` based on its material."""
    material_key = getattr(obj, "dicomator_material", "CUSTOM")
    if material_key == "CUSTOM":
        return
    value = get_material_intensity(material_key, "CT")
    if value is not None:
        obj.dicomator_hu = float(value)


def update_object_material(self, context: bpy.types.Context) -> None:
    """Update an object's HU when its material preset changes."""
    if context is None or context.scene is None:
        return
    apply_material_intensity(self)


class DICOMatorProperties(bpy.types.PropertyGroup):
    """CT-only properties exposed in the DICOMator UI."""

    patient_name: bpy.props.StringProperty(
        name="Patient Name",
        description="Name of the patient",
        default="Anonymous",
    )
    patient_id: bpy.props.StringProperty(
        name="MRN",
        description="Medical Record Number (Patient ID)",
        default="12345678",
    )
    patient_sex: bpy.props.EnumProperty(
        name="Patient Sex",
        description="Patient sex",
        items=[('M', 'Male', ''), ('F', 'Female', ''), ('O', 'Other', '')],
        default='M',
    )
    patient_position: bpy.props.EnumProperty(
        name="Patient Position",
        description="DICOM Patient Position",
        items=[
            ('HFS', 'Head First Supine', ''),
            ('FFS', 'Feet First Supine', ''),
            ('HFP', 'Head First Prone', ''),
            ('FFP', 'Feet First Prone', ''),
            ('HFDR', 'Head First Decubitus Right', ''),
            ('HFDL', 'Head First Decubitus Left', ''),
            ('FFDR', 'Feet First Decubitus Right', ''),
            ('FFDL', 'Feet First Decubitus Left', ''),
        ],
        default='HFS',
    )

    export_4d: bpy.props.BoolProperty(default=False)
    use_timeline_range: bpy.props.BoolProperty(default=True)
    frame_start: bpy.props.IntProperty(default=1, min=1)
    frame_end: bpy.props.IntProperty(default=250, min=1)
    frame_step: bpy.props.IntProperty(default=1, min=1)
    lateral_resolution_mm: bpy.props.FloatProperty(default=2.0, min=0.1, max=10.0)
    axial_resolution_mm: bpy.props.FloatProperty(default=2.0, min=0.1, max=10.0)
    apply_modifiers: bpy.props.BoolProperty(default=True)
    export_directory: bpy.props.StringProperty(subtype='DIR_PATH', default="C:\\Users\\Public\\DICOM_Export")
    series_description: bpy.props.StringProperty(default="CT Series from DICOMator")

    enable_noise: bpy.props.BoolProperty(default=False)
    noise_std_dev_hu: bpy.props.FloatProperty(default=20.0, min=0.0)

    enable_partial_volume: bpy.props.BoolProperty(default=False)
    partial_volume_kernel: bpy.props.IntProperty(default=3, min=1)
    partial_volume_iterations: bpy.props.IntProperty(default=1, min=1)
    partial_volume_mix: bpy.props.FloatProperty(default=1.0, min=0.0, max=1.0)

    enable_metal_artifacts: bpy.props.BoolProperty(default=False)
    metal_intensity: bpy.props.FloatProperty(default=400.0, min=0.0)
    metal_density_threshold: bpy.props.FloatProperty(default=2000.0, min=0.0)
    metal_num_streaks: bpy.props.IntProperty(default=10, min=0)
    metal_falloff: bpy.props.FloatProperty(default=6.0, min=0.1)

    enable_ring_artifacts: bpy.props.BoolProperty(default=False)
    ring_intensity: bpy.props.FloatProperty(default=80.0, min=0.0)
    ring_radius: bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)
    ring_thickness: bpy.props.FloatProperty(default=0.02, min=0.0)
    ring_jitter: bpy.props.FloatProperty(default=0.02, min=0.0)

    enable_motion_artifact: bpy.props.BoolProperty(default=False)
    motion_blur_size: bpy.props.IntProperty(default=9, min=1)
    motion_severity: bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)
    motion_axis: bpy.props.EnumProperty(
        items=[('X', 'X Axis', ''), ('Y', 'Y Axis', '')],
        default='X',
    )

    enable_poiss_
