# Copyright (c) 2022, Totrox & Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.background_jobs import enqueue
import json

from frappe.utils import now_datetime


def enqueue_execute(request):
    enqueue(
        method=execute,
        queue="short",
        timeout=10000,
        is_async=True,
        kwargs=request,
    )


def execute(kwargs):
    request = frappe.get_doc("Schedule Request", kwargs)
    if request.status in ["Processing", "Success"]:
        return
    frappe.db.set_value("Schedule Request", request.name, "status", "Processing")
    frappe.db.commit()
    try:
        if "." not in request.method:
            data = json.loads(request.data)
            data["doctype"] = request.method
            doc = frappe.get_doc(data)
            doc.save(ignore_permissions=True)
            frappe.db.set_value("Schedule Request", request.name, "status", "Success")
            add_response(request, doc.as_dict(convert_dates_to_str=True))
        else:
            kwargs = json.loads(request.data)
            data_res = frappe.get_attr(request.method)(**kwargs)
            add_response(request, json.dumps(data_res))
    except Exception as e:
        # frappe.db.set_value("Schedule Request", request.name, "status", "Faild")
        # frappe.log_error(frappe.get_traceback(), str(e))
        request.reload()
        request.status = "Failed"
        error = request.append("errors", {})
        error.time_stamp = now_datetime()
        error.error = str(e)[0:140]
        error.traceback = frappe.get_traceback()
        request.save(ignore_permissions=True)
        frappe.db.commit()


def add_response(request, data):
    response = frappe.new_doc("Schedule Response")
    response.schedule_request = request.name
    response.status = "Pending"
    response.method = request.method
    response.tag = request.tag
    response.callback_url = request.callback_url
    response.callback_profile = request.callback_profile
    response.reference_id = request.reference_id
    response.data = json.dumps(data, indent=4)
    if not response.callback_url:
        response.callback_url = frappe.get_value(
            "Callback Profile", response.callback_profile, "callback_url"
        )
    response.insert(ignore_permissions=True)
    frappe.db.commit()
