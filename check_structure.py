import os
for root, dirs, files in os.walk('data/C001'):
    print(f'\nDirectory: {root}')
    print(f'Subdirs: {dirs}')
    print(f'Files: {files[:5] if files else []}')
