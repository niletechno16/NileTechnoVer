from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date
from collections import defaultdict
import calendar

ARABIC_MONTHS = {
    1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',
    7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'
}


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


def _filter_reports(reports, date_from, date_to):
    df = int(date_from.replace('-', ''))
    dt = int(date_to.replace('-', ''))
    return [r for r in reports if df <= r['resolved_date'] <= dt]


def _customers_from_reports(all_customers, filtered_reports):
    stats = defaultdict(lambda: {'total': 0, 'resolved': 0, 'unresolved': 0, 'unspecified': 0, 'mins': []})
    for r in filtered_reports:
        c = r['customer_name']
        stats[c]['total'] += 1
        pt = r.get('problem_type')
        if pt == 1:
            stats[c]['resolved'] += 1
        elif pt == 0:
            stats[c]['unresolved'] += 1
        else:
            stats[c]['unspecified'] += 1
        if r.get('resolution_minutes'):
            stats[c]['mins'].append(r['resolution_minutes'])
    result = []
    for customer in all_customers:
        name = customer['customer_name']
        s    = stats.get(name, {'total': 0, 'resolved': 0, 'unresolved': 0, 'unspecified': 0, 'mins': []})
        mins = s['mins']
        result.append({
            'customer_id':            customer['customer_id'],
            'customer_name':          name,
            'customer_phone':         customer['customer_phone'],
            'total_reports':          s['total'],
            'resolved':               s['resolved'],
            'unresolved':             s['unresolved'],
            'unspecified':            s['unspecified'],
            'avg_resolution_minutes': round(sum(mins)/len(mins)) if mins else None,
        })
    return sorted(result, key=lambda x: x['total_reports'], reverse=True)


@login_required
def customers_list(request):
    if get_role(request.user) != 'visitor' and not is_manager_level(request.user):
        return redirect('home')

    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)
    search = request.GET.get('search', '')

    base_ctx = {
        'search': search, 'date_from': date_from, 'date_to': date_to,
        'month_label': month_label, 'filter_mode': filter_mode,
        'filter_month_year': filter_month_year, 'is_manager': True,
    }

    if get_role(request.user) == 'visitor':
        try:
            vdata            = get_visitor_data(request)
            filtered_reports = _filter_reports(vdata['reports'], date_from, date_to)
            customers        = _customers_from_reports(vdata['customers'], filtered_reports)
            if search:
                customers = [c for c in customers if search in c['customer_name'] or search in c['customer_phone']]
        except Exception:
            customers = []
        return render(request, 'customers/index.html', {**base_ctx, 'customers': customers})

    try:
        conn   = get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "EXEC Top_Customer_resolved_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw = cursor.fetchall() or []
        customers = [
            {
                'customer_id':            r.get('customer_id',        ''),
                'customer_name':          r.get('customer_name',       ''),
                'customer_phone':         r.get('customer_phone',      ''),
                'total_reports':          r.get('TotalProblems',        0) or 0,
                'resolved':               r.get('Resolved',             0) or 0,
                'unresolved':             r.get('Unresolved',           0) or 0,
                'unspecified':            r.get('NotDefined',           0) or 0,
                'avg_resolution_minutes': round(r.get('Avg_Resolution_Time', 0) or 0) or None,
            }
            for r in raw
        ]
        if search:
            customers = [c for c in customers if search in c['customer_name'] or search in c['customer_phone']]
        conn.close()
    except Exception:
        customers = []

    return render(request, 'customers/index.html', {**base_ctx, 'customers': customers})


@login_required
def customer_detail(request, customer_id):
    if get_role(request.user) != 'visitor' and not is_manager_level(request.user):
        return redirect('home')

    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)

    base_ctx = {
        'date_from': date_from, 'date_to': date_to, 'month_label': month_label,
        'filter_mode': filter_mode, 'filter_month_year': filter_month_year, 'is_manager': True,
    }

    if get_role(request.user) == 'visitor':
        try:
            vdata    = get_visitor_data(request)
            customer = next((c for c in vdata['customers'] if c['customer_id'] == customer_id), None)
            reports  = _filter_reports(
                [r for r in vdata['reports'] if r['customer_name'] == customer['customer_name']],
                date_from, date_to
            )
            reports = sorted(reports, key=lambda r: (r['resolved_date'], r.get('resolved_time', '')), reverse=True)
        except Exception:
            customer, reports = None, []
        return render(request, 'customers/detail.html', {**base_ctx, 'customer': customer, 'reports': reports})

    try:
        conn   = get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "EXEC Get_Reports_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw = cursor.fetchall() or []
        all_reports = [
            {
                'conv_id':            r.get('conv_id',           ''),
                'agent_id':           r.get('agent_id',          ''),
                'agent_name':         r.get('agent_name',        ''),
                'customer_id':        r.get('customer_id',       ''),
                'customer_name':      r.get('customer_name',     ''),
                'customer_phone':     r.get('customer_phone',    ''),
                'classification':     r.get('classification',    ''),
                'summary':            r.get('summary',           ''),
                'resolution_minutes': r.get('resolution_minutes', None),
                'resolve_date':       r.get('resolve_date',      ''),
                'resolved_time':      r.get('resolve_time',      ''),
                'status_label':       r.get('status_label',      ''),
                'problem_type':       r.get('problem_type',      None),
            }
            for r in raw
        ]
        # فلتر على الكاستومر ID
        customer_rows = [r for r in all_reports if str(r['customer_id']) == str(customer_id)]
        customer = {
            'customer_id':   customer_id,
            'customer_name': customer_rows[0]['customer_name'] if customer_rows else '',
            'customer_phone': customer_rows[0]['customer_phone'] if customer_rows else '',
        } if customer_rows else None
        reports = customer_rows
        conn.close()
    except Exception:
        customer, reports = None, []

    return render(request, 'customers/detail.html', {**base_ctx, 'customer': customer, 'reports': reports})
