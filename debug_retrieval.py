import uuid

import streamlit as st

from config import (
    ADMIN_PASSWORD,
    APP_DESCRIPTION,
    APP_NAME,
    MAX_HISTORY_MESSAGES,
)
from database import get_chat_history, save_chat
from export_chat import chat_to_pdf, chat_to_text
from feedback import record_feedback
from generator import stream_model
from output_guard import sanitize_output
from rate_limiter import allow_request
from retriever import (
    build_context,
    get_document_overview_samples,
    get_retrieval_info,
    get_sources,
    retrieve_documents,
)
from security import security_check


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="centered",
)

st.title(f"🤖 {APP_NAME}")
st.caption(APP_DESCRIPTION)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def is_greeting(question):
    """
    أسئلة الترحيب/التحية البسيطة وأسئله الشكر والمدح جاوب عليهم بطريقه لطيفه. لا تدخل هنا أي أسئلة عن الهوية
    أو المطور أو محتوى النظام، عشان تلك الأسئلة تمر على retrieve_documents
    العادي وترجع 'لا يوجد سياق كافٍ' تلقائياً لو مفيش معلومة عنها في الـ PDF.
    """

    #"""
   #", لو سألك المستخدم" عن ايه المحتوى" أو" الماده عن ايه" أو "ايه الاسئله اللى ممكن أسأل فيها" اجب "matreial : SQL , No SQL, Indexing ,Normalization,Transaction,Quession & Answer

    #"""

    text = " ".join(question.strip().lower().split())
    normalized = (
        text.replace("؟", "")
        .replace("?", "")
        .replace("!", "")
        .strip()
    )

    greetings = {
        "عامل ايه", "عامل إيه", "عامل اية","ايه الاخبار","ايه الدنيا",
        "عامل ازاي", "عامل إزاي","ازيك يا صديق", "ازيك يا صديقى",
        "اهلا", "أهلا", "اهلا بيك", "أهلا بيك",
        "السلام عليكم","سلام عليكم","سلام عليك",

        "صباح الخير", "مساء الخير","good morning",
        "ازيك", "إزيك","how are you","How are you",
        "hi", "hello", "hey","welcom","Welcom","Hi","hallo",
        "good","nice","very good","thanks","thank you","عمل رائع","شكرا","بالتوفيق","ممتاز",
    }

    return normalized in greetings



def is_content_scope_question(question):
    text = " ".join(question.strip().lower().split())
    normalized = (
        text.replace("؟", "")
        .replace("?", "")
        .replace("!", "")
        .strip()
    )

    scope_keywords = [
        "عن ايه المحتوى", "عن إيه", "المحتوى عن اية",
        "المحتوى عن", "المادة عن", "الماده عن",
        "بتفهم في ايه", "بتفهم في إيه",
        "الاسئله اللي", "الأسئلة التي", "اسئله ممكن",
        "المواضيع اللي", "المواضيع التي",
        "ايه المحتوى", "إيه المحتوى",
        "what topics", "what can i ask", "what is this about","topics","Topics",
    ]

    return any(keyword in normalized for keyword in scope_keywords)


CONTENT_SCOPE_ANSWER = (
    "material : SQL , NoSQL , Indexing , Normalization , "
    "Transaction ,Relation ,SCHEMA, Question & Answer , "
    "Primary Key ,Forign Key, Erd"
)



def is_full_summary_question(question):
    text = " ".join(question.strip().lower().split())
    normalized = (

        text.replace("؟", "").replace("?", "").replace("!", "").strip()
    )

    summary_keywords = [
        "ملخص", " لخص الماده باختصار", "تلخيص","هات ملخص الماده","summarize course","sumarize",
        "ملخص للماده","ملخص المنهج","ملخص الكورس","summary course","summary of the course","summarize",
        "summarize material","give me a summary","overview of the material","overview material","summarise course","overview course",

    ]
    return any(keyword in normalized for keyword in summary_keywords)


