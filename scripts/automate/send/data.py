from datetime import datetime
from config import PORT_DB, PORT_HY, URL_DB, URL_HY
from send.utils import generate_end_to_end_identification, generate_uuid  # Importar funciones necesarias
from constants import paymentId  # Importar paymentId desde constants.py

# Crear datos de la transferencia
def create_data(debtor_name, debtor_iban, debtor_currency, debtor_address, instructed_amount, creditor_name, creditor_iban, creditor_currency, creditor_bank, creditor_agent, creditor_address, payment_type, paymentId):
    return {
        "debtorAccount": {
            "currencyCode": debtor_currency,
            "iban": debtor_iban
        },
        "instructedAmount": {
            "amount": float(instructed_amount),
            "currencyCode": debtor_currency
        },
        "creditorName": creditor_name,
        "creditorAccount": {
            "currencyCode": creditor_currency,
            "iban": creditor_iban
        },
        "creditorBank": creditor_bank,
        "creditorAgent": creditor_agent,
        "creditorAddress": creditor_address,
        "debtorName": debtor_name,
        "debtorBank": "DEUTSCHE BANK",
        "debtorAgent": "DEUTDEFFXXX",
        "debtorAddress": debtor_address,
        "remittanceInformationUnstructured": "JN2DKYS-LNS-K",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "paymentType": payment_type,
        "endToEndIdentification": generate_end_to_end_identification(paymentId)
    }

debtor_address = {
    "buildingNumber": "1",
    "city": "FRANKFURT",
    "country": "DE",
    "postalCode": "60325",
    "street": "TAUNUSANLAGE"
}

creditor_addresses = {
    "DATA_01": {
        "buildingNumber": "1",
        "city": "MADRID",
        "country": "ES",
        "postalCode": "28001",
        "street": "PASEO DE PEREDA"
    },
    "DATA_02": {
        "buildingNumber": "20",
        "city": "BILBAO",
        "country": "ES",
        "postalCode": "48009",
        "street": "CALLE IPARRAGUIRRE"
    },
    "DATA_03": {
        "buildingNumber": "1",
        "city": "NORTHAMPTON",
        "country": "GB",
        "postalCode": "NN4 7SG",
        "street": "PAVILION DR BARCLAYCARD HOUSE"
    },
    "DATA_04": {
        "buildingNumber": "1",
        "city": "BIRMINGHAM",
        "country": "UK",
        "postalCode": "B1 1HQ",
        "street": "CENTENARY SQUARE"
    }
}

DATA_01 = create_data(
    "MIRYA TRADING CO LTD", "DE86500700100925993805", "EUR", debtor_address, 460000.00,
    "LEGALNET SYSTEMS SPAIN SL", "ES9400496103962716120773", "EUR", "BANCO SANTANDER",
    {"financialInstitutionId": "BSCHESMMXXX"},  # Ajuste aquí
    creditor_addresses["DATA_01"], "SCT", generate_end_to_end_identification(paymentId)
)

DATA_02 = create_data(
    "MIRYA TRADING CO LTD", "DE86500700100925993805", "EUR", debtor_address, 1000.00,
    "ZAIBATSUS.L.", "ES3901821250410201520178", "EUR", "BANCO BILBAO VIZCAYA ARGENTARIA, S.A.",
    {"financialInstitutionId": "BBVAESMMXXX"},  # Ajuste aquí
    creditor_addresses["DATA_02"], "SCT", generate_end_to_end_identification(paymentId)
)

DATA_03 = create_data(
    "MIRYA TRADING CO LTD", "DE86500700100925993805", "EUR", debtor_address, 1000.00,
    "REVSTAR GLOBAL INTERNATIONAL LTD", "GB69BUKB20041558708288", "EUR", "BARCLAYS BANK UK PLC",
    {"financialInstitutionId": "BUKBGB22XXX"},  # Ajuste aquí
    creditor_addresses["DATA_03"], "SCT", generate_end_to_end_identification(paymentId)
)

DATA_04 = create_data(
    "MIRYA TRADING CO LTD", "DE86500700100925993805", "EUR", debtor_address, 1000.00,
    "ECLIPS CORPORATION LTD", "GB43HBUK40127669998520", "EUR", "HSBC UK BANK PLC",
    {"financialInstitutionId": "HBUKGB4BXXX"},  # Ajuste aquí
    creditor_addresses["DATA_04"], "SCT", generate_end_to_end_identification(paymentId)
)

DATA_05 = {
    "debtor": {
        "debtorName": "MIRYA TRADING CO LTD",
        "debtorPostalAddress": {
            "country": "DE",
            "addressLine": {
                "streetAndHouseNumber": "TAUNUSANLAGE 1",
                "zipCodeAndCity": "60325 FRANKFURT"
            }
        }
    },
    "debtorAccount": {
        "iban": "DE86500700100925993805",
        "currency": "EUR"
    },
    "paymentIdentification": {
        "endToEndId": generate_end_to_end_identification(paymentId),
        "instructionId": f"INT{generate_end_to_end_identification(paymentId)}"
    },
    "instructedAmount": {
        "amount": float(1000.00),
        "currency": "EUR"
    },
    "creditorAgent": {
        "financialInstitutionId": "BBVAESMMXXX"
    },
    "creditor": {
        "creditorName": "ZAIBATSUS.L.",
        "creditorPostalAddress": {
            "country": "ES",
            "addressLine": {
                "streetAndHouseNumber": "CALLE IPARRAGUIRRE 20",
                "zipCodeAndCity": "48009 BILBAO"
            }
        }
    },
    "creditorAccount": {
        "iban": "ES3901821250410201520178",
        "currency": "EUR"
    },
    "remittanceInformationStructured": "JN2DKYS-LNS-K",
    "remittanceInformationUnstructured": "JN2DKYS-LNS-K",
    "purposeCode": "0178",
    "requestExecutionDate": datetime.now().strftime("%Y-%m-%d")
}

DATA = DATA_02

data = {
    "method": "pushTAN",
    "requestType": "SEPA_CREDIT_TRANSFERS",
    "requestData": {
        "targetIban": DATA["creditorAccount"]["iban"],
        "amountCurrency": DATA["instructedAmount"].get("currency", "EUR"),  # Valor predeterminado: "USD"
        "amountValue": DATA["instructedAmount"].get("amount", 0),  # Valor predeterminado: 0
        "targetSwiftBic": DATA["creditorAgent"]["financialInstitutionId"]
    }
}

api_url_SCT = f"https://api.dbapi.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfers"

api_url_ip = f"https://{URL_DB}/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers"

api_url_ISCT = f"https://api.dbapi.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers"

bank_url = "https://api.db.com/swift/transfer"

bank_api_url = f"https://{URL_DB}:{PORT_DB}/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfers"

transaction_authorization_url = "https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges"

bank_url_port = f"https://{URL_DB}:{PORT_DB}"

bank_url_port_s = f"https://{URL_DB}:{PORT_DB}/swift/transfer"

hydra_url_port = f"https://{URL_HY}:{PORT_HY}"


API_URL = hydra_url_port