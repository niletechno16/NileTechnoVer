from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
import calendar
from datetime import date

ARABIC_MONTHS = {
    1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',
    7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'
}


def _build_page_range(page_obj):
    """بتبني قائمة أرقام الصفحات مع None للـ '...' بين الأرقام البعيدة"""
    current = page_obj.number
    total   = page_obj.paginator.num_pages
    pages   = []
    for n in range(1, total + 1):
        if n == 1 or n == total or (current - 2 <= n <= current + 2):
            pages.append(n)
        elif pages and pages[-1] is not None:
            pages.append(None)  # يمثل الـ ...
    return pages


def _resolve_filter(request, today):
    default_from = today.replace(day=1).strftime('%Y-%m-%d')
    last_day     = calendar.monthrange(today.year, today.month)[1]
    default_to   = today.replace(day=last_day).strftime('%Y-%m-%d')
    filter_mode       = request.GET.get('filter_mode', 'monthyear')
    filter_month_year = request.GET.get('month_year', '')
    if filter_mode == 'monthyear' and filter_month_year:
        try:
            y, m = int(filter_month_year[:4]), int(filter_month_year[5:7])
            ld   = calendar.monthrange(y, m)[1]
            date_from   = f"{y}-{m:02d}-01"
            date_to     = f"{y}-{m:02d}-{ld:02d}"
            month_label = f"{ARABIC_MONTHS[m]} {y}"
        except (ValueError, IndexError):
            date_from, date_to = default_from, default_to
            month_label = f"{ARABIC_MONTHS[today.month]} {today.year}"
            filter_month_year = today.strftime('%Y-%m')
    elif filter_mode == 'exact':
        date_from   = request.GET.get('from', default_from)
        date_to     = request.GET.get('to',   default_to)
        month_label = f"{date_from} ← {date_to}"
        filter_month_year = ''
    else:
        date_from, date_to = default_from, default_to
        month_label       = f"{ARABIC_MONTHS[today.month]} {today.year}"
        filter_month_year = today.strftime('%Y-%m')
    return date_from, date_to, month_label, filter_mode, filter_month_year


