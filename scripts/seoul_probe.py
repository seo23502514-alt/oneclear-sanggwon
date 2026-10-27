#!/usr/bin/env python3
"""서울 열린데이터광장 상권분석서비스 OpenAPI 항목 확인 (sample 키, 5줄)"""
import json, os, requests
KEY = os.environ.get('SEOUL_KEY') or 'sample'
for svc in ['VwsmTrdarSelngQq', 'VwsmTrdarFlpopQq', 'VwsmTrdarWrcPopltnQq', 'TbgisTrdarRelm', 'VwsmTrdarRepopQq', 'VwsmTrdarStorQq']:
    for path in [f'{svc}/1/5/', f'{svc}/1/5/20262', f'{svc}/1/5/20261']:
        url = f'http://openapi.seoul.go.kr:8088/{KEY}/json/{path}'
        try:
            d = requests.get(url, timeout=40).json()
        except Exception as e:
            print(svc, path, 'ERR', e); continue
        b = d.get(svc) or {}
        print('##', path, 'total', b.get('list_total_count'), d.get('RESULT') or b.get('RESULT'))
        rows = b.get('row') or []
        if rows: print('  cols', list(rows[0].keys())); print('  ex', json.dumps(rows[0], ensure_ascii=False)[:900])
