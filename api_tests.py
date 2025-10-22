import requests, uuid

# Replace this with your API token (Bearer token)
ACCESS_TOKEN = "25d74ef1-ebd8-4468-a51a-c8efac6d79e8"

# Choose sandbox or production URL
BASE_URL = "https://api.sandbox.transferwise.tech"  # or https://api.transferwise.com

def auth_headers(json=True):
    h = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    if json: h["Content-Type"] = "application/json"
    return h

def get_profiles():
    """
    Fetches a list of user profiles from the API.

    This function sends a GET request to the API endpoint for profiles using the
    provided base URL and access token. It returns the list of profiles as a JSON
    object. If the request fails or if the response status is not successful, it
    raises an HTTP error.

    :raises HTTPError: If the HTTP request returns an unsuccessful status code.

    :return: A list of user profiles in JSON format.
    :rtype: dict
    """
    url = f"{BASE_URL}/v2/profiles"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    profiles = response.json()
    return profiles

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
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {"types": types}  # e.g. "STANDARD" or "STANDARD,SAVINGS"
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()

def create_quote(profile_id,
                source_currency,
                target_currency,
                source_amount=None,
                target_amount=None,
                pay_in="BALANCE",   # use "BALANCE" if funding from Wise balance
                pay_out="BANK_TRANSFER"): # other options: "BALANCE", "SWIFT", "SWIFT_OUR", "INTERAC"
    """
    Creates a payment quote based on the provided profile ID, source, and target
    currencies, and either source or target amount. This quote is used to
    represent the details of a transaction according to the provided parameters.

    :param profile_id: The unique identifier for the profile initiating the
        transaction.
    :type profile_id: str
    :param source_currency: The currency of the amount to be converted. Should
        be a valid ISO currency code.
    :type source_currency: str
    :param target_currency: The currency into which the amount will be converted.
        Should be a valid ISO currency code.
    :type target_currency: str
    :param source_amount: The amount in the source currency to be converted. Must
        not be provided if `target_amount` is specified (optional).
    :type source_amount: float, optional
    :param target_amount: The amount in the target currency expected after
        conversion. Must not be provided if `source_amount` is specified (optional).
    :type target_amount: float, optional
    :param pay_in: The method for funding the transaction. Defaults to "BALANCE".
        Other valid options include "SWIFT", "SWIFT_OUR", "INTERAC".
    :type pay_in: str, optional
    :param pay_out: The payout method for the transaction. Defaults to
        "BANK_TRANSFER". Other valid options include "BALANCE".
    :type pay_out: str, optional
    :return: The response from the Wise API containing the details of the
        created quote.
    :rtype: dict
    :raises AssertionError: If neither `source_amount` nor `target_amount` is provided,
        or if both are provided.
    :raises HTTPError: If the API request fails with a non-successful HTTP
        status code.
    """
    assert (source_amount is None) ^ (target_amount is None), "Provide exactly one of source_amount or target_amount"
    url = f"{BASE_URL}/v3/profiles/{profile_id}/quotes"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "profileId": profile_id,
        "sourceCurrency": source_currency,
        "targetCurrency": target_currency,
        "payIn": pay_in,
        "payOut": pay_out
    }
    if source_amount is not None:
        body["sourceAmount"] = source_amount
    if target_amount is not None:
        body["targetAmount"] = target_amount
    r = requests.post(url, headers=headers, json=body)
    r.raise_for_status()
    return r.json()