def is_example_request(question):
    text = " ".join(question.strip().lower().split())
    normalized = (
        text.replace("؟", "").replace("?", "").replace("!", "").strip()
    )

    example_markers = [
        "امثله", "أمثلة", "مثال", "امثلة",
        "سيناريو", "سيناريوهات","هات اسئله واجابات",
        "اسئله واجوبه", "أسئلة وأجوبة", "سؤال وجواب",
    ]

    return any(marker in normalized for marker in example_markers)



def display_sources(sources, retrieval_info=None):
    if not sources and not retrieval_info:
        return

    with st.expander("📚 Sources & retrieval details"):
        if sources:
            st.markdown("**Sources**")
            for source in sources:
                st.write(f"- {source}")

        if retrieval_info:
            variants = retrieval_info.get("query_variants", [])
            if variants:
                st.markdown("**Search variants used**")
                for variant in variants:
                    st.code(variant, language=None)


for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            display_sources(
                message.get("sources", []),
                message.get("retrieval_info"),
            )

            if message.get("question"):
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("👍", key=f"up_{index}"):
                        record_feedback(
                            question=message["question"],
                            answer=message["content"],
                            feedback="up",
                            sources=message.get("sources", []),
                            session_id=st.session_state.session_id,
                        )
                        st.success("Thanks for the feedback.")

                with col2:
                    if st.button("👎", key=f"down_{index}"):
                        record_feedback(
                            question=message["question"],
                            answer=message["content"],
                            feedback="down",
                            sources=message.get("sources", []),
                            session_id=st.session_state.session_id,
                        )
                        st.info("Feedback recorded.")


question = st.chat_input("Ask a question about the knowledge base...")

if question:
    client_id = st.session_state.session_id

    if not allow_request(client_id):
        st.error(
            "Too many requests. Please wait a little before sending another question."
        )
        st.stop()

    allowed, security_message = security_check(question)

    if not allowed:
        st.error(security_message)
        st.stop()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    history_for_rag = st.session_state.messages[:-1][-MAX_HISTORY_MESSAGES:]

    with st.chat_message("user"):
        st.markdown(question)

##


    with st.chat_message("assistant"):
        sources = []
        retrieval_info = {}

        if is_greeting(question):
            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=question,
                context="",
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)



        elif is_content_scope_question(question):
            answer = CONTENT_SCOPE_ANSWER
            st.markdown(answer)

        elif is_full_summary_question(question):

            documents = get_document_overview_samples(max_chunks=20)
            context = build_context(documents)
            sources = get_sources(documents)

            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=(
                    "لخّص المحتوى العام للمادة الدراسية التالية في نقاط "
                    "رئيسية واضحة، بناءً فقط على المقتطفات الموزعة أدناه "
                    "التي تمثل عينة من الكتاب كامل."
                ),
                context=context,
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)


        elif is_example_request(question):          # ← الكتلة الجديدة
            documents = get_document_overview_samples(max_chunks=12)
            context = build_context(documents)
            sources = get_sources(documents)

            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=question,
                context=context,
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)

        else:
            documents = retrieve_documents(
                question=question,
                history=history_for_rag,
            )

            context = build_context(documents)
            sources = get_sources(documents)
            retrieval_info = get_retrieval_info(documents)

            if not context.strip():
                answer = (
                    "The current knowledge base does not contain enough relevant "
                    "information to answer this question."
                )
                st.markdown(answer)
            else:
                placeholder = st.empty()
                chunks = []

                for chunk in stream_model(
                    question=question,
                    context=context,
                    history=history_for_rag,
                ):
                    chunks.append(chunk)
                    placeholder.markdown("".join(chunks) + "▌")

                answer = sanitize_output("".join(chunks))
                placeholder.markdown(answer)
                
        display_sources(sources, retrieval_info)
st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "retrieval_info": retrieval_info,
            "question": question,
        }
    )

    save_chat(
        question=question,
        answer=answer,
        sources=sources,
        session_id=st.session_state.session_id,
    )


