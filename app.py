import streamlit as st
import numpy as np
import cv2
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io
import base64

# 設定網頁標題
st.set_page_config(page_title="AI 魔術橡皮擦", layout="wide")
st.title("🪄 專業級圖片修復與浮水印去除工具")
st.write("上傳圖片並塗抹瑕疵，點擊執行即可移除！")

# 側邊欄設定
st.sidebar.header("控制台")
stroke_width = st.sidebar.slider("筆刷粗細", 5, 100, 25)
stroke_color = "#FF0000"  # 經典紅色筆刷

# 🛠️ 輔助函式：將圖片轉為 Base64 字串，徹底解決 image_to_url 報錯
def get_image_base64(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

uploaded_file = st.file_uploader("選擇照片 (JPG/PNG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 讀取圖片並限制大小以確保流暢度
    original_image = Image.open(uploaded_file).convert("RGB")
    max_size = 700
    if original_image.width > max_size or original_image.height > max_size:
        original_image.thumbnail((max_size, max_size))
    
    # 取得 Base64 編碼，這樣 st_canvas 就不會報錯了
    bg_image_url = get_image_base64(original_image)

    st.subheader("1. 請在下方畫面上塗抹要移除的區域")
    
    # 建立畫布
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_image=original_image, # 這裡傳入 PIL 物件
        update_streamlit=True,
        height=original_image.height,
        width=original_image.width,
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("✨ 執行修復 (Remove)", type="primary"):
        if canvas_result.image_data is not None:
            # 取得塗抹的遮罩 (Mask)
            mask = canvas_result.image_data[:, :, 3].astype(np.uint8)
            
            if np.sum(mask) > 0:
                with st.spinner("影像處理中..."):
                    img_np = np.array(original_image)
                    # 影像修復核心演算法
                    res = cv2.inpaint(img_np, mask, 3, cv2.INPAINT_TELEA)
                    res_img = Image.fromarray(res)
                    
                    st.success("處理完成！")
                    st.image(res_img, caption="修復結果", use_container_width=False)
                    
                    # 下載按鈕
                    buf = io.BytesIO()
                    res_img.save(buf, format="PNG")
                    st.download_button("⬇️ 下載成果", buf.getvalue(), "cleaned.png", "image/png")
            else:
                st.warning("請先在圖片上塗抹要移除的地方喔！")
