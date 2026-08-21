from datetime import datetime

deployment = {
    'service_url': 'http://54.86.13.231:8000',
    'api_docs': 'http://54.86.13.231:8000/docs',
    'health_check': 'http://54.86.13.231:8000/health',
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
}

print('\n' + '='*80)
print('MARBLO 배포 완료!')
print('='*80)
print(f'\n서비스 URL: {deployment["service_url"]}')
print(f'API 문서: {deployment["api_docs"]}')
print(f'헬스 체크: {deployment["health_check"]}')
print(f'\n배포 시간: {deployment["timestamp"]}')
print(f'리전: us-east-1 (버지니아 북부)')
print(f'인스턴스: i-09f4386f2b588b52b')
print(f'탄력적 IP: 54.86.13.231')

print('\n' + '='*80)
print('예상 월간 운영 비용 (가족용)')
print('='*80)

costs = [
    ('EC2 t3.medium', 12, '자정-오전10시 종료 (60% 절감)'),
    ('RDS db.t3.micro', 0, 'AWS 프리티어 (12개월 무료)'),
    ('ElastiCache', 12, '캐시 서버'),
    ('S3 스토리지', 1, '10GB 기준'),
    ('CloudFront CDN', 2, '이미지 전송'),
    ('AWS Lambda', 0.10, 'EC2 스케줄 자동화'),
]

print('\n비용 분석:')
print('-' * 80)
total_usd = 0
for name, cost, note in costs:
    print(f'{name:25} ${cost:6.2f}/월  - {note}')
    total_usd += cost

print('-' * 80)
krw_rate = 1200
total_krw = int(total_usd * krw_rate)

print(f'\n월간 총 비용: ${total_usd:.2f} USD')
print(f'환산 (1USD={krw_rate}원): {total_krw:,} KRW')
print(f'연간 총 비용: ${total_usd*12:.2f} USD')

print('\n' + '='*80)
print('비용 최적화 적용:')
print('='*80)
print('1. EC2 스케줄: 자동 종료 매일 자정 (기존 $30 -> $12)')
print('2. RDS 프리티어: 첫 12개월 무료')
print('3. 최소 사양: t3 버스트 인스턴스')
print('4. 가족 전용 사용: 트래픽 최소화')

print('\n' + '='*80)