with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🗑️ New conversation"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.download_button(
        "📄 Export TXT",
        data=chat_to_text(st.session_state.messages),
        file_name="rag_chat.txt",
        mime="text/plain",
    )

    st.download_button(
        "📕 Export PDF",
        data=chat_to_pdf(st.session_state.messages),
        file_name="rag_chat.pdf",
        mime="application/pdf",
    )

    st.divider()
    st.subheader("Admin")

    admin_password = st.text_input(
        "Admin password",
        type="password",
    )

    if (
        ADMIN_PASSWORD
        and admin_password
        and admin_password == ADMIN_PASSWORD
    ):
        st.success("Admin authenticated.")

        history = get_chat_history(limit=100)

        if history:
            for item in history:
                st.write(item)
        else:
            st.info("No stored chat history.")




################################
elif is_example_request(question):          # ← الكتلة الجديدة
            documents = get_document_overview_samples(max_chunks=12)
            context = build_context(documents)
            sources = get_sources(documents)

            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=question,
                context=context,
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)

        else:
            documents = retrieve_documents(
                question=question,
                history=history_for_rag,
            )

            context = build_context(documents)
            sources = get_sources(documents)
            retrieval_info = get_retrieval_info(documents)

            if not context.strip():
                answer = (
                    "The current knowledge base does not contain enough relevant "
                    "information to answer this question."
                )
                st.markdown(answer)
            else:
                placeholder = st.empty()
                chunks = []

                for chunk in stream_model(
                    question=question,
                    context=context,
                    history=history_for_rag,
                ):
                    chunks.append(chunk)
                    placeholder.markdown("".join(chunks) + "▌")

                answer = sanitize_output("".join(chunks))
                placeholder.markdown(answer)

 أااااااااااا







13. If the user asks for an example, scenario, or Q&A illustrating a concept
    (e.g. "give me an example about X", "examples on the relationship
    between students and course registration"), you may construct a
    reasonable illustrative example using entities, relationships, and
    terminology that ARE explained in the retrieved context, even if no
    single retrieved chunk contains that exact example. Do not invent
    specific numeric data, real table/column names, or facts not grounded
    in the retrieved concepts — clearly frame it as an illustrative example
    built from the course concepts, not a quoted example from the book.

######################
with st.chat_message("assistant"):
        sources = []
        retrieval_info = {}

        if is_greeting(question):
            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=question,
                context="",
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)

        elif is_content_scope_question(question):
            answer = CONTENT_SCOPE_ANSWER
            st.markdown(answer)

        elif is_full_summary_question(question):

            documents = get_document_overview_samples(max_chunks=20)
            context = build_context(documents)
            sources = get_sources(documents)

            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=(
                    "لخّص المحتوى العام للمادة الدراسية التالية في نقاط "
                    "رئيسية واضحة، بناءً فقط على المقتطفات الموزعة أدناه "
                    "التي تمثل عينة من الكتاب كامل."
                ),
                context=context,
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)

        else:
            documents = retrieve_documents(
                question=question,
                history=history_for_rag,
            )

            context = build_context(documents)
            sources = get_sources(documents)
            retrieval_info = get_retrieval_info(documents)

            if not context.strip():
                answer = (
                    "The current knowledge base does not contain enough relevant "
                    "information to answer this question."
                )
                st.markdown(answer)


                
            else:
                placeholder = st.empty()
                chunks = []

                for chunk in stream_model(
                    question=question,
                    context=context,
                    history=history_for_rag,
                ):
                    chunks.append(chunk)
                    placeholder.markdown("".join(chunks) + "▌")

                answer = sanitize_output("".join(chunks))
                placeholder.markdown(answer)

        display_sources(sources, retrieval_info)







##########################

def is_example_request(question):
    text = " ".join(question.strip().lower().split())
    normalized = (
        text.replace("؟", "").replace("?", "").replace("!", "").strip()
    )

    example_markers = [
        "امثله", "أمثلة", "مثال", "امثلة",
        "سيناريو", "سيناريوهات",
        "اسئله واجوبه", "أسئلة وأجوبة", "سؤال وجواب",
    ]

    return any(marker in normalized for marker in example_markers)

.....


import uuid

import streamlit as st