def create_recipient(profile_id, account_holder_name, currency="GBP",
                     sort_code="040075", account_number="37778842"):
    """
    Creates a recipient for a transfer.

    This function is used to register a recipient account, enabling transfers
    to the provided recipient.

    :param profile_id: The unique identifier of the profile creating the recipient.
    :type profile_id: str
    :param account_holder_name: The name of the account holder.
    :type account_holder_name: str
    :param currency: The currency of the recipient account, defaults to "GBP".
    :type currency: str, optional
    :param sort_code: The sort code of the recipient's bank, defaults to "040075".
    :type sort_code: str, optional
    :param account_number: The account number of the recipient, defaults to "37778842".
    :type account_number: str, optional
    :return: The response from the API containing the recipient account ID.
    :rtype: dict
    :raises requests.HTTPError: If the API request for creating a recipient fails.
    """
    url = f"{BASE_URL}/v1/accounts"
    body = {
        "profile": profile_id,
        "currency": currency,
        "type": "sort_code",                   # varies by currency (e.g., "iban" for EUR)
        "accountHolderName": account_holder_name,
        "ownedByCustomer": True,
        "details": {
            "legalType": "PRIVATE",
            "sortCode": sort_code,
            "accountNumber": account_number
        }
    }
    r = requests.post(url, headers=auth_headers(), json=body)
    r.raise_for_status()
    return r.json()          # contains recipient account "id"

def create_transfer(profile_id, quote_uuid, recipient_account_id,
                    reference="Invoice 123", source_account_id=None):
    """
    Creates a transfer using the specified profile ID, quote UUID, recipient account ID,
    reference, and optionally a source account ID. This operation posts transfer details
    to a remote API endpoint and returns the response.

    :param profile_id: The ID of the user's profile initiating the transfer.
    :type profile_id: str
    :param quote_uuid: The unique identifier of the quote associated with the transfer.
    :type quote_uuid: str
    :param recipient_account_id: The identification of the target account for the transfer.
    :type recipient_account_id: str
    :param reference: A reference string for the transfer, such as an invoice number. Defaults to "Invoice 123".
    :type reference: str, optional
    :param source_account_id: An optional ID representing the source or refund account.
    :type source_account_id: str, optional
    :return: The response JSON from the API containing details of the created transfer.
    :rtype: dict
    :raises HTTPError: If the API request results in an unsuccessful HTTP response status.
    """
    url = f"{BASE_URL}/v1/transfers"
    body = {
        "targetAccount": recipient_account_id,
        "quoteUuid": quote_uuid,               # v3/v2 quote id field
        "customerTransactionId": str(uuid.uuid4()),
        "details": {"reference": reference}
    }
    if source_account_id:
        body["sourceAccount"] = source_account_id  # refund recipient (optional, depends on route/model)
    r = requests.post(url, headers=auth_headers(), json=body)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        print("Funding failed:", r.status_code, r.text)  # <-- shows the real reason (SCA needed? not owner? etc.)
        #raise
    return r.json()


def fund_transfer_from_balance(profile_id, transfer_id):
    """
    Initiates a fund transfer operation using balance for a given transfer.

    This function facilitates transferring funds from a balance to fulfill a
    specific transfer request associated with a profile and transfer ID.

    :param profile_id: The unique identifier of the profile for the transfer.
    :type profile_id: str
    :param transfer_id: The unique identifier of the transfer to be funded.
    :type transfer_id: str
    :return: The response from the API in JSON format.
    :rtype: dict
    :raises requests.HTTPError: If the request to fund transfer fails due to
        reasons such as insufficient permissions, insufficient balance, or
        other errors outlined by the request error response.
    """
    url = f"{BASE_URL}/v3/profiles/{profile_id}/transfers/{transfer_id}/payments"
    body = {"type": "BALANCE"}
    r = requests.post(url,
                      headers={**auth_headers(),
                      "Accept-Minor-Version": "1",
                      "X-idempotence-uuid": str(uuid.uuid4())},
                      json=body)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        print("Funding failed:", r.status_code, r.text)  # <-- shows the real reason (SCA needed? not owner? etc.)
        #raise
    return r.json()

