import sys
sys.path.append('src')

from ingestion import ingest_all_files

data = ingest_all_files('data')

print(f'\nTotal files ingested: {len(data)}')

brokers = {}
for d in data:
    key = (d['client_id'], d['broker'])
    brokers[key] = brokers.get(key, 0) + 1

print('\nFiles by client and broker:')
for (c, b), count in sorted(brokers.items()):
    print(f'  {c} - {b}: {count} files')
