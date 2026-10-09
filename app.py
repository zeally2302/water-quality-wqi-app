# app.py
import streamlit as st
import pandas as pd
import numpy as np
from wqi_engine import calculate_wqi, calculate_treatment_chemicals, send_telegram_notify

st.set_page_config(page_title="Smart Water Treatment Control (Telegram)", layout="wide")
st.title("💧 ระบบนวัตกรรมประเมิน WQI และคำนวณสารเคมีอัตโนมัติ")
st.subheader("ระบบแจ้งเตือนผ่าน Telegram Notification Infrastructure")

# --- SIDEBAR: IoT Sensors & Config ---
st.sidebar.header("🔌 จำลองค่าจากเซ็นเซอร์ IoT")
input_location = st.sidebar.selectbox("เลือกพื้นที่ตรวจวัด", ["สถานีผลิตน้ำปากแซง (แม่น้ำจันทบุรี)", "คลองท่าช้าง"])
input_ph = st.sidebar.slider("ค่าความเป็นกรด-ด่าง (pH)", 0.0, 14.0, 6.2, 0.1)
input_turb = st.sidebar.slider("ค่าความขุ่น (Turbidity) [NTU]", 0.0, 80.0, 35.0, 0.5)
input_tds = st.sidebar.slider("สารละลายรวมทั้งหมด (TDS) [mg/L]", 0.0, 1200.0, 150.0, 10.0)
input_iron = st.sidebar.slider("ปริมาณเหล็ก (Fe) [mg/L]", 0.0, 2.0, 0.1, 0.05)
input_mn = st.sidebar.slider("ปริมาณแมงกานีส (Mn) [mg/L]", 0.0, 1.5, 0.02, 0.01)

st.sidebar.divider()
st.sidebar.header("🏗️ ขนาดกำลังการผลิตโรงกรองน้ำ")
water_flow = st.sidebar.number_input("อัตราการไหลของน้ำดิบเข้าสู่ระบบ (m³/ชั่วโมง)", min_value=1, max_value=5000, value=100)

st.sidebar.divider()
st.sidebar.header("✈️ ตั้งค่าระบบ Telegram Bot")
bot_token = st.sidebar.text_input("ใส่ Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("ใส่ Telegram Chat ID / Group ID")
trigger_alert = st.sidebar.button("🚨 ส่งข้อความรายงานเข้า Telegram")

# --- PROCESS DATA ---
wqi_score, water_status, status_color = calculate_wqi(input_ph, input_turb, input_tds, input_iron, input_mn)
chem = calculate_treatment_chemicals(input_turb, input_ph, water_flow)

# --- TELEGRAM INTERACTION ---
if trigger_alert and bot_token and chat_id:
    alert_msg = (
        f"🚨 *[รายงานเตือนภัยคุณภาพน้ำและสารเคมี]*\n\n"
        f"📍 *พื้นที่ตรวจวัด:* {input_location}\n"
        f"🌊 *อัตราจ่ายน้ำดิบ:* {water_flow} m³/hr\n"
        f"📈 *ดัชนีคุณภาพน้ำ WQI:* {wqi_score} ({water_status})\n"
        f"------------------------\n"
        f"🧪 *สารส้ม (Alum):* {chem['alum_mg_l']} mg/L (`{chem['alum_g_hr']}` g/hr)\n"
        f"⚪ *ปูนขาว (Lime):* {chem['lime_mg_l']} mg/L (`{chem['lime_g_hr']}` g/hr)\n"
        f"🧼 *คลอรีน (Chlorine):* {chem['chlorine_mg_l']} mg/L (`{chem['chlorine_g_hr']}` g/hr)\n\n"
        f"📌 _หมายเหตุ: {chem['lime_status']}_"
    )
    # รับค่าแบบ Tuple (ผลลัพธ์, ข้อความรายละเอียด Error)
    success, detail_msg = send_telegram_notify(bot_token, chat_id, alert_msg)
    if success:
        st.sidebar.success("ส่งข้อมูลเข้า Telegram สำเร็จแล้ว!")
    else:
        # แสดงรายละเอียดความผิดพลาดให้เห็นชัดเจนบนหน้าเว็บ
        st.sidebar.error(f"ส่งล้มเหลว! รายละเอียด: {detail_msg}")

# --- MAIN DASHBOARD DISPLAY ---
st.markdown(f"### 📍 สถานีตรวจวัด: **{input_location}**")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("ค่า pH", f"{input_ph}")
col2.metric("ความขุ่น", f"{input_turb} NTU")
col3.metric("สารละลาย (TDS)", f"{input_tds} mg/L")
col4.metric("เหล็ก (Fe)", f"{input_iron} mg/L")
col5.metric("แมงกานีส (Mn)", f"{input_mn} mg/L")

st.divider()
st.header("📊 ผลสรุปดัชนีคุณภาพน้ำ (WQI Analysis)")
st.info(f"ดัชนีคุณภาพน้ำรวม WQI: **{wqi_score}** -> คุณภาพอยู่ในระดับ: **{water_status}**")

st.divider()
st.header("🧪 แผงควบคุมการจ่ายสารเคมีอัตโนมัติ (Chemical Dosing)")
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("1. สารส้ม (Alum)")
    st.metric(label="ความเข้มข้นที่แนะนำ", value=f"{chem['alum_mg_l']} mg/L")
    st.metric(label="อัตราการจ่ายสารจริง", value=f"{chem['alum_g_hr']} กรัม/ชั่วโมง")
with c2:
    st.subheader("2. ปูนขาว (Lime)")
    st.metric(label="ความเข้มข้นที่แนะนำ", value=f"{chem['lime_mg_l']} mg/L")
    st.metric(label="อัตราการจ่ายสารจริง", value=f"{chem['lime_g_hr']} กรัม/ชั่วโมง")
with c3:
    st.subheader("3. คลอรีน (Chlorine)")
    st.metric(label="ความเข้มข้นที่แนะนำ", value=f"{chem['chlorine_mg_l']} mg/L")
    st.metric(label="อัตราการจ่ายสารจริง", value=f"{chem['chlorine_g_hr']} กรัม/ชั่วโมง")

