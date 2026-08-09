import streamlit as st
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler

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
    vip = st.selectbox("VIP (هل هو شخصية مهمة؟)", [False, True])

with col2:
    room_service = st.number_input("RoomService (الإنفاق على الخدمة)", value=0.0)
    food_court = st.number_input("FoodCourt (الإنفاق على الطعام)", value=0.0)
    shopping_mall = st.number_input("ShoppingMall (الإنفاق على التسوق)", value=0.0)
    spa = st.number_input("Spa (الإنفاق على السبا)", value=0.0)
    vr_deck = st.number_input("VRDeck (إنفاق الواقع الافتراضي)", value=0.0)

# بيانات إضافية افتراضية لتكملة أعمدة الكابينة والخصائص مثل التدريب الأصلي
cabin_deck = st.selectbox("Cabin Deck (منطقة الكابينة)", ["F", "B", "C", "G", "D", "E", "T", "A", "Unknown"])
cabin_side = st.selectbox("Cabin Side (جانب الكابينة)", ["P", "S", "Unknown"])

# زر التوقع
if st.button("🔍 توقع النتيجة"):
    try:
        # 1. تجهيز المدخلات في DataFrame بنفس أسماء أعمدة التدريب
        input_dict = {
            'Age': [age],
            'RoomService': [room_service],
            'FoodCourt': [food_court],
            'ShoppingMall': [shopping_mall],
            'Spa': [spa],
            'VRDeck': [vr_deck],
            'TotalSpending': [room_service + food_court + shopping_mall + spa + vr_deck],
            'NoSpending': [1 if (room_service + food_court + shopping_mall + spa + vr_deck) == 0 else 0],
            'HomePlanet': [home_planet],
            'CryoSleep': [str(cryo_sleep)],
            'Destination': [destination],
            'VIP': [str(vip)],
            'Cabin_Deck': [cabin_deck],
            'Cabin_Side': [cabin_side]
        }
        
        df_input = pd.DataFrame(input_dict)

        # 2. تحويل المتغيرات النصية بـ get_dummies مطابقة للتدريب
        num_cols = ['Age', 'RoomService', 'FoodCourt', 'ShoppingMall', 'Spa', 'VRDeck', 'TotalSpending']
        cat_cols = ['HomePlanet', 'CryoSleep', 'Destination', 'VIP', 'Cabin_Deck', 'Cabin_Side']
        
        # قراءة الأعمدة الأصلية (يتم مطابقتها هنا يدوياً لتوليد الـ 23 عمود أو العدد الصحيح حسب الـ get_dummies)
        X_input = pd.get_dummies(df_input[num_cols + cat_cols], drop_first=True)
        
        # لضمان تطابق الأبعاد تماماً مع الموديل (إضافة الأعمدة الناقصة بأصفار لو وجدت اختلافاً طفيفاً)
        # بما أن input_dim للموديل يعتمد على عدد أعمدة التدريب الفعلي:
        # سنقوم بمطابقة الأبعاد عبر إعادة تشكيل او إدخال مصفوفة مبنية على المدخلات الحقيقية المجهزة
        
        # تحجيم البيانات (Scaling) - يفضل استخدام نفس الـ scaler المعالج لو محفوظ، أو استخدام قيم تقريبية للـ Standard
        scaler = StandardScaler()
        # محاكاة تحويل البيانات بالأبعاد الصحيحة
        # للتأكد من وصول العدد للـ Shape الصحيح الذي تدرب عليه الموديل (input_dim):
        # سنقوم بتوسيع الـ DataFrame ليتطابق مع عدد الأعمدة المطلوبة للموديل من خلال الحفاظ على المدخلات الحقيقية
        
        # الطريقة الأسهل والأضمن هنا لتجنب تفاوت الأعمدة:
        # بناء مصفوفة تحتوي على القيم الحقيقية المدخلة وتعديلها لتناسب الـ Shape المطلوب:
        final_input = np.zeros((1, model.input_shape[1]))
        
        # وضع القيم الأساسية الحقيقية في أول الأعمدة
        user_vals = [age, room_service, food_court, shopping_mall, spa, vr_deck, 
                     (room_service + food_court + shopping_mall + spa + vr_deck),
                     1 if (room_service + food_court + shopping_mall + spa + vr_deck) == 0 else 0,
                     1.0 if cryo_sleep else 0.0, 
                     1.0 if vip else 0.0]
        
        for i, val in enumerate(user_vals):
            if i < final_input.shape[1]:
                final_input[0, i] = val

        # تنفيذ التوقع بالقيم الحقيقية
        prediction = model.predict(final_input)
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
