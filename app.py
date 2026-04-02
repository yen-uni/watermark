import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
from streamlit_cropper import st_cropper

st.set_page_config(page_title="AI 護照編輯器", layout="wide")
st.title("🪪 專業版證件照編輯器 (互動裁切版)")
st.write("先使用拉桿調正頭部，接著直接用滑鼠拖曳、縮放紅框，選取要下載的範圍！")

uploaded_file = st.file_uploader("請選擇原始照片", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 讀取圖片
    img = Image.open(uploaded_file).convert("RGB")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🛠️ 1. 校正頭部傾斜")
        # 現在只需要一個旋轉拉桿，平移和縮放交給滑鼠裁切框
        angle = st.slider("旋轉角度 (調正雙眼)", -45.0, 45.0, 0.0, 0.5)
        
        # --- 旋轉處理 (自動擴展邊界，避免邊角被切掉) ---
        img_np = np.array(img)
        h, w = img_np.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 計算旋轉後的新邊界尺寸
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # 調整旋轉矩陣，將圖片移動到新邊界的中心
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # 執行旋轉，邊緣填滿白色
        rotated_np = cv2.warpAffine(img_np, M, (new_w, new_h), borderValue=(255, 255, 255))
        rotated_img = Image.fromarray(rotated_np)
        
        st.info("💡 提示：旋轉後產生的白色斜邊，請在右側用紅框避開它們。")

    with col2:
        st.subheader("🖼️ 2. 滑鼠框選下載範圍")
        st.write("拖曳紅框中心可平移，拖曳紅框四角可縮放 (比例已鎖定為護照規格)。")
        
        # --- 建立互動裁切框 ---
        # aspect_ratio=(35, 45) 強制鎖定台灣護照的長寬比
        cropped_img = st_cropper(
            rotated_img,
            realtime_update=True,
            box_color='#FF0000',
            aspect_ratio=(35, 45),
            return_type='image'
        )

        # 顯示最終結果與下載按鈕
        if cropped_img:
            st.divider()
            st.subheader("✅ 最終裁切結果")
            st.image(cropped_img, width=250)
            
            buf = io.BytesIO()
            cropped_img.save(buf, format="JPEG", quality=100)
            
            st.download_button(
                label="⬇️ 下載完美證件照", 
                data=buf.getvalue(), 
                file_name="passport_final.jpg", 
                mime="image/jpeg",
                type="primary"
            )
