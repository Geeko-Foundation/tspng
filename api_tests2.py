import os
import uuid
import time
import requests
import datetime
"""
V0.2
this is a more complete transfer example, currently failing at a SCA test phase.
One time token needs to signed, and the challenge needs to be cleared - at least for EUR - GBP transfers.
"""

# === CONFIG ================================================================
#API_TOKEN = os.getenv("WISE_API_TOKEN")  # set this in your env
API_TOKEN = "25d74ef1-ebd8-4468-a51a-c8efac6d79e8"
USE_SANDBOX = True                       # set False for production

BASE_URL = (
    "https://api.sandbox.transferwise.tech"
    if USE_SANDBOX else
    "https://api.transferwise.com"
)

# Currencies/amount for the example
#SOURCE_CURRENCY = "GBP"
#TARGET_CURRENCY = "EUR"
SOURCE_CURRENCY = "EUR"
TARGET_CURRENCY = "EUR"
SOURCE_AMOUNT   = 25.00                  # or set targetAmount instead

# Recipient details (example: EUR IBAN recipient)
RECIPIENT_CURRENCY = "EUR"
RECIPIENT_TYPE     = "iban"              # e.g., "iban", "sort_code", "swift_code", etc.
#RECIPIENT_CURRENCY = "EUR"
#RECIPIENT_TYPE     = "sort_code"              # e.g., "iban", "sort_code", "swift_code", etc.
RECIPIENT_NAME     = "John Doe"
RECIPIENT_IBAN     = "DE89370400440532013000"  # <-- put a valid IBAN for real runs

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

def find_existing_recipient(profile_id, currency, account_summary_hint=None):
    """Optional helper: scan existing recipients to avoid duplicates."""
    # This endpoint returns all recipients; for large lists, add your own filters/paging as needed.
    r = session.get(f"{BASE_URL}/v1/accounts?profile={profile_id}")
    data = _check(r, "GET /v1/accounts?profile")
    for acc in data:
        if acc.get("currency") == currency:
            if not account_summary_hint:
                return acc["id"]
            # crude match on summary text if provided
            if account_summary_hint.lower() in (acc.get("accountSummary","") + acc.get("longAccountSummary","")).lower():
                return acc["id"]
    return None

