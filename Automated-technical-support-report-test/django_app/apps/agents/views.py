from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date
from collections import defaultdict
import calendar
from apps.users.notifications import notify_resolved

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


def _agents_from_reports(all_agents, filtered_reports):
    stats = defaultdict(lambda: {'total': 0, 'resolved': 0, 'unresolved': 0, 'unspecified': 0, 'mins': []})
    for r in filtered_reports:
        a = r['agent_name']
        stats[a]['total'] += 1
        pt = r.get('problem_type')
        if pt == 1:
            stats[a]['resolved'] += 1
        elif pt == 0:
            stats[a]['unresolved'] += 1
        else:
            stats[a]['unspecified'] += 1
        if r.get('resolution_minutes'):
            stats[a]['mins'].append(r['resolution_minutes'])
    result = []
    for agent in all_agents:
        name = agent['agent_name']
        s    = stats.get(name, {'total': 0, 'resolved': 0, 'unresolved': 0, 'unspecified': 0, 'mins': []})
        mins = s['mins']
        result.append({
            'agent_id':               agent['agent_id'],
            'agent_name':             name,
            'total':                  s['total'],
            'resolved':               s['resolved'],
            'unresolved':             s['unresolved'],
            'unspecified':            s['unspecified'],
            'avg_resolution_minutes': round(sum(mins)/len(mins)) if mins else None,
        })
    return sorted(result, key=lambda x: x['total'], reverse=True)


@login_required
def agents_list(request):
    today  = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)
    search = request.GET.get('search', '')

    base_ctx = {
        'search': search, 'date_from': date_from, 'date_to': date_to,
        'month_label': month_label, 'filter_mode': filter_mode,
        'filter_month_year': filter_month_year,
        'is_manager': is_manager_level(request.user),
    }

    if get_role(request.user) == 'visitor':
        try:
            vdata            = get_visitor_data(request)
            filtered_reports = _filter_reports(vdata['reports'], date_from, date_to)
            agents           = _agents_from_reports(vdata['agents'], filtered_reports)
            if search:
                agents = [a for a in agents if search in a['agent_name']]
        except Exception:
            agents = []
        return render(request, 'agents/index.html', {**base_ctx, 'agents': agents, 'is_manager': True})

    try:
        conn   = get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "EXEC Top_Agent_resolved_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw = cursor.fetchall() or []
        agents = [
            {
                'agent_id':               r.get('agent_id',          ''),
                'agent_name':             r.get('agent_name',         ''),
                'total':                  r.get('TotalProblems',       0) or 0,
                'resolved':               r.get('Resolved',            0) or 0,
                'unresolved':             r.get('Unresolved',          0) or 0,
                'unspecified':            r.get('NotDefined',          0) or 0,
                'avg_resolution_minutes': round(r.get('Avg_Resolution_Time', 0) or 0) or None,
            }
            for r in raw
        ]
        if search:
            agents = [a for a in agents if search in a['agent_name']]
        if not is_manager_level(request.user):
            current = request.user.first_name or request.user.username
            agents = [a for a in agents if a['agent_name'] == current]
        conn.close()
    except Exception:
        agents = []

    return render(request, 'agents/index.html', {**base_ctx, 'agents': agents})


@login_required
def agent_detail(request, agent_id):
    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)

    base_ctx = {
        'date_from': date_from, 'date_to': date_to, 'month_label': month_label,
        'filter_mode': filter_mode, 'filter_month_year': filter_month_year,
        'is_manager': is_manager_level(request.user),
    }

    if get_role(request.user) == 'visitor':
        try:
            vdata         = get_visitor_data(request)
            agent         = next((a for a in vdata['agents'] if a['agent_id'] == agent_id), None)
            agent_reports = _filter_reports(
                [r for r in vdata['reports'] if r['agent_id'] == agent_id],
                date_from, date_to
            )
            agent_reports = sorted(agent_reports, key=lambda r: (r['resolved_date'], r.get('resolved_time', '')), reverse=True)
        except Exception:
            agent, agent_reports = None, []
        return render(request, 'agents/detail.html', {**base_ctx, 'agent': agent, 'reports': agent_reports, 'is_manager': True})

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
        # جيب بيانات الأجنت من أول تقرير
        agent_rows = [r for r in all_reports if str(r['agent_id']) == str(agent_id)]
        agent = {'agent_id': agent_id, 'agent_name': agent_rows[0]['agent_name']} if agent_rows else None
        reports = agent_rows

        # ─── إشعار resolved ───
        # لو في تقارير resolved جديدة لم يُرسل إشعار عنها بعد
        try:
            from apps.users.models import Notification
            for r in agent_rows:
                if r.get('classification', '').startswith('تم حل'):
                    conv_id   = str(r.get('conv_id', ''))
                    # نتحقق لو الإشعار ده مش اتبعتش من قبل
                    already   = Notification.objects.filter(
                        notif_type='resolved',
                        agent_id=str(agent_id),
                        body__contains=conv_id,
                    ).exists() if conv_id else False

                    if not already:
                        agent_name = r.get('agent_name', str(agent_id))
                        notify_resolved(agent_id, agent_name, conv_id)
        except Exception:
            pass
        # ─────────────────────

        conn.close()
    except Exception:
        agent, reports = None, []

    return render(request, 'agents/detail.html', {**base_ctx, 'agent': agent, 'reports': reports})
