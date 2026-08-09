[11:53 pm, 09/08/2026] Mohamed Said 2050: import streamlit as st
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

# إعداد الصفحة
st.set_page_config(
    page_title="Spaceship Titanic Predictor", page_icon="🚀", layout="centered"
)

# عنوان التطبيق
st.title("🚀 Spaceship Titanic - Passenger Survival Prediction")
st.write("قم بإدخال بيانات الراكب لمعرفة ما إذا كان قد تم نقله (Transported).")

# تحميل الموديل
@st.cache_resource
def load_my_model():
    model = load_model("best_dnn_model.h5")
    return model

try:
    model = load_my_model()
except Exception as e:
    st.error(f"تعذر تحميل ملف الموديل h5: تأكد من وجوده في نفس المجلد. الخطأ: {e}")

# تصميم الواجهة لإدخال البيانات
st.subheader("📁 بيانات الراكب")

col1, col2 = st.columns(2)

with col1:
    home_planet = st.selectbox("HomePlanet (الكوكب الأصلي)", ["Earth", "Europa", "Mars"])
    cryo_sleep = st.selectbox("CryoSleep (هل كان في النوم المجمد؟)", [False, True])
    destination = st.selectbox("Destination (وجهة السفر)", ["TRAPPIST-1e", "PSO J318.5-22", "Cancri e"])
    age = st.number_input("Age (العمر)", min_value=0.0, max_value=100.0, value=25.0)

with col2:
    vip = st.selectbox("VIP (هل هو شخصية مهمة؟)", [False, True])
    room_service = st.number_input("RoomService (الإنفاق على الخدمة)", value=0.0)
    food_court = st.number_input("FoodCourt (الإنفاق على الطعام)", value=0.0)
    shopping_mall = st.number_input("ShoppingMall (الإنفاق على التسوق)", value=0.0)

# زر التوقع
if st.button("🔍 توقع النتيجة"):
    try:
        # إنشاء مصفوفة الإدخال بالأبعاد الـ 23 التي يتوقعها الموديل لتجنب الخطأ
        input_data = np.zeros((1, 23))
        
        # تعبئة القيم الأساسية في مصفوفة المدخلات
        input_data[0, 0] = age
        input_data[0, 1] = 1.0 if cryo_sleep else 0.0
        input_data[0, 2] = 1.0 if vip else 0.0
        input_data[0, 3] = room_service
        input_data[0, 4] = food_court
        input_data[0, 5] = shopping_mall
        
        # تنفيذ التوقع عبر النمط العصبي
        prediction = model.predict(input_data)
        prediction_value = prediction[0][0]

        st.markdown("---")
        st.subheader("📊 نتيجة التوقع")

        if prediction_value > 0.5:
            st.success(
                f"🎉 الاحتمالية: تم نقل الراكب (Transported) بنسبة {prediction_value * 100:.2f}%"
            )
        else:
            st.error(
                f"⚠️ الاحتمالية: لم يتم نقل الراكب (Not Transported) بنسبة {(1 - prediction_value) * 100:.2f}%"
            )

    except Exception as e:
        st.warning(
            f"ملاحظة برمجية: يرجى التأكد من مطابقة أبعاد مصفوفة الإدخال لعدد الأعمدة الـ 23. الخطأ التقني: {e}"
        )
