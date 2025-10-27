import os
import uuid
import time
import requests
import datetime
"""
V0.3 
This version should make the full transfer.  
NOTES:
 - Wise have advised me that due to our location - UK or Europe - we cannot make automatic transfers as we are not a bank.
 - Therefore we can start the processes as per normal, but then the final "funding" of the transfer is performed by a manual
   login to Wise.
 - However some of these steps need to be "simulated" in the sandbox api, presumably different outcomes need to be handled.
 - The Simulation API is found at: https://docs.wise.com/api-docs/api-reference/simulation
"""

# === CONFIG ================================================================
#API_TOKEN = os.getenv("WISE_API_TOKEN")  # set this in your env
API_TOKEN = "25d74ef1-ebd8-4468-a51a-c8efac6d79e8"
#API_TOKEN = "3f3d78dd-eb0f-401a-a3ce-3c10c9077233"
USE_SANDBOX = True                       # set False for production

BASE_URL = (
    "https://api.sandbox.transferwise.tech"
    if USE_SANDBOX else
    "https://api.transferwise.com"
)

# Currencies/amount for the example
#SOURCE_CURRENCY = "GBP"
#TARGET_CURRENCY = "EUR"
SOURCE_CURRENCY = "GBP"
TARGET_CURRENCY = "EUR"
SOURCE_AMOUNT   = 25.00                  # or set targetAmount instead

# Recipient details (example: EUR IBAN recipient)
RECIPIENT_CURRENCY = "EUR"
RECIPIENT_TYPE     = "iban"              # e.g., "iban", "sort_code", "swift_code", etc.
#RECIPIENT_CURRENCY = "EUR"
#RECIPIENT_TYPE     = "sort_code"              # e.g., "iban", "sort_code", "swift_code", etc.
RECIPIENT_NAME     = "Jane Doe"
RECIPIENT_IBAN     = "BE57 9677 4768 2935"
RECIPIENT_BIC      = "TRWIBEB1"
# Transfer metadata
REFERENCE_TEXT = os.getlogin()+" "+datetime.datetime.now().strftime("%Y%m%d")
# ==========================================================================

if not API_TOKEN:
    raise SystemExit("Please export WISE_API_TOKEN in your environment.")

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
})

def _check(resp, step):
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        # Show Wise error payloads nicely
        print(f"[{step}] HTTP {resp.status_code}:", resp.text)
        #raise
    return resp.json() if resp.text else {}

def get_profiles():
    """List profiles available to the token, then pick one (business preferred if present)."""
    r = session.get(f"{BASE_URL}/v1/profiles")
    data = _check(r, "GET /v1/profiles")
    if not isinstance(data, list) or not data:
        raise RuntimeError("No profiles returned.")
    # Prefer business profile if you have one; otherwise use personal
    business = next((p for p in data if p.get("type") == "business"), None)
    chosen = business or data[0]
    return chosen["id"], chosen["type"]

def list_balances(profile_id, types="STANDARD"):
    """
    Fetches the balances for a specified profile.

    This function retrieves the balance information for a given profile ID. The profile ID
    is required, and the type of balance to retrieve can also be specified. By default, the
    function retrieves "STANDARD" balances. Additional balance types such as "SAVINGS" can
    be included by providing a comma-separated string of types.

    :param profile_id: The unique identifier of the profile.
    :param types: A comma-separated string indicating the types of balances to retrieve.
                  Defaults to "STANDARD".
    :return: A dictionary containing the balance information for the specified profile.
    """
    url = f"{BASE_URL}/v4/profiles/{profile_id}/balances"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    params = {"types": types}  # e.g. "STANDARD" or "STANDARD,SAVINGS"
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()


def create_quote(profile_id, *, source_currency, target_currency, source_amount=None, target_amount=None, pay_out=None, preferred_pay_in="BALANCE", target_account=None):
    """Create an authenticated quote bound to your profile."""
    body = {
        "sourceCurrency": source_currency,
        "targetCurrency": target_currency,
        "sourceAmount": source_amount,
        "targetAmount": target_amount,
        "payOut": pay_out,               # usually None or "BANK_TRANSFER" (default)
        "preferredPayIn": preferred_pay_in,
        "targetAccount": target_account, # optional; can be set later
        # "paymentMetadata": {"transferNature": "..."}  # if required for specific corridors
    }
    r = session.post(f"{BASE_URL}/v3/profiles/{profile_id}/quotes", json=body)
    return _check(r, "POST /v3/profiles/{profileId}/quotes")

def create_recipient(profile_id, *, currency, account_holder_name, recipient_type, **details):
    """Create a recipient (beneficiary). The 'details' fields depend on the route."""
    body = {
        "profile": profile_id,
        "currency": currency,
        "type": recipient_type,
        "accountHolderName": account_holder_name,
        "ownedByCustomer": True,
        "iban": RECIPIENT_IBAN,
        "details": details
    }
    # Add an idempotency header to protect against accidental dupes on retries
    headers = {"X-idempotence-uuid": str(uuid.uuid4())}
    r = session.post(f"{BASE_URL}/v1/accounts", json=body, headers=headers)
    data = _check(r, "POST /v1/accounts")
    return data["id"]

