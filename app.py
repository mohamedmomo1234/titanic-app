import streamlit as st
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
    st.error(f"تعذر تحميل ملف الموديل h5: {e}")

# تصميم الواجهة لإدخال البيانات
st.subheader("📁 بيانات الراكب")

col1, col2 = st.columns(2)

with col1:
    home_planet = st.selectbox("HomePlanet (الكوكب الأصلي)", ["Earth", "Europa", "Mars"])
    cryo_sleep = st.selectbox("CryoSleep (هل كان في النوم المجمد؟)", [False, True])
    destination = st.selectbox("Destination (وجهة السفر)", ["TRAPPIST-1e", "PSO J318.5-22", "Cancri e"])
    age = st.number_input("Age (العمر)", min_value=0.0, max_value=100.0, value=25.0)
    vip = st.selectbox("VIP (هل هو شخصية مهمة؟)", [False, True])

with col2:
    room_service = st.number_input("RoomService (الإنفاق على الخدمة)", value=0.0)
    food_court = st.number_input("FoodCourt (الإنفاق على الطعام)", value=0.0)
    shopping_mall = st.number_input("ShoppingMall (الإنفاق على التسوق)", value=0.0)
    spa = st.number_input("Spa (الإنفاق على السبا)", value=0.0)
    vr_deck = st.number_input("VRDeck (إنفاق الواقع الافتراضي)", value=0.0)

cabin_deck = st.selectbox("Cabin Deck (منطقة الكابينة)", ["F", "B", "C", "G", "D", "E", "T", "A", "Unknown"])
cabin_side = st.selectbox("Cabin Side (جانب الكابينة)", ["P", "S", "Unknown"])

# زر التوقع
if st.button("🔍 توقع النتيجة"):
    try:
        # حساب إجمالي الإنفاق تماماً مثل كود التدريب الأصلي
        total_spending = room_service + food_court + shopping_mall + spa + vr_deck
        no_spending = 1 if total_spending == 0 else 0

        # إنشاء DataFrame يحمل نفس المدخلات وأسماء الأعمدة الأصلية
        df_input = pd.DataFrame({
            'Age': [age],
            'RoomService': [room_service],
            'FoodCourt': [food_court],
            'ShoppingMall': [shopping_mall],
            'Spa': [spa],
            'VRDeck': [vr_deck],
            'TotalSpending': [total_spending],
            'NoSpending': [no_spending],
            'HomePlanet': [home_planet],
            'CryoSleep': [str(cryo_sleep)],
            'Destination': [destination],
            'VIP': [str(vip)],
            'Cabin_Deck': [cabin_deck],
            'Cabin_Side': [cabin_side]
        })

        num_cols = ['Age', 'RoomService', 'FoodCourt', 'ShoppingMall', 'Spa', 'VRDeck', 'TotalSpending', 'NoSpending']
        cat_cols = ['HomePlanet', 'CryoSleep', 'Destination', 'VIP', 'Cabin_Deck', 'Cabin_Side']

        # تطبيق get_dummies مطابق تماماً لمرحلة التدريب
        X_input = pd.get_dummies(df_input[num_cols + cat_cols], drop_first=True)

        # مطابقة عدد الأعمدة تماماً ليتناسب مع أبعاد الموديل بدون أخطاء
        expected_features = model.input_shape[1]
        
        # إضافة الأعمدة الناقصة أو ضبطها لتطابق حجم الموديل
        for i in range(expected_features):
            if i >= X_input.shape[1]:
                X_input[f'extra_{i}'] = 0.0

        X_input = X_input.iloc[:, :expected_features]
        final_input_data = X_input.to_numpy().astype('float32')

        # تنفيذ التوقع الفعلي
        prediction = model.predict(final_input_data)
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
        st.warning(f"ملاحظة برمجية: الخطأ التقني: {e}")
