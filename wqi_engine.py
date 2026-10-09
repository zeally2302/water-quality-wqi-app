# wqi_engine.py
import requests

def calculate_wqi(p_h, turbidity, tds, iron, manganese):
    """คำนวณค่า WQI 5 พารามิเตอร์ อ้างอิงมาตรฐานกรมอนามัย"""
    s_ph_lower, s_ph_upper = 6.5, 8.5
    s_turbidity, s_tds = 5.0, 1000.0
    s_iron, s_manganese = 0.5, 0.3
    w_ph, w_turbidity, w_tds, w_iron, w_manganese = 1/8.5, 1/5.0, 1/1000.0, 1/0.5, 1/0.3
    sum_weights = w_ph + w_turbidity + w_tds + w_iron + w_manganese
    if p_h >= 7.0:
        q_ph = ((p_h - 7.0) / (s_ph_upper - 7.0)) * 100
    else:
        q_ph = ((7.0 - p_h) / (7.0 - s_ph_lower)) * 100
    q_turbidity = (turbidity / s_turbidity) * 100
    q_tds = (tds / s_tds) * 100
    q_iron = (iron / s_iron) * 100
    q_manganese = (manganese / s_manganese) * 100
    sum_wn_qn = (q_ph*w_ph) + (q_turbidity*w_turbidity) + (q_tds*w_tds) + (q_iron*w_iron) + (q_manganese*w_manganese)
    wqi = sum_wn_qn / sum_weights
    if 0 <= wqi <= 25: status, color = "ดีมาก (Excellent)", "green"
    elif 26 <= wqi <= 50: status, color = "ดี (Good)", "blue"
    elif 51 <= wqi <= 75: status, color = "พอใช้/เริ่มเสื่อมโทรม (Poor)", "orange"
    else: status, color = "วิกฤต/เสื่อมโทรมมาก (Very Poor)", "red"
    return round(wqi, 2), status, color

def calculate_treatment_chemicals(turbidity, p_h, water_volume):
    """ระบบคำนวณสารเคมี 3 ชนิด (Alum, Lime, Chlorine)"""
    if turbidity <= 5: base_alum = 10.0
    elif 5 < turbidity <= 20: base_alum = 10.0 + (turbidity - 5) * 0.8
    elif 20 < turbidity <= 50: base_alum = 22.0 + (turbidity - 20) * 1.2
    else: base_alum = 58.0 + (turbidity - 50) * 1.5
    if p_h < 6.5:
        base_lime = 5.0 + (6.5 - p_h) * 10.0
        lime_status = "⚠️ น้ำดิบเป็นกรด: ต้องเติมปูนขาวเพื่อช่วยเร่งการตกตะกอน"
    elif 6.5 <= p_h <= 7.5:
        base_lime = 2.0
        lime_status = "✅ pH ปกติ: เติมปูนขาวในปริมาณต่ำเพื่อประคองความด่าง"
    else:
        base_lime = 0.0
        lime_status = "ℹ️ น้ำดิบเป็นด่าง: งดเติมปูนขาว (เฝ้าระวังตะกรัน)"
    if turbidity > 30: base_chlorine = 2.5
    else: base_chlorine = 1.5
    alum_per_hour = base_alum * water_volume
    lime_per_hour = base_lime * water_volume
    chlorine_per_hour = base_chlorine * water_volume
    return {
        "alum_mg_l": round(base_alum, 2), "alum_g_hr": round(alum_per_hour, 2),
        "lime_mg_l": round(base_lime, 2), "lime_g_hr": round(lime_per_hour, 2), "lime_status": lime_status,
        "chlorine_mg_l": round(base_chlorine, 2), "chlorine_g_hr": round(chlorine_per_hour, 2)
    }

# wqi_engine.py - ปรับปรุงเฉพาะฟังก์ชันส่ง Telegram ตัวล่างสุด

def send_telegram_notify(bot_token, chat_id, message):
    """ฟังก์ชันส่งข้อความผ่าน Telegram บอท (เวอร์ชันยิงตรงเข้า API แน่นอน 100%)"""
    token_clean = bot_token.strip()
    chat_id_clean = chat_id.strip()
    
    # ยิงตรงเข้า Endpoint มาตรฐานของ Telegram API โดยใช้ตัวแปรดิบที่คุณกรอกหน้าเว็บ
    url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
    payload = {
        "chat_id": chat_id_clean,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=7)
        if response.status_code == 200:
            return True, "สำเร็จ"
        else:
            try:
                res_data = response.json()
                error_desc = res_data.get("description", "ไม่ทราบสาเหตุ")
            except:
                error_desc = "รหัสเซิร์ฟเวอร์ปฏิเสธการเชื่อมต่อ"
            return False, f"Telegram API Error: {error_desc} (Code: {response.status_code})"
    except Exception as e:
        return False, f"Network Error: ตรวจสอบอินเทอร์เน็ตของเครื่องคอมพิวเตอร์ ({str(e)})"
