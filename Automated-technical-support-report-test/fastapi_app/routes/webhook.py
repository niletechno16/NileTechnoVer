import os
import requests
from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone, timedelta
from fastapi_app.config.settings import CHATWOOT_URL, ACCOUNT_ID, ACCESS_TOKEN
from fastapi_app.ai.analyzer import analyze_chat
from fastapi_app.utils.parser import parse_ai_result
from fastapi_app.database.init_db import init_db
from fastapi_app.database.operations import (
    save_user,
    save_problem,
    get_or_create_category,
    get_existing_category_names
)

router = APIRouter()


def dt_to_compact(dt: datetime) -> int:
    return int(dt.strftime("%Y%m%d%H%M"))


def get_first_message_dt(messages_list, cairo_tz) -> datetime:
    for msg in messages_list:
        ts      = msg.get("created_at")
        content = msg.get("content")
        if ts and content:
            try:
                return datetime.fromtimestamp(int(ts), tz=cairo_tz)
            except Exception:
                pass
    return datetime.now(cairo_tz)


@router.get("/health")
async def health_check():
    return {"status": "alive"}


@router.post("/init-db")
async def init_db_endpoint(request: Request):
    """
    تشغيل يدوي مرة واحدة لإنشاء الجداول (بدل الاعتماد على startup event
    اللي بقى غير منطقي على serverless لأنه هيتكرر كل cold start).
    لازم تضيف متغير بيئة INIT_DB_SECRET وتبعته في الهيدر x-init-secret.
    """
    secret = os.getenv("INIT_DB_SECRET")
    if not secret or request.headers.get("x-init-secret") != secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    init_db()
    return {"status": "done"}



@router.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    status  = payload.get("status")

    if status == "resolved":

        conv_id        = payload.get("id")
        customer_id    = payload.get("meta", {}).get("sender",   {}).get("id")
        customer_name  = payload.get("meta", {}).get("sender",   {}).get("name",         "Unknown")
        customer_phone = payload.get("meta", {}).get("sender",   {}).get("phone_number", "No Phone")
        agent_id       = payload.get("meta", {}).get("assignee", {}).get("id")
        agent_name     = payload.get("meta", {}).get("assignee", {}).get("name",         "Unassigned")

        cairo_tz = timezone(timedelta(hours=3))

        resolved_at_raw = payload.get("resolved_at") or payload.get("updated_at")
        if resolved_at_raw:
            try:
                resolved_dt = datetime.fromtimestamp(int(resolved_at_raw), tz=cairo_tz)
            except Exception:
                try:
                    resolved_dt = datetime.fromisoformat(
                        str(resolved_at_raw).replace("Z", "+00:00")
                    ).astimezone(cairo_tz)
                except Exception:
                    resolved_dt = datetime.now(cairo_tz)
        else:
            resolved_dt = datetime.now(cairo_tz)

        resolve_date_compact = dt_to_compact(resolved_dt)

        print("\n" + "="*50)
        print(f"🎯 STATUS: RESOLVED")
        print(f"🪪 Customer ID : {customer_id}")
        print(f"👤 Customer    : {customer_name}")
        print(f"📞 Phone       : {customer_phone}")
        print(f"🪪 Agent ID    : {agent_id}")
        print(f"👨‍💻 Agent       : {agent_name}")
        print(f"🆔 Conv ID     : {conv_id}")
        print(f"📅 Resolve     : {resolve_date_compact}")

        api_url = (
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}"
            f"/conversations/{conv_id}/messages"
        )
        headers = {
            "api_access_token": ACCESS_TOKEN,
            "api-access-token": ACCESS_TOKEN,
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(api_url, headers=headers, timeout=20)

            if response.status_code == 200:
                data          = response.json()
                messages_list = data.get('payload') if isinstance(data, dict) else data

                if messages_list:

                    first_dt           = get_first_message_dt(messages_list, cairo_tz)
                    start_message_date = dt_to_compact(first_dt)
                    duration_minutes   = max(0, int((resolved_dt - first_dt).total_seconds() // 60))

                    print(f"⏱️  Start       : {start_message_date}")
                    print(f"⏳ Duration    : {duration_minutes} min")

                    full_chat_text = ""
                    for msg in reversed(messages_list):
                        content = msg.get("content")
                        sender  = msg.get("sender")
                        s_name  = sender.get("name") if sender else "System"
                        if content:
                            full_chat_text += f"[{s_name}]: {content}\n"

                    # ─── جلب الكاتيجوريز الموجودة للبرومت ───
                    existing_cat_names = get_existing_category_names()

                    # ─── AI ───
                    ai_raw = analyze_chat(full_chat_text, existing_cat_names)
                    prob_type, problem, raw_category, summary = parse_ai_result(ai_raw)

                    # ─── جلب/إنشاء category_id ───
                    category_id = get_or_create_category(raw_category)

                    print(f"🏷️  النوع       : {prob_type}")
                    print(f"📋 المشكلة     : {problem}")
                    print(f"📂 Category ID  : {category_id}  ({raw_category})")
                    print(f"📝 الملخص      : {summary[:80]}...")
                    print("="*50 + "\n")

                    # ─── حفظ العميل ───
                    save_user(
                        user_id   = customer_id,
                        user_name = customer_name,
                        phone     = customer_phone,
                        user_type = 1
                    )

                    # ─── حفظ الأيجينت ───
                    save_user(
                        user_id   = agent_id,
                        user_name = agent_name,
                        phone     = None,
                        user_type = 2
                    )

                    # ─── حفظ المشكلة ───
                    save_problem(
                        customer_id        = customer_id,
                        prob_type          = prob_type,
                        problem            = problem,
                        category_id        = category_id,
                        agent_id           = agent_id,
                        conv_id            = conv_id,
                        start_message_date = start_message_date,
                        resolve_date       = resolve_date_compact,
                        duration_minutes   = duration_minutes,
                        summary            = summary
                    )

            else:
                print(f"❌ Chatwoot API Error: {response.status_code}")

        except Exception as e:
            print("⚠️ Error:", str(e))

    return {"status": "success"}
