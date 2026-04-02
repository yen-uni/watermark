import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
# 🛠️ 關鍵修正：精確指定引入路徑，解決找不到 solutions 的問題
from mediapipe.python.solutions import face_mesh as mp_face_mesh
from PIL import Image
import io

# 初始化 MediaPipe 人臉偵測
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)

st.set_page_config(page_title="AI 護照格式自動校正", layout="wide")
st.title("🪪 AI 護照照片自動校正工具")
st.write("上傳歪斜的照片，AI 將自動對準雙眼、校正水平並調整構圖。")

def align_and_crop_face(image):
    # 轉換 PIL 到 OpenCV 格式
    img_np = np.array(image)
    h, w, _ = img_np.shape
    rgb_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # 1. 偵測臉部特徵點
    results = face_mesh.process(cv2.cvtColor(rgb_img, cv2.COLOR_BGR2RGB))
    
    if not results.multi_face_landmarks:
        return None, "找不到人臉，請確保照片清晰且光線充足。"

    landmarks = results.multi_face_landmarks[0].landmark
    
    # 2. 取得左右眼中心座標 (MediaPipe 特徵點索引)
    # 左眼: 33, 右眼: 263
    left_eye = (landmarks[33].x * w, landmarks[33].y * h)
    right_eye = (landmarks[263].x * w, landmarks[263].y * h)

    # 3. 計算旋轉角度
    dY = right_eye[1] - left_eye[1]
    dX = right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dY, dX))

    # 4. 執行旋轉校正
    eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
    M = cv2.getRotationMatrix2D(eye_center, angle, 1)
    rotated = cv2.warpAffine(img_np, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))

    # 5. 在旋轉後的圖中再次偵測臉部以進行精準裁切
    results_rotated = face_mesh.process(cv2.cvtColor(rotated, cv2.COLOR_RGB2BGR))
    if results_rotated.multi_face_landmarks:
        lms = results_rotated.multi_face_landmarks[0].landmark
        # 取得臉部範圍
        x_coords = [lm.x * w for lm in lms]
        y_coords = [lm.y * h for lm in lms]
        
        face_w = max(x_coords) - min(x_coords)
        face_h = max(y_coords) - min(y_coords)
        
        # 定義裁切中心與範圍 (預留頭頂與肩膀空間)
        center_x = int(sum(x_coords) / len(lms))
        center_y = int(sum(y_coords) / len(lms))
        
        # 護照標準：頭部約佔高度的 70-80%
        crop_h = int(face_h * 2.0)
        crop_w = int(crop_h * 0.77) # 接近 35:45 比例
        
        x1 = max(0, center_x - crop_w // 2)
        y1 = max(0, center_y - int(crop_h * 0.55)) # 稍微往上偏，留出頭頂空間
        x2 = min(w, x1 + crop_w)
        y2 = min(h, y1 + crop_h)
        
        final_img = rotated[y1:y2, x1:x2]
        return final_img, "成功校正水平並調整構圖！"

    return rotated, "已校正水平，但無法執行進階裁切。"

uploaded_file = st.file_uploader("選擇您的原始照片", type=["jpg", "jpeg", "png"])

if uploaded_file:
    col1, col2 = st.columns(2)
    img = Image.open(uploaded_file).convert("RGB")
    
    with col1:
        st.subheader("原始照片")
        st.image(img, use_container_width=True)

    with st.spinner("AI 正在分析並校正中..."):
        processed_np, msg = align_and_crop_face(img)
        
        if processed_np is not None:
            processed_img = Image.fromarray(processed_np)
            with col2:
                st.subheader("校正後結果")
                st.image(processed_img, use_container_width=True)
                st.success(msg)
                
                # 下載按鈕
                buf = io.BytesIO()
                processed_img.save(buf, format="JPEG", quality=95)
                st.download_button("⬇️ 下載護照規格照片", buf.getvalue(), "passport_photo.jpg", "image/jpeg")
        else:
            st.error(msg)