@login_required
def reports_list(request):
    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)
    agent_filter = request.GET.get('agent', '')
    class_filter = request.GET.get('classification', '')
    conv_id_filter = request.GET.get('conv_id', '')
    customer_filter = request.GET.get('customer_name', '')
    resolved_type = request.GET.get('resolved_type', '')   # '1' = resolved, '0' = unresolved
    category_id_filter = request.GET.get('category_id', '')  # filter by category id
    category_name_filter = request.GET.get('category_name', '')  # display name for badge

    # لو في conv_id filter → وسّع الـ date range تلقائياً عشان يلاقي التقرير
    if conv_id_filter:
        date_from = '2020-01-01'
        date_to   = date.today().strftime('%Y-%m-%d')
        month_label = f'بحث عن المحادثة: {conv_id_filter}'
        filter_mode = 'exact'
        filter_month_year = ''

    # لو في customer filter → عرّف label
    if customer_filter:
        month_label = f'{month_label} — عميل: {customer_filter}'

    # resolved_type label
    resolved_type_label = ''
    if resolved_type == '1':
        resolved_type_label = 'محلول'
    elif resolved_type == '0':
        resolved_type_label = 'غير محلول'
    elif resolved_type == '2':
        resolved_type_label = 'غير محدد'

    base_ctx = {
        'month_label': month_label, 'filter_mode': filter_mode,
        'filter_month_year': filter_month_year,
        'filters': {'agent': agent_filter, 'from': date_from, 'to': date_to, 'classification': class_filter, 'customer_name': customer_filter, 'resolved_type': resolved_type, 'category_id': category_id_filter, 'category_name': category_name_filter},
        'is_manager': is_manager_level(request.user),
        'resolved_type_label': resolved_type_label,
    }

    if get_role(request.user) == 'visitor':
        try:
            vdata = get_visitor_data(request)
            data  = vdata['reports']
            if date_from:
                data = [r for r in data if r['resolved_date'] >= int(date_from.replace('-', ''))]
            if date_to:
                data = [r for r in data if r['resolved_date'] <= int(date_to.replace('-', ''))]
            if agent_filter:
                data = [r for r in data if r['agent_name'] == agent_filter]
            if class_filter:
                data = [r for r in data if class_filter in r['classification']]
            if resolved_type == '1':
                data = [r for r in data if r.get('problem_type') == 1]
            elif resolved_type == '0':
                data = [r for r in data if r.get('problem_type') == 0]
            elif resolved_type == '2':
                data = [r for r in data if r.get('problem_type') == 2]
            if conv_id_filter:
                data = [r for r in data if str(r.get('conv_id', '')) == conv_id_filter]
            if customer_filter:
                data = [r for r in data if r.get('customer_name', '') == customer_filter]
            data = sorted(data, key=lambda r: (r['resolved_date'], r.get('resolved_time', '')), reverse=True)
            for r in data:
                pt = r.get('problem_type')
                r['classification_type'] = 'resolved' if pt == 1 else ('unresolved' if pt == 0 else 'other')

            agents = list(set(r['agent_name'] for r in vdata['reports']))
        except Exception:
            data, agents = [], []
        paginator = Paginator(data, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        page_range = _build_page_range(page_obj)
        return render(request, 'reports/list.html', {**base_ctx, 'data': page_obj, 'agents': agents, 'is_manager': True, 'total_count': len(data), 'page_range': page_range})

    try:
        conn   = get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "EXEC Get_Reports_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw = cursor.fetchall() or []
        data = [
            {
                'conv_id':            r.get('conv_id',           ''),
                'customer_name':      r.get('customer_name',     ''),
                'customer_phone':     r.get('customer_phone',    ''),
                'agent_name':         r.get('agent_name',        ''),
                'classification':     r.get('classification',    ''),
                'summary':            r.get('summary',           ''),
                'resolution_minutes': r.get('resolution_minutes', None),
                'resolve_date':       r.get('resolve_date',      ''),
                'resolved_time':      r.get('resolve_time',      ''),
                'status_label':       r.get('status_label',      ''),
                'problem_type':       r.get('problem_type',      None),  # 0=unresolved, 1=resolved
                'category_id':        r.get('category_id',       None),
            }
            for r in raw
        ]
        # فلتر بعد البروسيدر
        if agent_filter:
            data = [r for r in data if r['agent_name'] == agent_filter]
        if class_filter:
            data = [r for r in data if class_filter in r['classification']]
        if resolved_type != '':
            rt = int(resolved_type)
            data = [r for r in data if r['problem_type'] == rt]
        if category_id_filter != '':
            try:
                cid = int(category_id_filter)
                data = [r for r in data if r.get('category_id') == cid]
            except (ValueError, TypeError):
                pass
        if conv_id_filter:
            data = [r for r in data if str(r.get('conv_id', '')) == conv_id_filter]
        if customer_filter:
            data = [r for r in data if r.get('customer_name', '') == customer_filter]
        if not is_manager_level(request.user):
            current = request.user.first_name or request.user.username
            data = [r for r in data if r['agent_name'] == current]
        # جيب قائمة الأجنتات من الداتا نفسها
        agents = []
        if is_manager_level(request.user):
            agents = sorted(set(r['agent_name'] for r in data if r['agent_name']))
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Reports DB error: %s", e, exc_info=True)
        data, agents = [], []

    total_count = len(data)
    paginator = Paginator(data, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = _build_page_range(page_obj)

    return render(request, 'reports/list.html', {**base_ctx, 'data': page_obj, 'agents': agents, 'total_count': total_count, 'page_range': page_range})


@login_required
def monthly(request):
    year  = int(request.GET.get('year',  date.today().year))
    month = int(request.GET.get('month', date.today().month))
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years  = list(range(date.today().year - 2, date.today().year + 1))

    base_ctx = {
        'months': months, 'years': years,
        'selected_month': month, 'selected_year': year,
        'is_manager': is_manager_level(request.user),
    }

    if get_role(request.user) == 'visitor':
        try:
            vdata       = get_visitor_data(request)
            month_start = int(f"{year}{month:02d}01")
            month_end   = int(f"{year}{month:02d}{calendar.monthrange(year, month)[1]}")
            month_reps  = [r for r in vdata['reports'] if month_start <= r['resolved_date'] <= month_end]
            agents_seen = {}
            for r in month_reps:
                a = r['agent_name']
                if a not in agents_seen:
                    agents_seen[a] = {'agent_name': a, 'total': 0, 'resolved': 0, 'unresolved': 0, 'unspecified': 0}
                agents_seen[a]['total'] += 1
                if r['classification'].startswith('تم حل'):
                    agents_seen[a]['resolved'] += 1
                else:
                    agents_seen[a]['unresolved'] += 1
            data = sorted(agents_seen.values(), key=lambda x: x['total'], reverse=True)
        except Exception:
            data = []
        return render(request, 'reports/monthly.html', {**base_ctx, 'data': data, 'is_manager': True})

    try:
        conn      = get_connection()
        cursor    = conn.cursor(as_dict=True)
        date_from = f"{year}-{month:02d}-01"
        date_to   = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
        cursor.execute(
            "EXEC Top_Agent_resolved_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw  = cursor.fetchall() or []
        conn.close()
        data = [
            {
                'agent_name':  r.get('agent_name', ''),
                'total':       r.get('TotalProblems', 0) or 0,
                'resolved':    r.get('Resolved',      0) or 0,
                'unresolved':  r.get('Unresolved',    0) or 0,
                'unspecified': r.get('NotDefined',    0) or 0,
            }
            for r in raw
            if r.get('agent_name')
        ]
        if not is_manager_level(request.user):
            current = request.user.first_name or request.user.username
            data = [r for r in data if r['agent_name'] == current]
    except Exception:
        data = []

    return render(request, 'reports/monthly.html', {**base_ctx, 'data': data})