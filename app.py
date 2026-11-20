import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Golden Vision AI — Strategic Scalping Engine",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم الواجهة (واضح، شفاف، وخالٍ من التعقيد)
st.markdown("""
    <style>
    .stApp { background-color: #0b0514; color: #ffffff; }
    .expert-card {
        background-color: #160c29; border: 1px solid #2e1854; border-radius: 12px;
        padding: 16px; text-align: right; direction: rtl; margin-bottom: 12px;
    }
    .maestro-buy {
        background-color: #092e1a; border: 2px solid #2ecc71; color: #2ecc71;
        padding: 16px; border-radius: 12px; text-align: center; font-size: 21px; font-weight: bold; direction: rtl;
    }
    .maestro-sell {
        background-color: #330a0e; border: 2px solid #e74c3c; color: #e74c3c;
        padding: 16px; border-radius: 12px; text-align: center; font-size: 21px; font-weight: bold; direction: rtl;
    }
    .maestro-wait {
        background-color: #2c2105; border: 2px solid #f1c40f; color: #f1c40f;
        padding: 16px; border-radius: 12px; text-align: center; font-size: 21px; font-weight: bold; direction: rtl;
    }
    .order-line {
        background-color: #1e1136; padding: 10px 14px; border-radius: 8px;
        margin-bottom: 8px; direction: rtl; text-align: right; border-right: 4px solid #a29bfe;
    }
    .kpi-box {
        background-color: #120922; border: 1px solid #3a206b; border-radius: 8px;
        padding: 10px; text-align: center; direction: rtl;
    }
    h1, h2, h3, h4, p { direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# 2. القائمة الجانبية (الإدارة الوظيفية وإدارة المخاطر)
with st.sidebar:
    st.markdown("## ⚙️ إعدادات المنصة والاتصال")
    api_key = st.text_input("Twelve Data API Key:", value="afab930df3c64de29322c914219dd640", type="password")
    
    st.markdown("---")
    st.markdown("### 🤖 إعدادات Telegram Bot")
    tg_token = st.text_input("Telegram Bot Token:", value="9129059269:AAEu-F1mn7tEOAvBKDIa9mD_1xif5KxrRvY", type="password")
    tg_chat_id = st.text_input("Telegram Chat ID:", value="8985355476")
    
    st.markdown("---")
    st.markdown("### 🎯 إعدادات التكتيك والفريمات")
    market_type = st.radio("نوع السوق:", ["الذهب والعملات (Gold & Forex)", "العملات الرقمية (Crypto)"])
    if market_type == "الذهب والعملات (Gold & Forex)":
        symbol = st.selectbox("اختر الزوج:", ["XAU/USD", "EUR/USD", "GBP/USD", "USD/JPY"])
    else:
        symbol = st.selectbox("اختر العملة:", ["BTC/USD", "ETH/USD", "SOL/USD"])
    
    exec_tf = st.selectbox("فريم التنفيذ (التكتيك):", ["1min", "5min", "15min", "30min"], index=0)
    trend_tf = st.selectbox("فريم البوصلة (الاتجاه العام):", ["15min", "1h", "4h"], index=1)
    
    st.markdown("---")
    st.markdown("### 🛡️ حوكمة وإدارة المخاطر")
    balance = st.number_input("رأس المال ($):", min_value=10.0, value=100.0, step=10.0)
    risk_pct = st.slider("نسبة المخاطرة لكل صفقة (%):", 0.5, 5.0, 1.0, 0.5)
    min_confidence = st.slider("الحد الأدنى للثقة لقبول الصفقة (%):", 60, 90, 75, 5)

# 3. جلب البيانات مع التخزين المؤقت الذكي لحماية API
@st.cache_data(ttl=20)
def fetch_data(sym, interval, key):
    url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval={interval}&outputsize=100&apikey={key}"
    try:
        r = requests.get(url, timeout=15).json()
        if "values" not in r:
            return None, r.get("message", "خطأ في جلب البيانات من المزود")
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
    st.error(f"⚠️ خطأ في الاتصال بالسوق (تحليل السيناريو - وضع الطوارئ): {err1 or err2}")
    st.stop()

# 4. محرك التحليل الكمي والهيكلي (دمج النهج المعالج + التطوري + إدارة المخاطر)
def calculate_indicators(df):
    df = df.copy()
    df["ema9"] = df["close"].ewm(span=9).mean()
    df["ema21"] = df["close"].ewm(span=21).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()
    
    # حساب RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    
    # حساب ATR لقياس التقلب الحقيقي ومنع ضرب SL بسبب ضجيج 1min
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=14).mean()
    return df

df_exec = calculate_indicators(df_exec)
df_trend = calculate_indicators(df_trend)

# قراءة المؤشرات الحالية
price = df_exec["close"].iloc[-1]
atr_val = df_exec["atr"].iloc[-1]
rsi_val = df_exec["rsi"].iloc[-1]
ema9_exec = df_exec["ema9"].iloc[-1]
ema21_exec = df_exec["ema21"].iloc[-1]

ema21_trend = df_trend["ema21"].iloc[-1]
ema50_trend = df_trend["ema50"].iloc[-1]
trend_price = df_trend["close"].iloc[-1]

# تقييم الاتجاه العام (البوصلة)
trend_bullish = (trend_price > ema21_trend) and (ema21_trend > ema50_trend)
trend_bearish = (trend_price < ema21_trend) and (ema21_trend < ema50_trend)

# حساب نسبة الثقة الحقيقية بناءً على توافق الشروط (مؤشر أداء قابل للقياس)
score = 50
reasons = []

if trend_bullish:
    score += 20
    reasons.append(f"اتجاه عام صاعد على فريم {trend_tf} (السعر فوق EMA21 و EMA50)")
elif trend_bearish:
    score += 20
    reasons.append(f"اتجاه عام هابط على فريم {trend_tf} (السعر تحت EMA21 و EMA50)")
else:
    reasons.append(f"تذبذب على فريم البوصلة {trend_tf} (حذر من الضجيج)")

if trend_bullish and (ema9_exec > ema21_exec):
    score += 15
    reasons.append(f"تقاطع إيجابي للمتوسطات السريعة (EMA 9/21) على {exec_tf}")
elif trend_bearish and (ema9_exec < ema21_exec):
    score += 15
    reasons.append(f"تقاطع سلبي للمتوسطات السريعة (EMA 9/21) على {exec_tf}")

if trend_bullish and (45 <= rsi_val <= 68):
    score += 10
    reasons.append(f"زخم شرائي صحي ومستقر (RSI: {rsi_val:.1f}) بدون تشبع")
elif trend_bearish and (32 <= rsi_val <= 55):
    score += 10
    reasons.append(f"زخم بيعي صحي ومستقر (RSI: {rsi_val:.1f}) بدون تشبع")
else:
    score -= 10
    reasons.append(f"تحذير زخم (RSI: {rsi_val:.1f}) — احتمالية ارتداد أو تذبذب")

confidence_score = max(min(score, 96), 35)

# تحديد القرار النهائي وحساب SL/TP بدقة السكالبينج المحمي بـ ATR
buffer = atr_val * 0.6  # هامش أمان ديناميكي حسب تقلب السوق

if trend_bullish and confidence_score >= min_confidence:
    signal_dir = "شراء (BUY)"
    raw_dir = "BUY"
    expert_trend = "صاعد قوي ومؤكد 🟢"
    entry = price
    recent_low = df_exec["low"].tail(6).min()
    sl = min(recent_low - buffer, entry - (atr_val * 1.2))
    risk_dist = abs(entry - sl)
    tp1 = entry + (risk_dist * 2.0)
    tp2 = entry + (risk_dist * 3.5)
    tp3 = entry + (risk_dist * 5.0)
    maestro_msg = f"🚀 قرار المايسترو: نفذ صفقة {signal_dir} الآن — الثقة المحسوبة: {confidence_score}%"
    maestro_css = "maestro-buy"

elif trend_bearish and confidence_score >= min_confidence:
    signal_dir = "بيع (SELL)"
    raw_dir = "SELL"
    expert_trend = "هابط قوي ومؤكد 🔴"
    entry = price
    recent_high = df_exec["high"].tail(6).max()
    sl = max(recent_high + buffer, entry + (atr_val * 1.2))
    risk_dist = abs(sl - entry)
    tp1 = entry - (risk_dist * 2.0)
    tp2 = entry - (risk_dist * 3.5)
    tp3 = entry - (risk_dist * 5.0)
    maestro_msg = f"🚀 قرار المايسترو: نفذ صفقة {signal_dir} الآن — الثقة المحسوبة: {confidence_score}%"
    maestro_css = "maestro-sell"

else:
    signal_dir = "انتظار ومراقبة (WAIT)"
    raw_dir = "WAIT"
    expert_trend = "سوق متذبذب / خارج شروط الأمان 🟡"
    entry = price
    sl = price - (atr_val * 1.5)
    tp1 = price + (atr_val * 2.5)
    tp2 = price + (atr_val * 4.0)
    tp3 = price + (atr_val * 6.0)
    risk_dist = abs(entry - sl)
    maestro_msg = f"⏸️ قرار المايسترو: لا تدخل الآن (نسبة الثقة {confidence_score}% أقل من الحد الآمن {min_confidence}%)"
    maestro_css = "maestro-wait"

# حساب إدارة المخاطر المالية (KPIs)
risk_amount = balance * (risk_pct / 100.0)
rr_ratio = round(abs(tp2 - entry) / risk_dist, 2) if risk_dist > 0 else 0

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

# 5. الواجهة الرئيسية (واضحة، قابلة للقياس، وقابلة للتنفيذ)
st.markdown(f"# 🤖 Golden Vision AI — ({symbol})")
st.markdown(f'<div class="{maestro_css}">{maestro_msg}</div><br>', unsafe_allow_html=True)

# شريط مؤشرات الأداء الرئيسية (KPIs)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi-box"><b>نسبة الثقة الفعلية</b><br><span style="color:#00cec9; font-size:20px;">{confidence_score}%</span></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-box"><b>المبلغ المخاطر به</b><br><span style="color:#e74c3c; font-size:20px;">${risk_amount:.2f}</span></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-box"><b>العائد للمخاطرة (R:R)</b><br><span style="color:#2ecc71; font-size:20px;">1 : {rr_ratio}</span></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-box"><b>تقلب السوق (ATR)</b><br><span style="color:#a29bfe; font-size:20px;">{atr_val:.2f}</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

c_left, c_right = st.columns([1.2, 1.8])

with c_left:
    reasons_html = "".join([f"<li>{r}</li>" for r in reasons])
    st.markdown(f"""
        <div class="expert-card">
            <h3 style="color:#a29bfe; margin-top:0;">📊 التشخيص الاستراتيجي للسوق</h3>
            <p><b>الزوج:</b> {symbol} | <b>فريم التنفيذ:</b> {exec_tf} | <b>البوصلة:</b> {trend_tf}</p>
            <p><b>حالة السوق:</b> {expert_trend}</p>
            <p><b>أسباب القرار الفني:</b></p>
            <ul style="padding-right: 20px; margin-bottom: 0;">{reasons_html}</ul>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="expert-card">
            <h3 style="color:#a29bfe; margin-top:0;">📋 بطاقة الأوامر التكتيكية</h3>
            <div class="order-line">🎯 <b>الدخول (Entry):</b> <code>{entry:.2f}</code></div>
            <div class="order-line" style="border-color:#e74c3c;">🛑 <b>وقف الخسارة المحمي (SL):</b> <code>{sl:.2f}</code></div>
            <div class="order-line" style="border-color:#2ecc71;">✅ <b>الهدف 1 (TP1 - 1:2):</b> <code>{tp1:.2f}</code></div>
            <div class="order-line" style="border-color:#2ecc71;">✅ <b>الهدف 2 (TP2 - 1:3.5):</b> <code>{tp2:.2f}</code></div>
            <div class="order-line" style="border-color:#00b894;">🚀 <b>الهدف 3 (TP3 - 1:5):</b> <code>{tp3:.2f}</code></div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("📤 إرسال التوصية الموثقة إلى Telegram", use_container_width=True):
        if not tg_token or not tg_chat_id:
            st.warning("⚠️ أدخل أولاً Telegram Bot Token و Chat ID!")
        elif raw_dir == "WAIT":
            st.warning("⚠️ السوق حالياً في وضع الانتظار (WAIT) لحماية رأس مالك. خفض الحد الأدنى للثقة إذا أردت الإرسال يدوياً.")
        else:
            reasons_txt = "\n".join([f"• {r}" for r in reasons])
            text = (
                f"🚨 *Golden Vision AI — Verified Signal* 🚨\n\n"
                f"🔹 *الزوج:* `{symbol}` ({exec_tf})\n"
                f"🔹 *القرار:* `✨ {signal_dir}`\n"
                f"🔹 *نسبة الثقة:* `{confidence_score}%` | *R:R:* `1:{rr_ratio}`\n\n"
                f"🎯 *الدخول:* `{entry:.2f}`\n"
                f"🛑 *وقف الخسارة (SL):* `{sl:.2f}`\n"
                f"✅ *الهدف الأول (TP1):* `{tp1:.2f}`\n"
                f"✅ *الهدف الثاني (TP2):* `{tp2:.2f}`\n"
                f"🚀 *الهدف الثالث (TP3):* `{tp3:.2f}`\n\n"
                f"🛡️ *المخاطرة المحددة:* `${risk_amount:.2f}` ({risk_pct}%)\n"
                f"📌 *التحليل:*\n{reasons_txt}"
            )
            success, err_desc = send_telegram_message(tg_token, tg_chat_id, text)
            if success:
                st.success("✅ تم إرسال التوصية الموثقة إلى هاتفك عبر تيليجرام بنجاح!")
            else:
                st.error(f"❌ خطأ: {err_desc}")

with c_right:
    fig = go.Figure(data=[go.Candlestick(
        x=df_exec["datetime"], open=df_exec["open"], high=df_exec["high"],
        low=df_exec["low"], close=df_exec["close"],
        increasing_line_color="#2ecc71", decreasing_line_color="#e74c3c", name=symbol
    )])
    fig.add_hline(y=entry, line_dash="dash", line_color="#a29bfe", annotation_text="Entry")
    fig.add_hline(y=sl, line_dash="solid", line_color="#e74c3c", annotation_text="SL (ATR Protected)")
    fig.add_hline(y=tp1, line_dash="dot", line_color="#2ecc71", annotation_text="TP1")
    fig.add_hline(y=tp2, line_dash="dot", line_color="#00b894", annotation_text="TP2")
    fig.add_hline(y=tp3, line_dash="dot", line_color="#00b894", annotation_text="TP3")
    
    fig.update_layout(
        title=f"الشارت الحي والتحليل الهيكلي: {symbol} ({exec_tf})",
        paper_bgcolor="#160c29", plot_bgcolor="#0b0514", font=dict(color="white"),
        xaxis_rangeslider_visible=False, height=580, margin=dict(l=15, r=15, t=40, b=15)
    )
    st.plotly_chart(fig, use_container_width=True)
