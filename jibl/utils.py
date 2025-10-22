import frappe
from frappe.utils import validate_json_string
from frappe import _
from frappe.utils import now_datetime
from frappe.exceptions import AuthenticationError, ValidationError, PermissionError
from frappe.contacts.doctype.address.address import get_address_display
# def create_sales_invoice(data,headers):
#     if __authenticate_request():
#         try:
#             # ---- 1. Authenticate & authorize user ----
#             origin = frappe.get_request_header("Origin") or frappe.get_request_header("Host")
#             __authenticate_request(required_role="Insurance API", origin=origin)
#             frappe.logger("integration").info(f"Invoice request from {frappe.session.user}")

#             # ---- 2. Parse and validate incoming payload ----
#             if not data:
#                 frappe.throw("No payload received", frappe.ValidationError)

#             customer = __get_customer(data.get("customer"))
#             items = data.get("items", [])
#             if not items:
#                 frappe.throw("No items found in payload", frappe.ValidationError)

#             # ---- 3. Create Sales Invoice ----
#             si = frappe.new_doc("Sales Invoice")
#             si.customer = customer
#             si.posting_date = frappe.utils.nowdate()
#             si.due_date = frappe.utils.nowdate()
#             si.company = data.get("company") or "Default Company"

#             # Add items
#             for item_data in items:
#                 item_code = __get_or_create_item(item_data)
#                 si.append("items", {
#                     "item_code": item_code,
#                     "qty": item_data.get("qty", 1),
#                     "rate": item_data.get("rate", 0),
#                 })

#             si.insert(ignore_permissions=True)
#             si.submit()

#             frappe.db.commit()
#             return {"status": "success", "invoice": si.name}

#         except Exception as e:
#             frappe.db.rollback()
#             frappe.log_error(frappe.get_traceback(), "Insurance API Error")
#             frappe.local.response.http_status_code = 400
#             return {"status": "error", "message": str(e)}

#     else:
#         frappe.throw("Cannot authenticate incoming request", frappe.AuthenticationError)


# def __get_customer(customer_name):
#     if frappe.db.exists("Customer", {"customer_name": customer_name}):
#         return customer_name
#     else:
#         customer = frappe.new_doc("Customer")
#         customer.customer_name = customer_name
#         customer.customer_type = "Company"
#         customer.territory = "India"
#         customer.insert(ignore_permissions=True)
#         return customer.name


# # -------------------------
# #  ITEM HANDLERS
# # -------------------------
# def __get_or_create_item(item_data):
#     item_code = item_data.get("item_code")

#     # Return existing item
#     if frappe.db.exists("Item", {"item_code": item_code}):
#         return item_code

#     # Create new item
#     item = frappe.new_doc("Item")
#     item.item_code = item_code
#     item.item_name = item_data.get("item_name", item_code)
#     item.item_group = __get_or_create_item_group("Insurance")
#     item.is_sales_item = 1
#     item.insert(ignore_permissions=True)
#     return item.item_code


# def __get_or_create_item_group(group_name):
#     if frappe.db.exists("Item Group", group_name):
#         return group_name
#     group = frappe.new_doc("Item Group")
#     group.item_group_name = group_name
#     group.parent_item_group = "All Item Groups"
#     group.insert(ignore_permissions=True)
#     return group.name

def __authenticate_request(required_role = "Insurance API",origin= None):
    user = frappe.session.user 
    roles = set(frappe.get_roles(user))
    if required_role and required_role in roles:
        return user
    else:
        frappe.throw(f"User {frappe.session.user} is not authorized for this transaction",frappe.PermissionError)


