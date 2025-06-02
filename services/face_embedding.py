import torch
import numpy as np
import cv2
from PIL import Image
from mtcnn import MTCNN
from face_embedding import get_embedding_from_image
from inception_resnet_v1 import InceptionResnetV1

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load face detection and recognition models
mtcnn = MTCNN(device=device)
facenet = InceptionResnetV1(pretrained='vggFace2', classify=False).eval().to(device)

# Extract embedding from image file path
def get_embedding(image_path: str):
    img = Image.open(image_path).convert("RGB")
    face = mtcnn(img)
    if face is None:
        return None
    face = face.unsqueeze(0).to(device)
    with torch.no_grad():
        emb = facenet(face).squeeze(0).cpu().numpy()
    return emb

# Extract embedding from OpenCV image array
def get_embedding_from_image(cv2_img: np.ndarray):
    # Convert OpenCV BGR image to PIL RGB image
    img = Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))
    face = mtcnn(img)
    if face is None:
        return None
    face = face.unsqueeze(0).to(device)
    with torch.no_grad():
        emb = facenet(face).squeeze(0).cpu().numpy()
    return emb