def create_transfer(*, target_account_id, quote_uuid, reference_text=None, refund_recipient_id=None):
    """Create the transfer using the quote + recipient."""
    body = {
        "targetAccount": target_account_id,
        "quoteUuid": quote_uuid,
        "customerTransactionId": str(uuid.uuid4()),  # required idempotency token
        "details": {
            "reference": reference_text or ""
            # Add corridor-specific requirements when indicated by the API
            # e.g., "transferPurpose": "...", "sourceOfFunds": "..."
        }
    }
    if refund_recipient_id:
        body["sourceAccount"] = refund_recipient_id

    r = session.post(f"{BASE_URL}/v1/transfers", json=body)
    return _check(r, "POST /v1/transfers")

def fund_transfer(profile_id, transfer_id, funding_type="BALANCE"):
    body = {"type": funding_type}
    r = session.post(f"{BASE_URL}/v3/profiles/{profile_id}/transfers/{transfer_id}/payments", json=body)
    print('fund_transfer '+str(r.status_code))
    if r.status_code == 403:
        # Wise returns OTT details in these headers
        approval = r.headers.get("x-2fa-approval-result")
        print('approval code: '+str(approval))
        ott = r.headers.get("x-2fa-approval")
        print('ott: '+str(ott))
        if approval == "APPROVED":
            # Retry immediately with the OTT
            r = session.post(
                f"{BASE_URL}/v3/profiles/{profile_id}/transfers/{transfer_id}/payments",
                json=body,
                headers={"One-Time-Token": ott}
            )
        elif ott:
            # You must clear the challenges for this OTT, then retry with One-Time-Token
            raise RuntimeError(f"SCA required. Complete challenges for OTT={ott} and retry this call with header One-Time-Token.")
        else:
            raise RuntimeError("SCA required but OTT headers missing. Check auth setup (client-credentials + mTLS avoids SCA).")

    r.raise_for_status()
    return r.json()

def get_transfer(transfer_id):
    r = session.get(f"{BASE_URL}/v1/transfers/{transfer_id}")
    return _check(r, "GET /v1/transfers/{id}")

def simulate_user(transfer_id):
    """
    Simulate user interaction with the website.
    """
    r = session.get(f"{BASE_URL}/v1/simulation/transfers/{transfer_id}/processing")
    rj = r.json()
    print("TRACE ID: "+r.headers.get("x-trace-id"))
    if r.status_code == 200:
        print(str(r.status_code)+' processing: '+rj['status'])
    else:
        print(str(r.status_code)+': '+str(rj['errors'][0]['message']))

    time.sleep(10)
    r = session.get(f"{BASE_URL}/v1/simulation/transfers/{transfer_id}/funds_converted")
    rj = r.json()
    if r.status_code == 200:
        print(str(r.status_code)+' converted '+': '+rj['status'])
    else:
        print(str(r.status_code)+': '+str(rj['errors'][0]['message']))
    time.sleep(10)
    r = session.get(f"{BASE_URL}/v1/simulation/transfers/{transfer_id}/outgoing_payment_sent")
    rj = r.json()
    if r.status_code == 200:
        print(str(r.status_code)+' payment transfer complete. '+': '+rj['status'])
    else:
        print(str(r.status_code)+': '+str(rj['errors'][0]['message']))
    return _check(r, "GET /v1/transfers/{id}")

def main(transfer_id=None):
    if not transfer_id:
        profile_id, profile_type = get_profiles()
        print(f"Using profile {profile_id} ({profile_type})")

        '''get balances for each profile'''
        balances = list_balances(profile_id=profile_id, types="STANDARD")
        for b in balances:
            print(f"{b['currency']} | balanceId={b['id']} | amount={b['amount']['value']}")
        # 1) Create an authenticated quote (bound to your profile)
        quote = create_quote(
            profile_id,
            source_currency=SOURCE_CURRENCY,
            target_currency=TARGET_CURRENCY,
            source_amount=SOURCE_AMOUNT,
            target_amount=None
        )
        quote_uuid = quote["id"]
        print("Quote:", quote_uuid, "| payOut:", quote.get("payOut"), "| rate:", quote.get("rate"))

        # 2) Create (or reuse) a recipient account
        recipient_id = create_recipient(
            profile_id,
            currency=RECIPIENT_CURRENCY,
            account_holder_name=RECIPIENT_NAME,
            recipient_type=RECIPIENT_TYPE,
            legalType="PRIVATE",
            iban=RECIPIENT_IBAN,
        )
        print("Created / found recipient: ", recipient_id)

        # 3) Create the transfer
        transfer = create_transfer(
            target_account_id=recipient_id,
            quote_uuid=quote_uuid,
            reference_text=REFERENCE_TEXT
        )
        transfer_id = transfer["id"]
        print("Transfer created:", transfer_id, "| status:", transfer.get("status"))
    else:
        print("Resuming failed transfer...")
    # 4) SIMULATE the funding of the transfer (from Wise balance)
    simulate_user(transfer_id)

if __name__ == "__main__":
    main()