def create_channel_partner(headers: dict = None, payload: dict = None):
    """
    Creates a new Channel Partner record in ERPNext
    from an authenticated external request.
    Returns a REST-compliant JSON response.
    """
    try:
        # --- Authentication ---
        user = __authenticate_request()

        # --- Validate payload ---
        if not payload:
            frappe.log_error(
                title="Missing Request Payload",
                message="Incoming Channel Partner API payload is empty"
            )
            return __api_response(400, "error", "Missing request payload", "Payload cannot be empty")

        data = frappe.parse_json(payload)

        # --- Check if already exists ---
        existing_partner = __find_existing_partner(data)
        if existing_partner:
            updated_partner = __update_channel_partner(data)
            return updated_partner

        # --- Create new Partner ---
        partner = frappe.new_doc("Channel Partner")

        # Contact & Personal Info
        partner.first_name = data.get("first_name")
        partner.middle_name = data.get("middle_name")
        partner.last_name = data.get("last_name")
        partner.date_of_birth = data.get("date_of_birth")
        partner.email = data.get("email")
        partner.contact = __get_contact({
            "first_name": data.get("first_name"),
            "middle_name": data.get("middle_name"),
            "last_name": data.get("last_name"),
            "email": data.get("email"),
            "phone_number": data.get("phone_number"),
        })

        # Address
        if data.get("address"):
            partner.address = __get_address(data.get("address"))

        # Core Info
        partner.gender = data.get("gender")

        partner.zone = __get_zone(data.get("zone"))

        # KYC / Compliance
        partner.pan = data.get("pan")
        partner.aadhar = data.get("aadhar")
        partner.gst_certificate_number = data.get("gst_certificate_number")

        # Hierarchy
        partner.area_manager = data.get("area_manager")
        partner.area_manager_code = data.get("area_manager_code")
        partner.regional_manager = data.get("regional_manager")
        partner.regional_manager_code = data.get("regional_manager_code")
        partner.zonal_manager = data.get("zonal_manager")
        partner.zonal_manager_code = data.get("zonal_manager_code")
        partner.referrer = data.get("referrer")
        partner.referrer_code = data.get("referrer_code")
        partner.referral_source = data.get("referral_source")
        partner.level = data.get("level")

        # Training
        partner.training_partner_name = data.get("training_partner_name")
        partner.registration_date = data.get("registration_date")
        partner.training_start_datetime = data.get("training_start_datetime")
        partner.training_end_datetime = data.get("training_end_datetime")
        partner.training_duration = data.get("training_duration")
        partner.exam_passed_date = data.get("exam_passed_date")
        partner.exam_status_section = data.get("exam_status_section")

        # Scoring
        partner.gi_score = data.get("gi_score")
        partner.li_score = data.get("li_score")
        partner.gi_training_time = data.get("gi_training_time")
        partner.li_training_time = data.get("li_training_time")

        # Status
        partner.profile_status = data.get("profile_status")
        partner.onboard_status = data.get("onboard_status")
        partner.current_status = data.get("current_status")
        partner.remarks = data.get("remarks")

        # Mark check fields based on documents
        documents = data.get("documents") or {}
        for field in [
            "pan_uploaded",
            "aadhar_front_uploaded",
            "aadhar_back_uploaded",
            "cheque_uploaded",
            "gst_certificate_uploaded",
            "qualification_certificate_uploaded",
            "noc_uploaded",
        ]:
            setattr(partner, field, documents.get(field))

        # Insert Partner
        partner.flags.ignore_permissions = False
        partner.insert(ignore_permissions=False)

        # --- Success Response ---
        return __api_response(
            201,
            "success",
            f"Channel Partner {partner.name} created successfully.",
            created_by=user,
            partner=partner.name,
        )

    except AuthenticationError:
        return __api_response(401, "error", "Invalid or missing API credentials", "Authentication failed")
    except PermissionError:
        return __api_response(403, "error", "Permission denied", "User not authorized to perform this action")
    except ValidationError as e:
        frappe.log_error(title="Validation Error", message=frappe.get_traceback())
        return __api_response(422, "error", "Validation failed", str(e))
    except Exception as e:
        frappe.log_error(title="Unhandled API Error", message=frappe.get_traceback())
        return __api_response(500, "error", "Internal Server Error", str(e))

def __api_response(status_code, status, message, hint=None, **extra):
    """ REST API response wrapper."""
    response = {
        "status": status,
        "status_code": status_code,
        "message": message,
    }
    if hint:
        response["hint"] = hint
    response.update(extra)
    frappe.local.response["http_status_code"] = status_code
    return response


def __find_existing_partner(data):
    """Check for an existing Channel Partner by unique identifiers like PAN or Email."""
    filters = []
    if data.get("pan"):
        filters.append({"pan": data.get("pan")})
    if data.get("email"):
        filters.append({"email": data.get("email")})

    for filter in filters:
        partner = frappe.db.exists("Channel Partner", filter)
        if partner:
            return partner
    return None

def __get_zone(zone:str):
    """ """
    if zone and frappe.db.exists("Zone",zone.strip()):
        return zone.strip()
    else:
        zone_doc = frappe.new_doc("Zone")
        zone_doc.zone = zone.strip()
        zone_doc.insert(ignore_permissions=True)
        return zone_doc.name