def create_recipient(profile_id, *, currency, account_holder_name, recipient_type, **details):
    """Create a recipient (beneficiary). The 'details' fields depend on the route."""
    body = {
        "profile": profile_id,
        "currency": currency,
        "type": recipient_type,
        "accountHolderName": account_holder_name,
        "ownedByCustomer": True,
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

'''
def fund_transfer(profile_id, transfer_id, funding_type="BALANCE"):
    """Fund the transfer (for balance-funded flows)."""
    body = {"type": funding_type}
    print(profile_id)
    print(transfer_id)
    r = session.post(f"{BASE_URL}/v3/profiles/{profile_id}/transfers/{transfer_id}/payments", json=body)
    return _check(r, "POST /v3/profiles/{profile_id}/transfers/{transfer_id}/payments")
'''

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


def _ott_get_status(session, base_url, ott):
    r = session.get(f"{base_url}/v1/one-time-token/status",
                    headers={"One-Time-Token": ott})
    print(r.json())
    r.raise_for_status()
    return r.json()["oneTimeTokenProperties"]  # { oneTimeToken, challenges: [...], validity }

def _ott_trigger_sms(session, base_url, ott):
    r = session.post(f"{base_url}/v1/one-time-token/sms/trigger",
                     headers={"One-Time-Token": ott})
    r.raise_for_status()
    # optional: r.json().get("obfuscatedPhoneNo")
    return True

def _ott_verify_sms(session, base_url, ott, otp_code):
    r = session.post(f"{base_url}/v1/one-time-token/sms/verify",
                     headers={"One-Time-Token": ott},
                     json={"otpCode": str(otp_code)})
    r.raise_for_status()
    return r.json()["oneTimeTokenProperties"]

def _ott_clear_required_challenges(session, base_url, ott, *, otp_provider=None, wait_secs=1):
    """
    Clears the challenges listed on the OTT.
    Currently implements the SMS path. You can extend with WHATSAPP/VOICE, PIN, device fingerprint, etc.
    """
    props = _ott_get_status(session, base_url, ott)
    challenges = props.get("challenges", [])
    print('clearing challenges')
    # nothing to clear
    if not challenges:
        print("No challenges to clear.")
        return props

    # scan for an SMS challenge
    has_sms = any(c.get("type") == "SMS" for c in challenges)
    if has_sms:
        print("Clearing SMS challenge.")

        _ott_trigger_sms(session, base_url, ott)

        # In SANDBOX the OTP is always 111111. In PROD, supply via otp_provider()
        otp = "111111" if otp_provider is None else otp_provider()
        props = _ott_verify_sms(session, base_url, ott, otp)
        challenges = props.get("challenges", [])

    # add other challenge handlers here (WHATSAPP/VOICE similar to SMS).
    # NOTE: Some challenges (e.g., PIN or partner-device-fingerprint) require JOSE-encrypted payloads.
    # See Wise JOSE guidance if you need those.

    if challenges:
        # If more than one challenge is required, loop again (rare).
        time.sleep(wait_secs)
        return _ott_clear_required_challenges(session, base_url, ott, otp_provider=otp_provider, wait_secs=wait_secs)

    return props

def fund_transfer_with_ott(session, base_url, profile_id, transfer_id, funding_type="BALANCE", otp_provider=None):
    """
    Attempts to fund a transfer and completes SCA using OTT if required.
    Returns the JSON of the successful funding call.
    """
    url = f"{base_url}/v3/profiles/{profile_id}/transfers/{transfer_id}/payments"
    body = {"type": funding_type}

    # 1) try normal funding first
    r = session.post(url, json=body)
    print('fund_transfer_with_ott: '+str(r.status_code))
    if r.status_code != 403:
        r.raise_for_status()
        return r.json()

    # 2) extract OTT from 403 headers
    ott = r.headers.get("x-2fa-approval")
    print(ott)
    print("TRACE ID: "+r.headers.get("x-trace-id"))
    result = r.headers.get("x-2fa-approval-result")  # e.g., REJECTED/APPROVED
    if not ott:
        raise RuntimeError("SCA required, but server did not return One-Time-Token (x-2fa-approval).")

    # 3) if already approved (some setups), just retry with OTT
    if result == "APPROVED":
        print('approved')
        r = session.post(url, json=body, headers={"One-Time-Token": ott})
        r.raise_for_status()
        return r.json()

    # 4) otherwise, clear challenges on this OTT (SMS in this example)
    _ott_clear_required_challenges(session, base_url, ott, otp_provider=otp_provider)

    # 5) retry the funding with the OTT
    r = session.post(url, json=body, headers={"One-Time-Token": ott})
    r.raise_for_status()
    return r.json()


def get_transfer(transfer_id):
    r = session.get(f"{BASE_URL}/v1/transfers/{transfer_id}")
    return _check(r, "GET /v1/transfers/{id}")

def main():
    profile_id, profile_type = get_profiles()
    print(f"Using profile {profile_id} ({profile_type})")

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
    recipient_id = find_existing_recipient(profile_id, RECIPIENT_CURRENCY)
    if recipient_id:
        print("Reusing existing recipient:", recipient_id)
    else:
        # details fields depend on the route; for EUR, Wise expects an IBAN and legalType
        recipient_id = create_recipient(
            profile_id,
            currency=RECIPIENT_CURRENCY,
            account_holder_name=RECIPIENT_NAME,
            recipient_type=RECIPIENT_TYPE,
            legalType="PRIVATE",
            iban=RECIPIENT_IBAN,
        )
        print("Created recipient:", recipient_id)

    # 3) Create the transfer
    transfer = create_transfer(
        target_account_id=recipient_id,
        quote_uuid=quote_uuid,
        reference_text=REFERENCE_TEXT
    )
    transfer_id = transfer["id"]
    print("Transfer created:", transfer_id, "| status:", transfer.get("status"))

    # 4) Fund the transfer (from Wise balance)
    #funding = fund_transfer(profile_id, transfer_id, funding_type="BALANCE")
    #print("Funding status:", funding.get("status"), "| errorCode:", funding.get("errorCode"))
    print('funding with ott')
    resp = fund_transfer_with_ott(session, BASE_URL, profile_id, transfer_id, funding_type="BALANCE")
    print("Funding status:", resp.get("status"))
    # (Optional) Fetch final transfer state
    details = get_transfer(transfer_id)
    print("Final transfer state:", details.get("status"))

if __name__ == "__main__":
    main()