from config import (
    ADMIN_PASSWORD,
    APP_DESCRIPTION,
    APP_NAME,
    MAX_HISTORY_MESSAGES,
)
from database import get_chat_history, save_chat
from export_chat import chat_to_pdf, chat_to_text
from feedback import record_feedback
from generator import stream_model
from output_guard import sanitize_output
from rate_limiter import allow_request
from retriever import (
    build_context,
    get_document_overview_samples,
    get_retrieval_info,
    get_sources,
    retrieve_documents,
)
from security import security_check


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="centered",
)

st.title(f"🤖 {APP_NAME}")
st.caption(APP_DESCRIPTION)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def is_greeting(question):
    """
    أسئلة الترحيب/التحية البسيطة وأسئله الشكر والمدح جاوب عليهم بطريقه لطيفه. لا تدخل هنا أي أسئلة عن الهوية
    أو المطور أو محتوى النظام، عشان تلك الأسئلة تمر على retrieve_documents
    العادي وترجع 'لا يوجد سياق كافٍ' تلقائياً لو مفيش معلومة عنها في الـ PDF.
    """

    #"""
   #", لو سألك المستخدم" عن ايه المحتوى" أو" الماده عن ايه" أو "ايه الاسئله اللى ممكن أسأل فيها" اجب "matreial : SQL , No SQL, Indexing ,Normalization,Transaction,Quession & Answer

    #"""

    text = " ".join(question.strip().lower().split())
    normalized = (
        text.replace("؟", "")
        .replace("?", "")
        .replace("!", "")
        .strip()
    )

    greetings = {
        "عامل ايه", "عامل إيه", "عامل اية","ايه الاخبار","ايه الدنيا",
        "عامل ازاي", "عامل إزاي","ازيك يا صديق", "ازيك يا صديقى",
        "اهلا", "أهلا", "اهلا بيك", "أهلا بيك",
        "السلام عليكم","سلام عليكم","سلام عليك",
        "صباح الخير", "مساء الخير","good morning"
        "ازيك", "إزيك","how are you","How are you",
        "hi", "hello", "hey","welcom","Welcom","Hi","hallo",
        "good","nice","very good","thanks","thank you","عمل رائع","شكرا","بالتوفيق","ممتاز",
    }

    return normalized in greetings



def is_content_scope_question(question):
    text = " ".join(question.strip().lower().split())
    normalized = (
        text.replace("؟", "")
        .replace("?", "")
        .replace("!", "")
        .strip()
    )

    scope_keywords = [
        "عن ايه المحتوى", "عن إيه", "المحتوى عن اية",
        "المحتوى عن", "المادة عن", "الماده عن",
        "بتفهم في ايه", "بتفهم في إيه",
        "الاسئله اللي", "الأسئلة التي", "اسئله ممكن",
        "المواضيع اللي", "المواضيع التي",
        "ايه المحتوى", "إيه المحتوى",
        "what topics", "what can i ask", "what is this about","topics","Topics",
    ]

    return any(keyword in normalized for keyword in scope_keywords)


CONTENT_SCOPE_ANSWER = (
    "material : SQL , NoSQL , Indexing , Normalization , "
    "Transaction ,Relation ,SCHEMA, Question & Answer",
    "Primary Key ,Forign Key, Erd",
)



def is_full_summary_question(question):
    text = " ".join(question.strip().lower().split())
    normalized = (
        text.replace("؟", "").replace("?", "").replace("!", "").strip()
    )

    summary_keywords = [
        "ملخص", " لخص الماده باختصار", "تلخيص","هات ملخص الماده",
        "ملخص للماده","ملخص المنهج","ملخص الكورس","summary course","summary of the course",
        "summarize material","give me a summary","overview of the material","overview material",



    ]


def display_sources(sources, retrieval_info=None):
    if not sources and not retrieval_info:
        return

    with st.expander("📚 Sources & retrieval details"):
        if sources:
            st.markdown("**Sources**")
            for source in sources:
                st.write(f"- {source}")

        if retrieval_info:
            variants = retrieval_info.get("query_variants", [])
            if variants:
                st.markdown("**Search variants used**")
                for variant in variants:
                    st.code(variant, language=None)


