import streamlit as st
import requests
from PIL import Image, ImageEnhance, ImageDraw
import io
import numpy as np
import cv2
from streamlit_cropper import st_cropper

# --- 0. 系統安全鎖 (防路人攻擊) ---
st.set_page_config(page_title="居留證大頭照與列印排版系統", layout="centered")

if 'processed_photo' not in st.session_state:
    st.session_state['processed_photo'] = None
if 'final_4x6_image' not in st.session_state:
    st.session_state['final_4x6_image'] = None

app_password = st.sidebar.text_input("請輸入內部密碼解鎖系統", type="password")

if app_password != "@unipro":
    st.warning("🔒 這是環久內部專用系統，請在左側輸入正確密碼以解鎖功能。擅自盜用必將追究")
    st.stop()

# --- 1. 配置區域 (恢復最安全的 st.secrets 做法) ---
try:
    # 讓 Streamlit 從雲端安全金庫讀取 Key，程式碼中不再出現明碼
    REMOVEBG_API_KEY = st.secrets["REMOVEBG_API_KEY"]
except:
    REMOVEBG_API_KEY = ""

TARGET_WIDTH_PX = 413
TARGET_HEIGHT_PX = 531
CANVAS_WIDTH = 1800
CANVAS_HEIGHT = 1200

st.title("🇹🇼 環久大頭照證件照極速與列印系統V10.2")
st.info(
    "功能：生成標準大頭照，並自動排版為 4x6 吋列印檔。\n\n"
    "**操作步驟:**\n"
    "1. 調正頭部與框選範圍 -> 2. 調亮度去背 (可核對輔助線) -> 3. 選擇排版下載列印檔。\n"
)

def generate_4x6_layout(single_photo, layout_type):
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "WHITE")
    
    if layout_type == "2inch":
        photo_w, photo_h = single_photo.size 
        margin_x = 30
        margin_y = 49 
        gap_x = 30
        gap_y = 40
        for row in range(2):
            for col in range(4):
                x = margin_x + col * (photo_w + gap_x)
                y = margin_y + row * (photo_h + gap_y)
                canvas.paste(single_photo, (x, y))
                
    elif layout_type == "1inch":
        target_1inch_w = 295
        target_1inch_h = 413
        photo_1inch = single_photo.resize((target_1inch_w, target_1inch_h), Image.Resampling.LANCZOS)
        photo_w, photo_h = photo_1inch.size
        margin_x = 83
        margin_y = 147 
        gap_x = 40
        gap_y = 80
        for row in range(2):
            for col in range(5):
                x = margin_x + col * (photo_w + gap_x)
                y = margin_y + row * (photo_h + gap_y)
                canvas.paste(photo_1inch, (x, y))

    return canvas

uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    img_raw = Image.open(uploaded_file)
    if img_raw.mode in ('RGBA', 'LA') or (img_raw.mode == 'P' and 'transparency' in img_raw.info):
        bg = Image.new('RGB', img_raw.size, (255, 255, 255))
        bg.paste(img_raw, (0, 0), img_raw.convert('RGBA'))
        original_image = bg
    else:
        original_image = img_raw.convert('RGB')
    
    st.write("### ✂️ 第一步：校正頭部傾斜與框選範圍")
    st.warning("💡 **請務必先拉動下方滑桿將頭部轉正，轉正後再畫紅框裁切。**")
    
    angle = st.slider("🔄 旋轉角度 (若頭部歪斜，請先微調此拉桿調正)", -30.0, 30.0, 0.0, 0.5)
    
    img_np = np.array(original_image)
    h, w = img_np.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    rotated_np = cv2.warpAffine(img_np, M, (new_w, new_h), borderValue=(255, 255, 255))
    rotated_image = Image.fromarray(rotated_np)

    st.write("請拖拉紅色框線，圈選最大頭部比例（請將肩膀切在框外）：")

    dynamic_key = f"main_cropper_{angle}"
    
    cropped_image = st_cropper(
        rotated_image, 
        aspect_ratio=(35, 45), 
        box_color='#FF0000',
        return_type='image',
        key=dynamic_key 
    )

    st.write("### ☀️ 第二步：調整亮度與核對頭部比例")
    
    brightness = st.slider("調整照片亮度", 0.5, 2.0, 1.1, 0.1)
    enhancer = ImageEnhance.Brightness(cropped_image)
    final_preview = enhancer.enhance(brightness)

    def add_passport_guidelines(img):
        guide_img = img.copy()
        draw = ImageDraw.Draw(guide_img)
        w, h = guide_img.size
        
        top_margin = int(h * (0.4 / 4.5)) 
        max_h = int(h * (3.6 / 4.5))
        max_w = int(w * 0.72) 
        max_x0 = (w - max_w) // 2
        draw.ellipse([max_x0, top_margin, max_x0 + max_w, top_margin + max_h], outline="red", width=3)
        
        min_h = int(h * (3.2 / 4.5))
        min_w = int(w * 0.62)
        min_x0 = (w - min_w) // 2
        draw.ellipse([min_x0, top_margin, min_x0 + min_w, top_margin + min_h], outline="#00FF00", width=3)
        
        center_x = w // 2
        for y in range(0, h, 10):
            draw.line([(center_x, y), (center_x, y+5)], fill="gray", width=1)
            
        return guide_img

    col_preview, col_action = st.columns([1, 1])
    
    with col_preview:
        show_guide = st.checkbox("👁️ 顯示護照頭圍輔助線", value=True)
        display_img = add_passport_guidelines(final_preview) if show_guide else final_preview
        
        st.image(display_img, caption="最終範圍與亮度預覽", width=250)
        
        if show_guide:
            st.markdown(
