import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="AI 護照格式自動校正", layout="wide")
st.title("🪪 專業版護照照片自動校正工具")
st.write("上傳歪斜的照片，系統將自動偵測五官、校正水平並調整為護照標準構圖。")

@st.cache_resource
def load_cascades():
    # 使用 OpenCV 內建且絕對穩定的預訓練模型，免除額外安裝套件的麻煩
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    return face_cascade, eye_cascade

def align_and_crop_face(image):
    img_np = np.array(image)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    face_cascade, eye_cascade = load_cascades()

    # 1. 偵測臉部
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    if len(faces) == 0:
        return None, "找不到人臉，請確保照片清晰且光線充足。"
    
    # 取最大的臉，避免背景雜物干擾
    x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
    
    # 2. 為了更精準偵測眼睛，只取臉部上半段作為感興趣區域 (ROI)
    roi_gray = gray[y:int(y+h*0.6), x:x+w]
    eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5)

    rotated_img = img_np
    msg = "成功完成構圖裁切！"

    # 3. 如果找到兩隻以上的眼睛，計算斜率並旋轉
    if len(eyes) >= 2:
        # 依 X 座標排序，區分左右眼
        eyes = sorted(eyes, key=lambda e: e[0])
        left_eye = eyes[0]
        right_eye = eyes[-1]

        # 計算雙眼中心點的絕對座標
        left_center = (x + left_eye[0] + left_eye[2]//2, y + left_eye[1] + left_eye[3]//2)
        right_center = (x + right_eye[0] + right_eye[2]//2, y + right_eye[1] + right_eye[3]//2)

        dY = right_center[1] - left_center[1]
        dX = right_center[0] - left_center[0]
        angle = np.degrees(np.arctan2(dY, dX))

        # 以雙眼中點為軸心旋轉
        eyes_center = ((left_center[0] + right_center[0]) // 2, (left_center[1] + right_center[1]) // 2)
        M = cv2.getRotationMatrix2D(eyes_center, angle, 1)
        
        # 使用白色(255,255,255)填補旋轉後的黑邊，符合護照白底需求
        rotated_img = cv2.warpAffine(img_np, M, (img_np.shape[1], img_np.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))
        msg = "成功校正水平並調整構圖！"

    # 4. 在校正後的圖片上重新定位臉部進行標準裁切
    gray_rot = cv2.cvtColor(rotated_img, cv2.COLOR_RGB2GRAY)
    faces_rot = face_cascade.detectMultiScale(gray_rot, 1.1, 5)
    
    if len(faces_rot) > 0:
        xr, yr, wr, hr = max(faces_rot, key=lambda rect: rect[2] * rect[3])
        center_x = xr + wr // 2
        center_y = yr + hr // 2
        
        # 護照標準：頭部佔比要大，比例約為 35:45
        crop_h = int(hr * 1.9)
        crop_w = int(crop_h * 0.77)
        
        x1 = max(0, center_x - crop_w // 2)
        y1 = max(0, center_y - int(crop_h * 0.5)) # 往上留白給頭頂空間
        x2 = min(rotated_img.shape[1], x1 + crop_w)
        y2 = min(rotated_img.shape[0], y1 + crop_h)
        
        final_img = rotated_img[y1:y2, x1:x2]
        return final_img, msg
        
    return rotated_img, "已完成水平校正。"

uploaded_file = st.file_uploader("選擇您的原始照片", type=["jpg", "jpeg", "png"])

if uploaded_file:
    col1, col2 = st.columns(2)
    img = Image.open(uploaded_file).convert("RGB")
    
    with col1:
        st.subheader("原始照片")
        st.image(img, use_container_width=True)

    with st.spinner("AI 正在分析並校正中..."):
        processed_np, result_msg = align_and_crop_face(img)
        
        if processed_np is not None:
            processed_img = Image.fromarray(processed_np)
            with col2:
                st.subheader("校正後結果")
                st.image(processed_img, use_container_width=True)
                st.success(result_msg)
                
                buf = io.BytesIO()
                processed_img.save(buf, format="JPEG", quality=95)
                st.download_button("⬇️ 下載護照規格照片", buf.getvalue(), "passport_photo.jpg", "image/jpeg")
        else:
            st.error(result_msg)
