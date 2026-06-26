# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaAccessoryItem(FrappeTestCase):
    def test_create(self):
        doc = frappe.get_doc({
            "doctype": "Lavanya Accessory Item",
            "item_name": "_Test Accessory",
            "qty": 1,
        })
        doc.insert()
        self.assertTrue(doc.name)
        doc.delete()
