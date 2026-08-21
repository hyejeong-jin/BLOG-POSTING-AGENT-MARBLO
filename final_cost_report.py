from datetime import datetime

deployment = {
    'service_url': 'http://54.86.13.231:8000',
    'api_docs': 'http://54.86.13.231:8000/docs',
    'health_check': 'http://54.86.13.231:8000/health',
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
}

print('\n' + '='*80)
print('MARBLO ���� �Ϸ�!')
print('='*80)
print(f'\n���� URL: {deployment["service_url"]}')
print(f'API ����: {deployment["api_docs"]}')
print(f'�ｺ üũ: {deployment["health_check"]}')
print(f'\n���� �ð�: {deployment["timestamp"]}')
print(f'����: us-east-1 (�����Ͼ� �Ϻ�)')
print(f'�ν��Ͻ�: i-09f4386f2b588b52b')
print(f'ź���� IP: 54.86.13.231')

print('\n' + '='*80)
print('���� ���� � ��� (������)')
print('='*80)

costs = [
    ('EC2 t3.medium', 12, '����-����10�� ���� (60% ����)'),
    ('RDS db.t3.micro', 0, 'AWS ����Ƽ�� (12���� ����)'),
    ('ElastiCache', 12, 'ĳ�� ����'),
    ('S3 ���丮��', 1, '10GB ����'),
    ('CloudFront CDN', 2, '�̹��� ����'),
    ('AWS Lambda', 0.10, 'EC2 ������ �ڵ�ȭ'),
]

print('\n��� �м�:')
print('-' * 80)
total_usd = 0
for name, cost, note in costs:
    print(f'{name:25} ${cost:6.2f}/��  - {note}')
    total_usd += cost

print('-' * 80)
krw_rate = 1200
total_krw = int(total_usd * krw_rate)

print(f'\n���� �� ���: ${total_usd:.2f} USD')
print(f'ȯ�� (1USD={krw_rate}��): {total_krw:,} KRW')
print(f'���� �� ���: ${total_usd*12:.2f} USD')

print('\n' + '='*80)
print('��� ����ȭ ����:')
print('='*80)
print('1. EC2 ������: �ڵ� ���� ���� ���� (���� $30 -> $12)')
print('2. RDS ����Ƽ��: ù 12���� ����')
print('3. �ּ� ���: t3 ����Ʈ �ν��Ͻ�')
print('4. ���� ���� ���: Ʈ���� �ּ�ȭ')

print('\n' + '='*80)


