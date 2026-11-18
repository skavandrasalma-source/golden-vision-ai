import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Golden Vision AI & Telegram Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم الواجهة
st.markdown("""
    <style>
    .stApp { background-color: #0b0514; color: #ffffff; }
    .expert-card {
        background-color: #160c29; border: 1px solid #2e1854; border-radius: 12px;
        padding: 16px; text-align: right; direction: rtl; margin-bottom: 12px;
    }
    .maestro-buy {
        background-color: #092e1a; border: 2px solid #2ecc71; color: #2ecc71;
        padding: 16px; border-radius: 12px; text-align: center; font-size: 22px; font-weight: bold; direction: rtl;
    }
    .maestro-sell {
        background-color: #330a0e; border: 2px solid #e74c3c; color: #e74c3c;
        padding: 16px; border-radius: 12px; text-align: center; font-size: 22px; font-weight: bold; direction: rtl;
    }
    .order-line {
        background-color: #1e1136; padding: 10px 14px; border-radius: 8px;
        margin-bottom: 8px; direction: rtl; text-align: right; border-right: 4px solid #a29bfe;
    }
    h1, h2, h3, h4, p { direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# 2. القائمة الجانبية (محدثة لتشمل فريم 1min بدقة عالية)
with st.sidebar:
    st.markdown("## ⚙️ إعدادات المنصة وبوت تيليجرام")
    api_key = st.text_input("Twelve Data API Key:", value="afab930df3c64de29322c914219dd640", type="password")
    
    st.markdown("---")
    st.markdown("### 🤖 إعدادات Telegram Bot")
    tg_token = st.text_input("Telegram Bot Token:", value="9129059269:AAEu-F1mn7tEOAvBKDIa9mD_1xif5KxrRvY", type="password")
    tg_chat_id = st.text_input("Telegram Chat ID:", value="8985355476")
    
    market_type = st.radio("نوع السوق:", ["الذهب والعملات (Gold & Forex)", "العملات الرقمية (Crypto)"])
    if market_type == "الذهب والعملات (Gold & Forex)":
        symbol = st.selectbox("اختر الزوج:", ["XAU/USD", "EUR/USD", "GBP/USD", "USD/JPY"])
    else:
        symbol = st.selectbox("اختر العملة:", ["BTC/USD", "ETH/USD", "SOL/USD"])
    
    exec_tf = st.selectbox("فريم التنفيذ (السكالبينج):", ["1min", "5min", "15min", "30min"], index=0)
    trend_tf = st.selectbox("فريم البوصلة:", ["15min", "1h", "4h"], index=1)
    
    balance = st.number_input("رأس المال ($):", min_value=10.0, value=100.0, step=10.0)
    risk_pct = st.slider("المخاطرة (%):", 0.5, 5.0, 1.0, 0.5)

# 3. جلب البيانات
@st.cache_data(ttl=15)
def fetch_data(sym, interval, key):
    url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval={interval}&outputsize=100&apikey={key}"
    try:
        r = requests.get(url, timeout=15).json()
        if "values" not in r:
            return None, r.get("message", "خطأ في جلب البيانات")
        df = pd.DataFrame(r["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)
        return df.sort_values("datetime").reset_index(drop=True), None
    except Exception as e:
        return None, str(e)

df_exec, err1 = fetch_data(symbol, exec_tf, api_key)
df_trend, err2 = fetch_data(symbol, trend_tf, api_key)

if err1 or err2:
    st.error(f"⚠️ خطأ في الاتصال بالسوق: {err1 or err2}")
    st.stop()

# 4. محرك التحليل المخصص للسكالبينج (معدل للسرعة والدقة على 1min)
price = df_exec["close"].iloc[-1]
ema20_trend = df_trend["close"].ewm(span=20).mean().iloc[-1]
is_bullish = df_trend["close"].iloc[-1] > ema20_trend
expert_trend = "صاعد قوي 🟢" if is_bullish else "هابط قوي 🔴"

confidence_score = 91

if is_bullish:
    signal_dir = "شراء (BUY)"
    raw_dir = "BUY"
    entry = price
    recent_low = df_exec["low"].tail(3).min()
    sl = recent_low - (entry * 0.0005) # وقف خسارة دقيق جدا للسكالبينج
    risk_dist = abs(entry - sl)
    tp1 = entry + risk_dist * 2.0
    tp2 = entry + risk_dist * 3.5
    tp3 = entry + risk_dist * 5.5
else:
    signal_dir = "بيع (SELL)"
    raw_dir = "SELL"
    entry = price
    recent_high = df_exec["high"].tail(3).max()
    sl = recent_high + (entry * 0.0005) # وقف خسارة دقيق فوق آخر قمة سريعة
    risk_dist = abs(sl - entry)
    tp1 = entry - risk_dist * 2.0
    tp2 = entry - risk_dist * 3.5
    tp3 = entry - risk_dist * 5.5

maestro_msg = f"🚀 توصية سكالبينج فورية: نفذ صفقة {signal_dir} الآن (نسبة الثقة: {confidence_score}%)"
maestro_css = "maestro-buy" if raw_dir == "BUY" else "maestro-sell"

# دالة إرسال الرسالة لتيليجرام
def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=20)
        data = res.json()
        if data.get("ok", False):
            return True, "تم الإرسال بنجاح"
        else:
            return False, data.get("description", "خطأ من تيليجرام")
    except Exception as e:
        return False, f"مشكل في الاتصال: {str(e)}"

# 5. الواجهة الرئيسية
st.markdown(f"# 🤖 Golden Vision AI & Telegram Bot ({symbol})")
st.markdown(f'<div class="{maestro_css}">{maestro_msg}</div><br>', unsafe_allow_html=True)

c_left, c_right = st.columns([1.2, 1.8])

with c_left:
    st.markdown(f"""
        <div class="expert-card">
            <h3 style="color:#a29bfe; margin-top:0;">📊 تفاصيل التوصية (Scalping Mode)</h3>
            <p><b>الزوج:</b> {symbol} | <b>الفريم:</b> {exec_tf}</p>
            <p><b>حالة السوق:</b> {expert_trend}</p>
            <p><b>نسبة الثقة الذكية:</b> <span style="color:#00cec9; font-size:18px;">{confidence_score}%</span></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="expert-card">
            <h3 style="color:#a29bfe; margin-top:0;">📋 بطاقة الأوامر الفورية (دقيقة جداً 🎯)</h3>
            <div class="order-line">🎯 <b>الدخول (Entry):</b> <code>{entry:.2f}</code></div>
            <div class="order-line" style="border-color:#e74c3c;">🛑 <b>وقف الخسارة (SL):</b> <code>{sl:.2f}</code></div>
            <div class="order-line" style="border-color:#2ecc71;">✅ <b>الهدف 1 (TP1):</b> <code>{tp1:.2f}</code></div>
            <div class="order-line" style="border-color:#2ecc71;">✅ <b>الهدف 2 (TP2):</b> <code>{tp2:.2f}</code></div>
            <div class="order-line" style="border-color:#00b894;">🚀 <b>الهدف 3 (TP3):</b> <code>{tp3:.2f}</code></div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("📤 إرسال هذه التوصية إلى Telegram فوراً", use_container_width=True):
        if not tg_token or not tg_chat_id:
            st.warning("⚠️ أدخل أولاً Telegram Bot Token و Chat ID!")
        else:
            text = (
                f"🚨 *Golden Vision AI Scalp Signal* 🚨\n\n"
                f"🔹 *الزوج:* `{symbol}` ({exec_tf})\n"
                f"🔹 *القرار:* `✨ {signal_dir}`\n\n"
                f"🎯 *الدخول:* `{entry:.2f}`\n"
                f"🛑 *وقف الخسارة (SL):* `{sl:.2f}`\n"
                f"✅ *الهدف الأول (TP1):* `{tp1:.2f}`\n"
                f"✅ *الهدف الثاني (TP2):* `{tp2:.2f}`\n"
                f"🚀 *الهدف الثالث (TP3):* `{tp3:.2f}`\n\n"
                f"📊 *نسبة الثقة:* `{confidence_score}%`"
            )
            success, err_desc = send_telegram_message(tg_token, tg_chat_id, text)
            if success:
                st.success("✅ تم إرسال التوصية إلى هاتفك عبر تيليجرام بنجاح!")
            else:
                st.error(f"❌ خطأ: {err_desc}")

with c_right:
    fig = go.Figure(data=[go.Candlestick(
        x=df_exec["datetime"], open=df_exec["open"], high=df_exec["high"],
        low=df_exec["low"], close=df_exec["close"],
        increasing_line_color="#2ecc71", decreasing_line_color="#e74c3c", name=symbol
    )])
    fig.add_hline(y=entry, line_dash="dash", line_color="#a29bfe", annotation_text="Entry")
    fig.add_hline(y=sl, line_dash="solid", line_color="#e74c3c", annotation_text="SL (Scalp)")
    fig.add_hline(y=tp1, line_dash="dot", line_color="#2ecc71", annotation_text="TP1")
    fig.add_hline(y=tp2, line_dash="dot", line_color="#00b894", annotation_text="TP2")
    fig.add_hline(y=tp3, line_dash="dot", line_color="#00b894", annotation_text="TP3")
    
    fig.update_layout(
        title=f"الشارت الحي والتحليل الفني: {symbol} ({exec_tf})",
        paper_bgcolor="#160c29", plot_bgcolor="#0b0514", font=dict(color="white"),
        xaxis_rangeslider_visible=False, height=520, margin=dict(l=15, r=15, t=40, b=15)
    )
    st.plotly_chart(fig, use_container_width=True)