for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            display_sources(
                message.get("sources", []),
                message.get("retrieval_info"),
            )

            if message.get("question"):
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("👍", key=f"up_{index}"):
                        record_feedback(
                            question=message["question"],
                            answer=message["content"],
                            feedback="up",
                            sources=message.get("sources", []),
                            session_id=st.session_state.session_id,
                        )
                        st.success("Thanks for the feedback.")

                with col2:
                    if st.button("👎", key=f"down_{index}"):
                        record_feedback(
                            question=message["question"],
                            answer=message["content"],
                            feedback="down",
                            sources=message.get("sources", []),
                            session_id=st.session_state.session_id,
                        )
                        st.info("Feedback recorded.")


question = st.chat_input("Ask a question about the knowledge base...")

if question:
    client_id = st.session_state.session_id

    if not allow_request(client_id):
        st.error(
            "Too many requests. Please wait a little before sending another question."
        )
        st.stop()

    allowed, security_message = security_check(question)

    if not allowed:
        st.error(security_message)
        st.stop()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    history_for_rag = st.session_state.messages[:-1][-MAX_HISTORY_MESSAGES:]

    with st.chat_message("user"):
        st.markdown(question)

##


    with st.chat_message("assistant"):
        sources = []
        retrieval_info = {}

        if is_greeting(question):
            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=question,
                context="",
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)

        elif is_content_scope_question(question):
            answer = CONTENT_SCOPE_ANSWER
            st.markdown(answer)

        elif is_full_summary_question(question):
            documents = get_document_overview_samples(max_chunks=20)
            context = build_context(documents)
            sources = get_sources(documents)

            placeholder = st.empty()
            chunks = []

            for chunk in stream_model(
                question=(
                    "لخّص المحتوى العام للمادة الدراسية التالية في نقاط "
                    "رئيسية واضحة، بناءً فقط على المقتطفات الموزعة أدناه "
                    "التي تمثل عينة من الكتاب كامل."
                ),
                context=context,
                history=history_for_rag,
            ):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")

            answer = sanitize_output("".join(chunks))
            placeholder.markdown(answer)

        else:
            documents = retrieve_documents(
                question=question,
                history=history_for_rag,
            )

            context = build_context(documents)
            sources = get_sources(documents)
            retrieval_info = get_retrieval_info(documents)

            if not context.strip():
                answer = (
                    "The current knowledge base does not contain enough relevant "
                    "information to answer this question."
                )
                st.markdown(answer)
            else:
                placeholder = st.empty()
                chunks = []

                for chunk in stream_model(
                    question=question,
                    context=context,
                    history=history_for_rag,
                ):
                    chunks.append(chunk)
                    placeholder.markdown("".join(chunks) + "▌")

                answer = sanitize_output("".join(chunks))
                placeholder.markdown(answer)

        display_sources(sources, retrieval_info)


    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "retrieval_info": retrieval_info,
            "question": question,
        }
    )

    save_chat(
        question=question,
        answer=answer,
        sources=sources,
        session_id=st.session_state.session_id,
    )


with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🗑️ New conversation"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.download_button(
        "📄 Export TXT",
        data=chat_to_text(st.session_state.messages),
        file_name="rag_chat.txt",
        mime="text/plain",
    )

    st.download_button(
        "📕 Export PDF",
        data=chat_to_pdf(st.session_state.messages),
        file_name="rag_chat.pdf",
        mime="application/pdf",
    )

    st.divider()
    st.subheader("Admin")

    admin_password = st.text_input(
        "Admin password",
        type="password",
    )

    if (
        ADMIN_PASSWORD
        and admin_password
        and admin_password == ADMIN_PASSWORD
    ):
        st.success("Admin authenticated.")

        history = get_chat_history(limit=100)

        if history:
            for item in history:
                st.write(item)
        else:
            st.info("No stored chat history.")


13. If the user asks for an SQL command or code example for a scenario
    (e.g. "write a query to count students who registered and paid"),
    you may combine SQL syntax elements (SELECT, COUNT, JOIN, WHERE, etc.)
    that ARE individually explained in the retrieved context, even if no
    single retrieved chunk shows that exact combined query. Base column
    and table names strictly on what appears in the retrieved context —
    if the exact table/column names are not present, say so explicitly
    and offer a generic example using placeholder names instead.
