def parse_ai_result(raw_text):
    prob_type = 0
    problem = ""
    category = ""
    summary = ""

    try:
        for line in raw_text.splitlines():
            line = line.strip()

            if line.startswith("النوع:"):
                val = line.replace("النوع:", "").strip()

                if val in ("0", "1", "2"):
                    prob_type = int(val)
                else:
                    prob_type = 0

            elif line.startswith("المشكلة:"):
                problem = line.replace("المشكلة:", "").strip()

            elif line.startswith("التصنيف:"):
                category = line.replace("التصنيف:", "").strip()

            elif line.startswith("الملخص:"):
                summary = line.replace("الملخص:", "").strip()

    except Exception:
        problem = raw_text
        category = "غير محدد"
        summary = raw_text
        prob_type = 0

    # قيم افتراضية
    if not problem:
        problem = raw_text

    if not category:
        category = "غير محدد"

    if not summary:
        summary = problem

    # تصحيح التوافق بين النوع والتصنيف
    category_normalized = category.strip().replace("ـ", "")

    if category_normalized == "لم يتم تحديد مشكلة":
        prob_type = 2

    # حماية إضافية لو الـ AI كتب النوع 2 ونسي التصنيف
    if prob_type == 2 and category_normalized != "لم يتم تحديد مشكلة":
        category = "لم يتم تحديد مشكلة"

    return prob_type, problem, category, summary