def __get_contact(contact_data:dict):
    """Create or get a Contact record for a Channel Partner."""
    email_id = contact_data.get("email")
    
    if email_id:
        # exists just return the contact to be set in the channel partner 
        if frappe.db.exists("Contact Email",{"email_id":email_id}):
            return frappe.get_value("Contact Email",{"email_id":email_id},"parent")
        # create new contact 
        else:
            contact_doc = frappe.new_doc("Contact")
            contact_doc.first_name = contact_data.get("first_name")
            contact_doc.last_name = contact_data.get("last_name")
            contact_doc.append("email_ids",{"email_id":email_id})
            if contact_data.get("phone_number"):
                contact_doc.append("phone_nos",{"phone":contact_data.get("phone_number")})
            contact_doc.insert(ignore_permissions=True)
            return contact_doc.name
    else:
        frappe.log_error(title="Email not found",message= "Email Id not found in Channel Partner API Payload")
        return None

def __get_address(address_data: dict):
    """Create or get an Address record for a Channel Partner."""

    # Validate required fields
    required_fields = ["address_line1", "pincode"]
    for field in required_fields:
        if not address_data.get(field):
            frappe.log_error(f"Missing required address field: {field}", frappe.MandatoryError)
    filters_dict = {}
    
    for field in ["address_line1", "address_line2","city", "pincode", "state", "country"]:
        if address_data.get(field):
            filters_dict[field] = address_data.get(field)
    # Check if similar address exists
    existing_address = frappe.db.exists(
        "Address",
        filters_dict,
    )
    if existing_address:
        return existing_address  # return the existing address name

    # Create new Address doc
    address_doc = frappe.new_doc("Address")
    address_doc.address_title = f"{address_data.get('address_line_1')}, {address_data.get('city')}"
    address_doc.address_type = "Billing" 
    address_doc.address_line1 = address_data.get("address_line1")
    address_doc.address_line2 = address_data.get("address_line2")
    address_doc.city = address_data.get("city")
    address_doc.pincode = address_data.get("pincode")
    address_doc.state = address_data.get("state")
    address_doc.country = address_data.get("country")
    address_doc.address_title = address_doc.address_line1 + ", " + (address_doc.city or "")
    # Insert ignoring permissions so that API user can create via backend
    address_doc.insert(ignore_permissions=True)
    return address_doc.name

def __update_channel_partner(data):
    partner_name = __find_existing_partner(data)
    if not partner_name:
        return None  
    partner = frappe.get_doc("Channel Partner", partner_name)
    updated_fields = []
    # Check for changes in fields and update 
    for field in [
        "first_name", "middle_name", "last_name", "date_of_birth",
        "gender", "pan", "aadhar", "gst_certificate_number",
        "area_manager", "area_manager_code", "regional_manager", "regional_manager_code",
        "zonal_manager", "zonal_manager_code", "referrer", "referrer_code", "referral_source",
        "level", "training_partner_name", "registration_date", "training_start_datetime",
        "training_end_datetime", "training_duration", "exam_passed_date", "exam_status_section",
        "gi_score", "li_score", "gi_training_time", "li_training_time", "profile_status",
        "onboard_status", "current_status", "remarks"
    ]:
        new_value = data.get(field)
        if new_value and str(new_value) != str(getattr(partner, field)):
            setattr(partner, field, new_value)
            updated_fields.append(field)

    # Linked doctypes
    if data.get("address"):
        new_address = __get_address(data.get("address"))
        if new_address != partner.address:
            partner.address = new_address
            updated_fields.append("address")

    if data.get("email") or data.get("phone_number"):
        new_contact = __get_contact({
            "first_name": data.get("first_name"),
            "middle_name": data.get("middle_name"),
            "last_name": data.get("last_name"),
            "email": data.get("email"),
            "phone_number": data.get("phone_number")
        })
        if new_contact != partner.contact:
            partner.contact = new_contact
            updated_fields.append("contact")

    partner.zone = __get_zone(data.get("zone"))
    # Only save if something changed
    if updated_fields:
        try:
            partner.save(ignore_permissions=True)
            return __api_response(
                    status_code=201,
                    status = "success",
                    message=f"Channel Partner {partner.name} updated successfully.",
                    created_by=frappe.session.user,
                    partner=partner.name,
                    updated_fields=updated_fields
                )
        except Exception as e:
            frappe.log_error(title= "Channel Partner Update Error", message=frappe.get_traceback())
            return __api_response(
                status_code = 500,
                status= "error",
                message ="Failed to update Channel Partner",
                hint = str(e)
            )
    else:
        frappe.logger().info(f"No changes detected for Channel Partner {partner.name}")

