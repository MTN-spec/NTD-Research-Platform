import os

files = ['gee_app.js', 'Untitled-1.js']
replaced_count = 0

for f in files:
    if not os.path.exists(f):
        continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace the text
    content = content.replace('Chinhoyi Irrigation Alert System', 'Optiflow Aqua Systems')
    content = content.replace('🌱 Chinhoyi', '💧 Optiflow')
    content = content.replace('Chinhoyi IrrigAlert', 'Optiflow Aqua Systems')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
    replaced_count += 1

print(f'Successfully updated {replaced_count} files.')
