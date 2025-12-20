"""
CT DICOM export helpers (Blender-independent).

Derived from DICOMator by Michael Douglass (MIT License).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Callable, Optional, Sequence, Tuple

import numpy as np

from .constants import (
    AIR_DENSITY,
    DEFAULT_DENSITY,
    MAX_HU_VALUE,
    MIN_HU_VALUE,
    Dataset,
    FileDataset,
    PYDICOM_AVAILABLE,
    generate_uid,
    pydicom,
)

SliceProgressCallback = Optional[Callable[[int, int], None]]


def export_voxel_grid_to_dicom(
    voxel_grid: np.ndarray,
    voxel_size: Sequence[float] | float,
    output_dir: str,
    bbox_min: Tuple[float, float, float],
    *,
    patient_name: str = "Anonymous",
    patient_id: str = "12345678",
    patient_sex: str = "M",
    series_description: str = "Synthetic CT Series",
    progress_callback: SliceProgressCallback = None,
    direct_hu: bool = False,
    patient_position: str = "HFS",
    study_instance_uid: Optional[str] = None,
    frame_of_reference_uid: Optional[str] = None,
    series_instance_uid: Optional[str] = None,
    series_number: int = 1,
    phase_index: Optional[int] = None,
) -> dict[str, str]:
    """
    Export a 3D voxel grid to a folder of CT DICOM slices.

    Parameters
    ----------
    voxel_grid : np.ndarray
        3D array of voxel values or HU.
    voxel_size : float or (x, y, z)
        Voxel spacing in meters.
    bbox_min : (x, y, z)
        Minimum bounding-box corner in meters.
    """

    if not PYDICOM_AVAILABLE or pydicom is None:
        return {"error": "pydicom not available"}

    os.makedirs(output_dir, exist_ok=True)

    # -----------------------------
    # Time metadata
    # -----------------------------
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S.%f")

    # -----------------------------
    # HU handling
    # -----------------------------
    if direct_hu:
        hu_grid = np.array(voxel_grid, dtype=np.int16, copy=False)
    else:
        hu_grid = np.where(
            voxel_grid > 0,
            DEFAULT_DENSITY,
            AIR_DENSITY
        ).astype(np.int16, copy=False)

    hu_grid = np.clip(hu_grid, MIN_HU_VALUE, MAX_HU_VALUE)

    num_slices = hu_grid.shape[2]

    # -----------------------------
    # Voxel spacing (meters → mm)
    # -----------------------------
    if isinstance(voxel_size, Sequence) and len(voxel_size) == 3:
        vx_m, vy_m, vz_m = map(float, voxel_size)
    else:
        vx_m = vy_m = vz_m = float(voxel_size)

    vx_mm, vy_mm, vz_mm = vx_m * 1000.0, vy_m * 1000.0, vz_m * 1000.0
    bbox_min_mm = tuple(coord * 1000.0 for coord in bbox_min)

    # -----------------------------
    # UIDs
    # -----------------------------
    study_instance_uid = study_instance_uid or generate_uid()
    frame_of_reference_uid = frame_of_reference_uid or generate_uid()
    series_instance_uid = series_instance_uid or generate_uid()

    # -----------------------------
    # Slice loop
    # -----------------------------
    for index in range(num_slices):
        slice_data = hu_grid[:, :, index]

        try:
            file_meta = Dataset()
            file_meta.MediaStorageSOPClassUID = pydicom.uid.CTImageStorage
            file_meta.MediaStorageSOPInstanceUID = generate_uid()
            file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
            file_meta.ImplementationClassUID = pydicom.uid.PYDICOM_IMPLEMENTATION_UID

            dataset = FileDataset(
                None, {}, file_meta=file_meta, preamble=b"\0" * 128
            )

            # -----------------------------
            # Patient & study info
            # -----------------------------
            dataset.PatientName = patient_name
            dataset.PatientID = patient_id
            dataset.PatientSex = patient_sex
            dataset.PatientPosition = patient_position

            dataset.StudyInstanceUID = study_instance_uid
            dataset.FrameOfReferenceUID = frame_of_reference_uid
            dataset.SeriesInstanceUID = series_instance_uid

            dataset.StudyDate = date_str
            dataset.StudyTime = time_str
            dataset.SeriesDate = date_str
            dataset.SeriesTime = time_str
            dataset.ContentDate = date_str
            dataset.ContentTime = time_str

            dataset.Modality = "CT"
            dataset.SeriesNumber = series_number
            dataset.SeriesDescription = series_description
            dataset.Manufacturer = "DICOMator"
            dataset.InstitutionName = "Virtual Hospital"

            dataset.InstanceNumber = index + 1
            dataset.AcquisitionNumber = int(phase_index or 1)

            # -----------------------------
            # Geometry
            # -----------------------------
            dataset.ImagePositionPatient = [
                bbox_min_mm[0],
                bbox_min_mm[1],
                bbox_min_mm[2] + index * vz_mm,
            ]

            dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
            dataset.SliceThickness = vz_mm
            dataset.SpacingBetweenSlices = vz_mm
            dataset.SliceLocation = bbox_min_mm[2] + index * vz_mm

            # -----------------------------
            # Pixel data
            # -----------------------------
            pixel_array = slice_data.T.astype(np.int16, copy=False)
            rows, cols = pixel_array.shape

            dataset.Rows = rows
            dataset.Columns = cols
            dataset.PixelSpacing = [vy_mm, vx_mm]
            dataset.SamplesPerPixel = 1
            dataset.PhotometricInterpretation = "MONOCHROME2"
            dataset.BitsAllocated = 16
            dataset.BitsStored = 16
            dataset.HighBit = 15
            dataset.PixelRepresentation = 1

            dataset.RescaleIntercept = 0
            dataset.RescaleSlope = 1
            dataset.WindowCenter = 40
            dataset.WindowWidth = 400

            dataset.PixelData = pixel_array.tobytes()

            filename = os.path.join(
                output_dir, f"CT_Slice_{index + 1:04d}.dcm"
            )

            dataset.is_little_endian = True
            dataset.is_implicit_VR = False
            dataset.save_as(filename)

            if progress_callback:
                progress_callback(index + 1, num_slices)

        except Exception as exc:
            return {
                "error": f"Error saving slice {index + 1}: {exc}"
            }

    return {
        "success": f"Exported {num_slices} CT slices to {output_dir}"
    }


__all__ = ["export_voxel_grid_to_dicom"]


