"""
CT-only constants and optional dependencies for the DICOMator research pipeline.

Derived from DICOMator by Michael Douglass (MIT License).
"""

from __future__ import annotations

import importlib
import importlib.util
import logging

# -----------------------------
# CT HU CONSTANTS
# -----------------------------

AIR_DENSITY = -1000.0   # HU value for air (DICOM standard)
DEFAULT_DENSITY = 0.0   # Default HU for objects unless overridden
MAX_HU_VALUE = 3071     # Max HU for 12-bit CT
MIN_HU_VALUE = -1024    # Min HU for CT

MODALITY_CT = "CT"      # Explicitly fixed modality


# -----------------------------
# CT MATERIAL / TISSUE PRESETS
# -----------------------------

CT_MATERIAL_HU = {
    "AIR": -1000,
    "CORTICAL_BONE": 1100,
    "TRABECULAR_BONE": 200,
    "FAT": -75,
    "MUSCLE": 50,
    "LIVER": 50,
    "SPLEEN": 50,
    "KIDNEY_CORTEX": 40,
    "KIDNEY_MEDULLA": 40,
    "CARTILAGE": 200,
    "BLOOD_ACUTE": 60,
    "WHITE_MATTER": 25,
    "GRAY_MATTER": 40,
    "CSF_WATER": 0,
    "LUNG": -700,
    "SOFT_TISSUE": 40,
    "ALUMINIUM": 300,
    "TITANIUM": 3000,
}

MATERIAL_ITEMS = [
    ("CUSTOM", "Custom", "Manually specify a CT HU value"),
    ("AIR", "Air", "Air / vacuum"),
    ("CORTICAL_BONE", "Cortical Bone / Calcification", "Very dense bone"),
    ("TRABECULAR_BONE", "Trabecular Bone", "Cancellous bone"),
    ("FAT", "Fat", "Adipose tissue"),
    ("MUSCLE", "Muscle", "Skeletal muscle"),
    ("LIVER", "Liver", "Liver parenchyma"),
    ("SPLEEN", "Spleen", "Splenic tissue"),
    ("KIDNEY_CORTEX", "Kidney Cortex", "Renal cortex"),
    ("KIDNEY_MEDULLA", "Kidney Medulla", "Renal medulla"),
    ("CARTILAGE", "Cartilage", "Cartilage tissue"),
    ("BLOOD_ACUTE", "Blood (acute)", "Acute blood"),
    ("WHITE_MATTER", "White Matter", "Cerebral white matter"),
    ("GRAY_MATTER", "Gray Matter", "Cerebral gray matter"),
    ("CSF_WATER", "CSF / Water", "Fluid"),
    ("LUNG", "Lung Parenchyma", "Aerated lung"),
    ("SOFT_TISSUE", "Soft Tissue", "Generic soft tissue"),
    ("ALUMINIUM", "Aluminium", "Moderately dense metal"),
    ("TITANIUM", "Titanium", "High-density metal implant"),
]


def get_ct_intensity(material_key: str) -> float | None:
    """
    Return the CT HU value for a given material key.
    """
    return CT_MATERIAL_HU.get(material_key)


# -----------------------------
# OPTIONAL PYDICOM DEPENDENCY
# -----------------------------

PYDICOM_AVAILABLE = False
Dataset = None
FileDataset = None
generate_uid = None
pydicom = None

try:
    if importlib.util.find_spec("pydicom") is not None:
        pydicom = importlib.import_module("pydicom")
        from pydicom.dataset import Dataset, FileDataset
        from pydicom.uid import generate_uid
        PYDICOM_AVAILABLE = True
except Exception:
    logging.getLogger(__name__).warning(
        "pydicom not available. DICOM export functionality will be disabled."
    )
    pydicom = None
    Dataset = None
    FileDataset = None
    generate_uid = None


__all__ = [
    "AIR_DENSITY",
    "DEFAULT_DENSITY",
    "MAX_HU_VALUE",
    "MIN_HU_VALUE",
    "MODALITY_CT",
    "CT_MATERIAL_HU",
    "MATERIAL_ITEMS",
    "get_ct_intensity",
    "PYDICOM_AVAILABLE",
    "Dataset",
    "FileDataset",
    "generate_uid",
    "pydicom",
]


