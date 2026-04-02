# 建立畫布
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=stroke_width,
        stroke_color="#FF0000",
        # 【核心修正】：不要用 background_image_url，直接把 Base64 字串傳給 background_image
        background_image=bg_image_url, 
        update_streamlit=True,
        height=original_image.height,
        width=original_image.width,
        drawing_mode="freedraw",
        key="canvas",
    )
