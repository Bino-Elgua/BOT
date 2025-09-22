import json
import sys

try:
    with open('bandit-report.json', 'r') as f:
        report = json.load(f)
    
    high_issues = [r for r in report.get('results', []) if r.get('issue_severity') in ['HIGH', 'MEDIUM']]
    
    if high_issues:
        print('SECURITY ALERT: Found {} medium+ severity issues'.format(len(high_issues)))
        for issue in high_issues:
            print('- {}: {} (Line {})'.format(issue['test_name'], issue['issue_text'], issue['line_number']))
        sys.exit(1)
    else:
        print('✅ No medium+ severity security issues found')
except FileNotFoundError:
    print('⚠️ Bandit report not found, allowing pipeline to continue')
