import frappe, os

page = frappe.get_doc('Page', 'lavanya-today')
print('Page name:', page.name)
print('Page module:', page.module)

from frappe.modules.utils import get_doc_path
doc_path = get_doc_path(page.module, 'Page', page.page_name)
print('Doc path:', doc_path)
for f in os.listdir(doc_path):
    fp = os.path.join(doc_path, f)
    print('  File:', f, os.path.getsize(fp))

js_file = os.path.join(doc_path, page.page_name + '.js')
if os.path.exists(js_file):
    with open(js_file) as f:
        content = f.read()
    print('\nJS has LavanyaService:', 'LavanyaService' in content)
    print('JS has frappe.require:', 'frappe.require' in content)
    print('JS first 100 chars:', content[:100])
