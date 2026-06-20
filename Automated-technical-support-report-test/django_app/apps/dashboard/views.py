from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date
import calendar
import logging

logger = logging.getLogger(__name__)

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


def _date_int(date_str):
    return int(date_str.replace('-', ''))


def _empty_context():
    return {
        'total_reports':           0,
        'total_resolved':          0,
        'total_unresolved':        0,
        'total_unspecified':       0,
        'total_customers':         0,
        'top_agents_resolved':     [],
        'top_customers':           [],
        'common_problems':         [],
        'resolved_pct':            0,
        'unresolved_pct':          0,
        'unspecified_pct':         0,
        'traffic_by_date':         [],
        'avg_resolution_overall':  0,
        'avg_resolution_by_agent': [],
        'db_error':                True,
    }


@login_required
def home(request):
    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)

    base_ctx = {
        'is_manager':        is_manager_level(request.user),
        'date_from':         date_from,
        'date_to':           date_to,
        'month_label':       month_label,
        'filter_mode':       filter_mode,
        'filter_month_year': filter_month_year,
    }

    # ─── Visitor mode ────────────────────────────────────────────────────────
    if get_role(request.user) == 'visitor':
        try:
            vdata = get_visitor_data(request)
            df_int = _date_int(date_from)
            dt_int = _date_int(date_to)

            all_reports = vdata['reports']
            filtered    = [r for r in all_reports if df_int <= r['resolved_date'] <= dt_int]

            total_reports    = len(filtered)
            total_resolved   = sum(1 for r in filtered if r.get('problem_type') == 1)
            total_unspecified = sum(1 for r in filtered if r.get('problem_type') == 2)
            total_unresolved = total_reports - total_resolved - total_unspecified
            resolved_pct     = round(total_resolved   / total_reports * 100) if total_reports else 0
            unresolved_pct   = round(total_unresolved / total_reports * 100) if total_reports else 0
            unspecified_pct  = round(total_unspecified / total_reports * 100) if total_reports else 0
            total_customers  = vdata['total_customers']

            avg_mins = [r['resolution_minutes'] for r in filtered if r.get('resolution_minutes')]
            avg_resolution_overall = round(sum(avg_mins) / len(avg_mins)) if avg_mins else 0

            agents_map = {}
            for r in filtered:
                a = r['agent_name']
                if a not in agents_map:
                    agents_map[a] = {'agent_name': a, 'total': 0, 'resolved': 0, 'unresolved': 0, 'unspecified': 0}
                agents_map[a]['total'] += 1
                pt = r.get('problem_type')
                if pt == 1:
                    agents_map[a]['resolved'] += 1
                elif pt == 0:
                    agents_map[a]['unresolved'] += 1
                else:
                    agents_map[a]['unspecified'] += 1
            top_agents_resolved = sorted(agents_map.values(), key=lambda x: x['total'], reverse=True)[:4]

            cust_map = {}
            for r in filtered:
                c = r['customer_name']
                cust_map[c] = cust_map.get(c, 0) + 1
            top_customers = sorted(
                [{'customer_name': k, 'total': v} for k, v in cust_map.items()],
                key=lambda x: x['total'], reverse=True
            )[:5]

            prob_map = {}
            for r in filtered:
                cl = r['classification']
                cid = r.get('category_id', None)
                if cl not in prob_map:
                    prob_map[cl] = {'total': 0, 'category_id': cid}
                prob_map[cl]['total'] += 1
            common_problems = sorted(
                [{'classification': k, 'total': v['total'], 'category_id': v['category_id']} for k, v in prob_map.items()],
                key=lambda x: x['total'], reverse=True
            )[:5]

            traffic_map = {}
            for r in filtered:
                d_str = str(r['resolved_date'])
                label = f"{d_str[6:8]}/{d_str[4:6]}/{d_str[:4]}"
                traffic_map[label] = traffic_map.get(label, 0) + 1
            traffic_by_date = [{'date': k, 'count': v} for k, v in sorted(traffic_map.items())]

            agent_mins = {}
            for r in filtered:
                if r.get('resolution_minutes'):
                    a = r['agent_name']
                    if a not in agent_mins:
                        agent_mins[a] = []
                    agent_mins[a].append(r['resolution_minutes'])
            avg_resolution_by_agent = sorted([
                {'name': a, 'avg': round(sum(mins)/len(mins))}
                for a, mins in agent_mins.items()
            ], key=lambda x: x['avg'], reverse=True)[:8]

            return render(request, 'dashboard/home.html', {
                **base_ctx,
                'total_reports':           total_reports,
                'total_resolved':          total_resolved,
                'total_unresolved':        total_unresolved,
                'total_unspecified':       total_unspecified,
                'total_customers':         total_customers,
                'top_agents_resolved':     top_agents_resolved,
                'top_customers':           top_customers,
                'common_problems':         common_problems,
                'resolved_pct':            resolved_pct,
                'unresolved_pct':          unresolved_pct,
                'unspecified_pct':         unspecified_pct,
                'traffic_by_date':         traffic_by_date,
                'avg_resolution_overall':  avg_resolution_overall,
                'avg_resolution_by_agent': avg_resolution_by_agent,
                'is_manager':              True,
            })
        except Exception:
            return render(request, 'dashboard/home.html', {**base_ctx, **_empty_context()})

    # ─── Real DB mode ────────────────────────────────────────────────────────
    try:
        conn   = get_connection()
        cursor = conn.cursor(as_dict=True)

        # ── 1. الكروت ──
        cursor.execute(
            "EXEC sp_DashboardCard_bya @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        card_row = cursor.fetchone()
        cursor.nextset()

        if card_row:
            total_reports          = card_row.get('TotalConversations',    0) or 0
            total_resolved         = card_row.get('Resolved',              0) or 0
            total_unresolved       = card_row.get('Unresolved',            0) or 0
            total_unspecified      = card_row.get('NotDefined',            0) or 0
            total_customers        = card_row.get('TotalCustomers',        0) or 0
            avg_resolution_overall = round(card_row.get('AvgResolutionMinutes', 0) or 0)
        else:
            total_reports = total_resolved = total_unresolved = total_unspecified = total_customers = avg_resolution_overall = 0

        resolved_pct    = round(total_resolved    / total_reports * 100) if total_reports else 0
        unresolved_pct  = round(total_unresolved  / total_reports * 100) if total_reports else 0
        unspecified_pct = round(total_unspecified / total_reports * 100) if total_reports else 0

        # ── 2. Top Agents ──
        cursor.execute(
            "EXEC Top_Agent_resolved_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw_agents = cursor.fetchall() or []
        top_agents_resolved = [
            {
                'agent_name':   r.get('agent_name',   ''),
                'total':        r.get('TotalProblems', 0) or 0,
                'resolved':     r.get('Resolved',      0) or 0,
                'unresolved':   r.get('Unresolved',    0) or 0,
                'unspecified':  r.get('NotDefined',    0) or 0,
                'avg':          round(r.get('Avg_Resolution_Time', 0) or 0),
            }
            for r in raw_agents
        ][:4]
        avg_resolution_by_agent = [
            {'name': a['agent_name'], 'avg': a['avg']}
            for a in top_agents_resolved
        ]
        cursor.nextset()

        # ── 3. Top Customers ──
        cursor.execute(
            "EXEC Top_Customer_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw_customers = cursor.fetchall() or []
        top_customers = [
            {
                'customer_name': r.get('customer_name', ''),
                'total':         r.get('TotalContacts',  0) or 0,
            }
            for r in raw_customers
        ]
        cursor.nextset()

        # ── 4. Most Common Issues ──
        cursor.execute(
            "EXEC Top_Common_Issues_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw_issues = cursor.fetchall() or []
        common_problems = [
            {
                'classification': r.get('category_name', ''),
                'category_id':    r.get('category_id', ''),
                'total':          r.get('TotalIssues',   0) or 0,
            }
            for r in raw_issues
        ]
        cursor.nextset()

        # ── 5. Traffic by Date ──
        cursor.execute(
            "EXEC sp_TrafficByDate_bya @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw_traffic = cursor.fetchall() or []
        traffic_by_date = [
            {
                'date':  f"{str(r['resolve_date'])[6:8]}/{str(r['resolve_date'])[4:6]}/{str(r['resolve_date'])[:4]}",
                'count': r.get('total', 0) or 0,
            }
            for r in raw_traffic
        ]
        cursor.nextset()

        conn.close()

        return render(request, 'dashboard/home.html', {
            **base_ctx,
            'total_reports':           total_reports,
            'total_resolved':          total_resolved,
            'total_unresolved':        total_unresolved,
            'total_unspecified':       total_unspecified,
            'total_customers':         total_customers,
            'top_agents_resolved':     top_agents_resolved,
            'top_customers':           top_customers,
            'common_problems':         common_problems,
            'resolved_pct':            resolved_pct,
            'unresolved_pct':          unresolved_pct,
            'unspecified_pct':         unspecified_pct,
            'traffic_by_date':         traffic_by_date,
            'avg_resolution_overall':  avg_resolution_overall,
            'avg_resolution_by_agent': avg_resolution_by_agent,
        })

    except Exception as e:
        logger.error("Dashboard DB error: %s", e, exc_info=True)
        return render(request, 'dashboard/home.html', {**base_ctx, **_empty_context()})