import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io

st.set_page_config(page_title="AI 護照編輯器", layout="wide")
st.title("🪪 專業版證件照編輯器 (無敵穩定版)")
st.write("無懼雲端環境報錯！使用下方滑桿即時微調，將照片對齊輔助線，即可無痛生成完美護照照片。")

uploaded_file = st.file_uploader("請選擇原始照片", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 讀取圖片
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)
    h, w, _ = img_np.shape

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🛠️ 影像微調控制台")
        angle = st.slider("1. 旋轉角度 (調正雙眼)", -45.0, 45.0, 0.0, 0.5)
        zoom = st.slider("2. 縮放比例 (調整頭部大小)", 0.2, 3.0, 1.0, 0.05)
        offset_x = st.slider("3. 左右平移", -w, w, 0, 5)
        offset_y = st.slider("4. 上下平移 (控制頭頂留白)", -h, h, 0, 5)
        
        show_guide = st.checkbox("顯示對齊輔助線", value=True)

    # 護照標準輸出尺寸 (35mm x 45mm 比例，我們放大像素以保持高畫質)
    out_w, out_h = 700, 900 
    
    # 計算旋轉與縮放矩陣
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, zoom)
    
    # 將圖片中心對齊到輸出畫布的中心，並加上使用者的平移設定
    M[0, 2] += (out_w / 2 - center[0]) + offset_x
    M[1, 2] += (out_h / 2 - center[1]) + offset_y

    # 執行影像轉換 (預設用純白背景填補邊緣)
    final_img_np = cv2.warpAffine(img_np, M, (out_w, out_h), borderValue=(255, 255, 255))
    
    # 建立預覽圖 (用來畫輔助線，不影響最終下載的圖)
    preview_np = final_img_np.copy()
    
    if show_guide:
        # 畫中心垂直線
        cv2.line(preview_np, (out_w//2, 0), (out_w//2, out_h), (0, 255, 0), 2)
        # 畫雙眼水平基準線 (約在照片高度 45% 處)
        eye_y = int(out_h * 0.45)
        cv2.line(preview_np, (0, eye_y), (out_w, eye_y), (0, 255, 0), 2)
        st.markdown("<p style='color:green; font-size:14px;'>* 提示：請將雙眼對齊水平綠線，鼻樑對齊垂直綠線</p>", unsafe_allow_html=True)

    with col2:
        st.subheader("✅ 即時預覽 (35x45 護照比例)")
        st.image(preview_np, use_container_width=False, width=400)
        
        # 準備下載用的無輔助線圖片
        final_img_pil = Image.fromarray(final_img_np)
        buf = io.BytesIO()
        final_img_pil.save(buf, format="JPEG", quality=95)
        
        st.download_button(
            label="⬇️ 下載符合規定的護照照片", 
            data=buf.getvalue(), 
            file_name="passport_photo.jpg", 
            mime="image/jpeg",
            type="primary"
        )
