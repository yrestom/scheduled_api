# Copyright (c) 2022, Totrox & Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.background_jobs import enqueue
from frappe.utils import now_datetime
import json
import requests
from time import sleep


def enqueue_execute(request):
    enqueue(
        method=execute,
        queue="long",
        timeout=10000,
        is_async=True,
        kwargs=request,
    )


@frappe.whitelist()
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
            create_response(request, doc.as_dict(convert_dates_to_str=True))
        else:
            kwargs = json.loads(request.data)
            data_res = frappe.get_attr(request.method)(**kwargs)
            create_response(request, json.dumps(data_res))
    except Exception as e:
        request.reload()
        request.status = "Failed"
        error = request.append("errors", {})
        error.time_stamp = now_datetime()
        error.error = str(e)[0:140]
        error.traceback = frappe.get_traceback()
        request.save(ignore_permissions=True)
        frappe.db.commit()


def create_response(request, data):
    if isinstance(data, object):
        data = frappe._dict(data)
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
    if not response.callback_url:
        response.status = "Don't Send"
    response.insert(ignore_permissions=True)
    frappe.db.commit()
    if response.status == "Pending":
        enqueue_send_response(response.name)


def enqueue_send_response(response):
    enqueue(
        method=send_response,
        queue="short",
        timeout=10000,
        is_async=True,
        kwargs=response,
    )


def send_response(kwargs):
    response = frappe.get_doc("Schedule Response", kwargs)
    if response.status in ["Sending", "Success", "Don't Send"]:
        return
    if not response.callback_url:
        frappe.db.set_value("Schedule Request", response.name, "status", "Don't Send")
        frappe.db.commit()
        return
    frappe.db.set_value("Schedule Request", response.name, "status", "Sending")
    frappe.db.commit()
    headers = get_headers(response.callback_profile)
    data = {
        "data": response.data,
        "reference_id": response.reference_id,
        "request_id": response.schedule_request,
    }
    for i in range(3):
        r = {}
        try:
            r = requests.request(
                method="POST",
                url=response.callback_url,
                data=data,
                headers=headers,
                timeout=15,
            )
            r.raise_for_status()
            frappe.db.set_value("Schedule Response", response.name, "status", "Success")
            if r.text:
                frappe.db.set_value(
                    "Schedule Response", response.name, "response", r.text
                )
            frappe.db.commit()
            break
        except Exception as e:
            response.reload()
            response.status = "Failed"
            error = response.append("errors", {})
            error.time_stamp = now_datetime()
            error.error = str(e)[0:140]
            error.traceback = frappe.get_traceback()
            response.save(ignore_permissions=True)
            frappe.db.commit()
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e


def get_headers(profile=None):
    headers = {}
    if not profile:
        return {}
    profile = frappe.get_cached_doc("Callback Profile", profile)
    if profile.headers:
        for h in profile.headers:
            if h.get("key") and h.get("value"):
                headers[h.get("key")] = h.get("value")

    return headers


def process_all():
    request_list = frappe.get_all(
        "Schedule Request",
        filters={"status": ["in", ["Pending", "Failed"]]},
        pluck="name",
    )
    for request in request_list:
        enqueue_execute(request)
