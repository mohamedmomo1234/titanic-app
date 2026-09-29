1) صياغات السؤال (query variants)
============================================================
 - 'الفرق بين primary key و forign key'
 - 'الفرق بين primary key و forign key primary key المفتاح الأساسي key primary key foreign key مفتاح foreign key المفتاح الأجنبي key primary key foreign key مفتاح'
 - 'الفرق بين primary key forign key'

============================================================
2) نتايج hybrid_search للسؤال الأصلي
============================================================
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|████████████████| 391/391 [00:02<00:00, 166.49it/s]
عدد النتايج: 16
 hybrid_score=0.0164 | page=229 | 'key?  \n∙ Candidate keys are chosen randomly  \n∙ Primary key is the selected cand'
 hybrid_score=0.0161 | page=207 | '58. What is the difference between a candidate key and a primary \nkey?  \n∙ Candi'
 hybrid_score=0.0154 | page=229 | '∙ To uniquely identify tuples  \n∙ To store multiple values  \n∙ To reference othe'
 hybrid_score=0.0149 | page=216 | 'primary key ∙ All attributes must be candidate keys  \n∙ All attributes must be f'
 hybrid_score=0.0146 | page=14 | '3Representingrelationships between tables  \n• A foreign key creates a relationsh'

============================================================
3) بعد الـ reranking
============================================================
Loading weights: 100%|███████████████| 201/201 [00:00<00:00, 1090.73it/s]
 rerank_score=0.9413 | page=207 | '58. What is the difference between a candidate key and a primary \nkey?  \n∙ Candi'
 rerank_score=0.8059 | page=229 | 'key?  \n∙ Candidate keys are chosen randomly  \n∙ Primary key is the selected cand'
 rerank_score=0.5635 | page=229 | '∙ To uniquely identify tuples  \n∙ To store multiple values  \n∙ To reference othe'
 rerank_score=0.1161 | page=216 | 'primary key ∙ All attributes must be candidate keys  \n∙ All attributes must be f'
 rerank_score=0.0766 | page=14 | '3Representingrelationships between tables  \n• A foreign key creates a relationsh'

============================================================
4) النتيجة النهائية من retrieve_documents (الفعلية)
============================================================
عدد النتايج النهائية: 4
 rerank_score=0.9413 | '58. What is the difference between a candidate key and a primary \nkey?  \n∙ Candidate keys are chosen'
 rerank_score=0.8059 | 'key?  \n∙ Candidate keys are chosen randomly  \n∙ Primary key is the selected candidate key  \n∙ Candid'
 rerank_score=0.5635 | '∙ To uniquely identify tuples  \n∙ To store multiple values  \n∙ To reference other tables  \nAnswer: T'
 rerank_score=0.1161 | 'primary key ∙ All attributes must be candidate keys  \n∙ All attributes must be foreign keys  \n   Ans'
(venv) PS E:\نقل ملفات من السى C\Downloads\Reusable_RAG_Engine_Production_Updated> 
