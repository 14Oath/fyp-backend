import os
import cv2
from face_embedding import get_embedding_from_image
from face_recognition import FaceVerifier

# Path to your dataset
DATASET_PATH = "evaluation_dataset"
THRESHOLD = 0.7

verifier = FaceVerifier()

true_positives = 0
false_positives = 0
false_negatives = 0
true_negatives = 0

# Evaluate genuine matches
for student_id in os.listdir(DATASET_PATH):
    student_path = os.path.join(DATASET_PATH, student_id)
    if student_id == "impostors" or not os.path.isdir(student_path):
        continue

    for test_image in os.listdir(student_path):
        if test_image == "reg.jpg":
            continue

        img_path = os.path.join(student_path, test_image)
        img = cv2.imread(img_path)
        emb = get_embedding_from_image(img)
        if emb is None:
            continue

        matched_id = verifier.verify_face(emb, threshold=THRESHOLD)
        if matched_id == student_id:
            true_positives += 1
        else:
            false_negatives += 1
        print(f"Expected: {student_id}, Predicted: {matched_id}")

# Evaluate impostors
impostor_path = os.path.join(DATASET_PATH, "impostors")
for img_name in os.listdir(impostor_path):
    img_path = os.path.join(impostor_path, img_name)
    img = cv2.imread(img_path)
    emb = get_embedding_from_image(img)
    if emb is None:
        continue

    matched_id = verifier.verify_face(emb, threshold=THRESHOLD)
    if matched_id:
        false_positives += 1
        print(f"Impostor {img_name} incorrectly matched with {matched_id}")
    else:
        true_negatives += 1

verifier.close()

# Calculate metrics
total = true_positives + false_negatives + false_positives + true_negatives
accuracy = (true_positives + true_negatives) / total
precision = true_positives / (true_positives + false_positives + 1e-6)
recall = true_positives / (true_positives + false_negatives + 1e-6)
f1 = 2 * (precision * recall) / (precision + recall + 1e-6)

print("\n--- Evaluation Results ---")
print(f"✅ True Positives: {true_positives}")
print(f"❌ False Negatives: {false_negatives}")
print(f"🚫 False Positives: {false_positives}")
print(f"✔️ True Negatives: {true_negatives}")
print(f"\n📊 Accuracy: {accuracy:.2%}")
print(f"🎯 Precision: {precision:.2%}")
print(f"📥 Recall: {recall:.2%}")
print(f"📈 F1 Score: {f1:.2%}")
