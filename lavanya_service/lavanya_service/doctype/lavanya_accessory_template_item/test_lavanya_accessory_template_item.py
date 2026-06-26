# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaAccessoryTemplateItem(FrappeTestCase):
    def test_create(self):
        doc = frappe.get_doc({
            "doctype": "Lavanya Accessory Template Item",
            "accessory_name": "_Test Accessory",
            "quantity": 1,
            "is_mandatory": 1,
        })
        doc.insert()
        self.assertTrue(doc.name)
        doc.delete()
