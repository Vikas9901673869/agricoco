from ultralytics import YOLO
import streamlit as st


@st.cache_resource
def load_model(model_path):
    """
    Loads a YOLO object detection model from the specified model_path.

    Parameters:
        model_path (str or Path): Path to the YOLO weight file (.pt).

    Returns:
        YOLO: A loaded Ultralytics YOLO model instance.
    """
    model = YOLO(str(model_path))
    return model