def get_account_requirements(quote_id):
    """
    Fetches account requirements for the specified quote.

    This function sends a GET request to retrieve account requirements associated
    with a specific quote ID. It uses a base URL and appends the path for
    account requirements. The request is authenticated with headers and indicates
    a specific API minor version.

    :param quote_id: The unique identifier of the quote for which account
        requirements are fetched (str).
    :return: The account requirements data as JSON (dict).
    :rtype: dict
    :raises requests.exceptions.HTTPError: If the HTTP request fails or returns
        an unsuccessful status code.
    """
    url = f"{BASE_URL}/v1/quotes/{quote_id}/account-requirements"
    r = requests.get(url, headers={**auth_headers(False), "Accept-Minor-Version": "1"})
    r.raise_for_status()
    return r.json()

def get_activities(profile_id):
    """
    Fetches a list of activities for a given profile from the external API.

    This function retrieves activities associated with the specified profile
    by making a request to the defined external API endpoint. The response
    contains a structured representation of activities data as returned by
    the API.

    :param profile_id: The unique identifier for the profile whose activities
                       are to be retrieved.
    :type profile_id: str
    :return: A JSON object or list detailing the activities retrieved from
             the API for the specified profile.
    :rtype: dict | list
    """
    url = f"{BASE_URL}/v1/profiles/{profile_id}/activities"
    r = requests.get(url, headers={**auth_headers(False), "Accept-Minor-Version": "1"})
    #r.raise_for_status()
    #for a in r.json():
    #    print(a)
    return r.json()

if __name__ == "__main__":
    '''
    make it all happen
    '''
    profiles = get_profiles()
    # cheat for testing transfer
    person_profile = profiles[0] #['id']
    business_profile = profiles[1] #['id']
    for profile in profiles:
        print(f"Profile ID: {profile['id']}")
        print(f"Type: {profile['type']}")
        '''get balances for each profile'''
        balances = list_balances(profile_id=profile['id'], types="STANDARD")
        for b in balances:
            print(f"{b['currency']} | balanceId={b['id']} | amount={b['amount']['value']}")

        '''make a quote'''
        quote = create_quote(
            profile_id=profile['id'],
            source_currency="EUR",
            target_currency="GBP",
            source_amount=10.00,  # send 10 EUR
            pay_in="BALANCE",  # pricing aligned with balance funding
            pay_out="BANK_TRANSFER"  # payout to recipient bank
        )

        account_requirements = get_account_requirements(quote["id"])
        print("-" * 40)

        '''get profile details'''
        if profile['type'] == 'PERSONAL':
            print(f"Full name: {profile['firstName']} {profile['lastName']}")
            print('transferring EUR to EUR:')
            print("Quote ID:", quote["id"])
            print("Rate:", quote["rate"])
            # transfer to company account?
            #recipient = create_recipient(profile['id'], "Willis and Co 6942")
            recipient = business_profile
            #transfer = create_transfer(profile['id'], quote['id'], recipient['id'], reference="I owe you")
            #print("Transfer created:", transfer['id'], transfer.get("status"))
            #funding = fund_transfer_from_balance(profile['id'], transfer['id'])
            #print("Funding result:", funding)
            #print("Estimated target amount:", quote.get("paymentOptions", [{}])[0].get("targetAmount"))
        else:
            print(f"Company Details: {profile['businessName']}")
            print('transferring EUR to GBP:')
            print("Quote ID:", quote["id"])
            print("Rate:", quote["rate"])
            #recipient = create_recipient(profile['id'], "Mr Money Bags")
            recipient = create_recipient(profile['id'], "John Doe")
            #recipient = person_profile
            transfer = create_transfer(profile['id'], quote['id'], recipient['id'], reference="April payroll")
            print("Transfer created:", transfer['id'], transfer.get("status"))
            funding = fund_transfer_from_balance(profile['id'], transfer['id'])
            print("Funding result:", funding)
            print("Estimated target amount:", quote.get("paymentOptions", [{}])[0].get("targetAmount"))
        print("-" * 40)
        print('\n')
