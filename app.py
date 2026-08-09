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
st.write(
    "قم بإدخال بيانات الراكب لمعرفة ما إذا كان قد تم نقله (Transported) أم لا باستخدام نموذج الذكاء الاصطناعي."
)


# تحميل الموديل (تأكد من مطابقة اسم ملف الh5 لديك)
@st.cache_resource
def load_my_model():
  model = load_model("best_dnn_model.h5")
  return model


try:
  model = load_my_model()
except Exception as e:
  st.error(f"تعرّض لتحميل الموديل. تأكد من وجود ملف الـ h5 في نفس المجلد: {e}")

# تصميم الواجهة لإدخال البيانات (تأكد من تعديل المدخلات لتناسب الميزات المتدرب عليها موديلك)
st.subheader("📝 بيانات الراكب:")

col1, col2 = st.columns(2)

with col1:
  home_planet = st.selectbox(
      "HomePlanet (الكوكب الأصلي)", ["Earth", "Europa", "Mars"]
  )
  cryo_sleep = st.selectbox(
      "CryoSleep (هل كان في النوم المجمد؟)", [False, True]
  )
  destination = st.selectbox(
      "Destination (وجهة السفر)", ["TRAPPIST-1e", "PSO J318.5-22", "Cancri e"]
  )
  age = st.number_input("Age (العمر)", min_value=0.0, max_value=100.0, value=25.0)

with col2:
  vip = st.selectbox("VIP (هل هو شخصية مهمة؟)", [False, True])
  room_service = st.number_input("RoomService (الإنفاق على الخدمة)", value=0.0)
  food_court = st.number_input("FoodCourt (الإنفاق على الطعام)", value=0.0)
  shopping_mall = st.number_input("ShoppingMall (الإنفاق على التسوق)", value=0.0)

# ملاحظة: إذا كان نموذجك يتطلب معالجة مسبقة (Scaling أو Encoding) قبل إدخاله للموديل،
# يجب تطبيق نفس الخطوات هنا على البيانات قبل تمريرها لـ model.predict()

# زر التوقع
if st.button("🔍 توقع النتيجة"):
  # [تنبيه هام]: هذا تمثيل افتراضي للمصفوفة المدخلة.
  # يجب تحويل المدخلات هنا لتتوافق تماماً مع عدد ونوع الأعمدة (Features) التي دُرب عليها الموديل الخاص بك.
  try:
    # مثال افتراضي لبيانات مدخلة (قم بتعديلها لتطابق شكل بيانات التدريب الخاصة بك)
    # الهوم بلانيت والديستنيشن والـ CryoSleep تتطلب One-Hot Encoding أو Mapping حسب كود التدريب الأصلي
    input_data = np.zeros(
        (1, 10)
    )  # ضع هنا شكل البيانات المناسب لطبقة الإدخال للموديل لديك

    prediction = model.predict(input_data)
    prediction_value = prediction[0][0]

    st.markdown("---")
    st.subheader("📊 نتيجة التوقع:")

    if prediction_value > 0.5:
      st.success(
          f"🎉 *النتيجة: تم نقل الراكب (Transported)!* (احتمالية الثقة:"
          f" {prediction_value * 100:.2f}%)"
      )
    else:
      st.error(
          f"⚠️ *النتيجة: لم يتم نقل الراكب (Not Transported).* (احتمالية الثقة:"
          f" {(1 - prediction_value) * 100:.2f}%)"
      )

  except Exception as e:
    st.warning(
        "ملاحظة برمجية: يرجى التأكد من مطابقة أبعاد مصفوفة الإدخال (Input Shape)"
        f" لعدد الأعمدة التي تدرب عليها الموديل الخاص بك. الخطأ التقني: {e}"
    )