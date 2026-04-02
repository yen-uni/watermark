import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io

# 設定網頁標題與寬度
st.set_page_config(page_title="AI 魔術橡皮擦", layout="wide")
st.title("🪄 簡易圖片修復與浮水印去除工具")
st.write("上傳您的圖片，用筆刷塗抹想要去除的浮水印或瑕疵，然後點擊處理！")

# 側邊欄設定
st.sidebar.header("筆刷設定")
stroke_width = st.sidebar.slider("筆刷粗細", 5, 50, 20)

# 上傳圖片區塊
uploaded_file = st.file_uploader("請選擇一張圖片 (支援 JPG, PNG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 讀取並顯示圖片
    image = Image.open(uploaded_file).convert("RGB")
    
    # 為了避免圖片過大導致網頁卡頓，稍微縮放圖片以適應畫布
    max_width = 800
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height))

    st.subheader("1. 請在下方圖片上塗抹要去除的區域")
    
    # 建立可繪圖的畫布
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",  # 內部填充透明
        stroke_width=stroke_width,
        stroke_color="#FF0000", # 使用醒目的紅色筆刷
        background_image=image,
        update_streamlit=True,
        height=image.height,
        width=image.width,
        drawing_mode="freedraw",
        key="canvas",
    )

    # 當使用者畫了東西並點擊處理按鈕
    if st.button("✨ 執行移除處理", type="primary"):
        if canvas_result.image_data is not None:
            # 將 PIL 圖片轉換為 OpenCV 格式 (NumPy array)
            img_array = np.array(image)
            # OpenCV 預設是 BGR，但 Streamlit/PIL 是 RGB，我們先保持 RGB 處理
            
            # 從畫布結果提取遮罩 (Mask)
            # canvas_result.image_data 是一個 RGBA 陣列，我們提取 Alpha 通道作為遮罩
            mask = canvas_result.image_data[:, :, 3].astype(np.uint8)

            # 檢查是否有塗抹
            if np.sum(mask) == 0:
                st.warning("您似乎還沒有塗抹任何區域喔！請先用筆刷畫出想去除的地方。")
            else:
                with st.spinner('影像修復處理中，請稍候...'):
                    # 使用 OpenCV 的 inpaint 功能進行修復
                    # cv2.INPAINT_TELEA 是其中一種修復演算法
                    restored_img_array = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)

                    # 將處理後的陣列轉回 PIL 圖片
                    restored_image = Image.fromarray(restored_img_array)

                    st.success("處理完成！")
                    
                    # 顯示處理後的結果
                    st.subheader("2. 處理結果")
                    st.image(restored_image, caption="修復後的圖片", use_container_width=False)

                    # 準備下載按鈕
                    buf = io.BytesIO()
                    restored_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()

                    st.download_button(
                        label="⬇️ 下載圖片",
                        data=byte_im,
                        file_name="cleaned_image.png",
                        mime="image/png"
                    )
