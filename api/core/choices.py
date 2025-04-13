"""
Choice constants for model fields across the application.

This module defines standardized choice tuples for use in model fields,
ensuring consistency in dropdown menus, form fields, and database values.
"""
from django.utils.translation import gettext_lazy as _


# Transfer types and strategies
TRANSFER_TYPES = [
    ('standard', _('Standard')),
    ('instant', _('Instant')),
]

TYPE_STRATEGIES = [
    ('standard_only', _('Standard Only')),
    ('instant_only', _('Instant Only')),
    ('instant_if_available', _('Instant If Available')),
]

# Account types
TYPE = [
    ('main', _('Main')),
    ('virtual', _('Virtual')),
]

# Transaction status codes
STATUS_CHOICES = [
    ('RJCT', _('Rejected')),
    ('RCVD', _('Received')),
    ('ACCP', _('Accepted')),
    ('ACTP', _('Accepted Technical Validation')),
    ('ACSP', _('Accepted Settlement in Process')),
    ('ACWC', _('Accepted with Change')),
    ('ACWP', _('Accepted with Pending')),
    ('ACCC', _('Accepted Credit Check')),
    ('CANC', _('Cancelled')),
    ('PDNG', _('Pending')),
]

# Transaction direction
DIRECTION_CHOICES = [
    ('debit', _('Debit')),
    ('credit', _('Credit')),
]

# Sandbox transaction status
SANDBOX_STATUS_CHOICES = [
    ('PENDING', _('Pending')),
    ('COMPLETED', _('Completed')),
]

# SEPA direct debit schemes
SCHEME_CHOICES = [
    ('b2b', _('B2B')),
    ('core', _('CORE')),
]

# Collection status
COLLECTION_STATUS_CHOICES = [
    ('pending', _('Pending')),
    ('scheduled', _('Scheduled')),
    ('confirmed', _('Confirmed')),
    ('canceled', _('Canceled')),
    ('failed', _('Failed')),
]

# Account types
ACCOUNT_TYPES = [
    ('current_account', _('Current Account')),
    ('ring_fenced_account', _('Ring-Fenced Account')),
    ('settlement_account', _('Settlement Account')),
    ('specially_dedicated_account', _('Specially Dedicated Account')),
    ('trust_account', _('Trust Account')),
    ('meal_voucher_account', _('Meal Voucher Account')),
    ('booster_account', _('Booster Account')),
]

# Account status
ACCOUNT_STATUS = [
    ('active', _('Active')),
    ('closed', _('Closed')),
]

# Predefined company names
NAME = [
    ('MIRYA TRADING CO LIMITED', _('MIRYA TRADING CO LIMITED')),
    ('ZAIBATSUS.L.', _('ZAIBATSUS.L.')),
    ('REVSTAR GLOBAL INTERNATIONAL LTD', _('REVSTAR GLOBAL INTERNATIONAL LTD')),
    ('ECLIPS CORPORATION LTD.', _('ECLIPS CORPORATION LTD.')),
]

# Predefined IBAN values
IBAN = [
    ('DE86500700100925993805', 'DE86500700100925993805'),
    ('ES3901821250410201520178', 'ES3901821250410201520178'),
    ('GB69BUKB20041558708288', 'GB69BUKB20041558708288'),
    ('GB43HBUK40127669998520', 'GB43HBUK40127669998520'),
]

# Predefined BIC values
BIC = [
    ('DEUTDEFFXXX', 'DEUTDEFFXXX'),
    ('BBVAESMMXXX', 'BBVAESMMXXX'),
    ('BUKBGB22XXX', 'BUKBGB22XXX'),
    ('HBUKGB4BXXX', 'HBUKGB4BXXX'),
]

# Predefined bank names
BANK = [
    ('DEUTSCHE BANK AG', _('DEUTSCHE BANK AG')),
    ('BANCO BILBAO VIZCAYA ARGENTARIA, S.A.', _('BANCO BILBAO VIZCAYA ARGENTARIA, S.A.')),
    ('BARCLAYS BANK UK PLC', _('BARCLAYS BANK UK PLC')),
    ('HSBC UK BANK PLC', _('HSBC UK BANK PLC')),
]

# Payment purpose codes (ISO 20022)
PURPOSE_CODES = [
    ('ACCT', _('Account Management')),
    ('CASH', _('Cash Management Transfer')),
    ('COLL', _('Collection Payment')),
    ('INTC', _('Intra-Company Payment')),
    ('TREA', _('Treasury Payment')),
    ('BONU', _('Bonus Payment')),
    ('COMM', _('Commission')),
    ('SALA', _('Salary Payment')),
    ('PENS', _('Pension Payment')),
    ('TAXS', _('Tax Payment')),
    ('VATX', _('VAT Payment')),
    ('SUPP', _('Supplier Payment')),
    ('INVP', _('Invoice Payment')),
    ('TRAD', _('Trade Services')),
    ('CDPT', _('Cash Deposit')),
    ('LOAN', _('Loan')),
    ('DEPT', _('Deposit')),
    ('CHAR', _('Charity Payment')),
]

# Currency codes
CURRENCY_CODES = [
    ('EUR', _('Euro')),
    ('USD', _('US Dollar')),
    ('GBP', _('British Pound')),
    ('CHF', _('Swiss Franc')),
    ('JPY', _('Japanese Yen')),
    ('CAD', _('Canadian Dollar')),
    ('AUD', _('Australian Dollar')),
    ('SEK', _('Swedish Krona')),
    ('NOK', _('Norwegian Krone')),
    ('DKK', _('Danish Krone')),
    ('PLN', _('Polish Zloty')),
    ('CZK', _('Czech Koruna')),
    ('HUF', _('Hungarian Forint')),
    ('RON', _('Romanian Leu')),
    ('BGN', _('Bulgarian Lev')),
    ('HRK', _('Croatian Kuna')),
    ('ISK', _('Icelandic Krona')),
]

# Transaction types
TRANSACTION_TYPES = [
    ('transfer', _('Transfer')),
    ('deposit', _('Deposit')),
    ('withdrawal', _('Withdrawal')),
    ('payment', _('Payment')),
    ('collection', _('Collection')),
    ('fee', _('Fee')),
    ('interest', _('Interest')),
    ('refund', _('Refund')),
    ('adjustment', _('Adjustment')),
]

# Payment methods
PAYMENT_METHODS = [
    ('sepa_credit_transfer', _('SEPA Credit Transfer')),
    ('sepa_direct_debit', _('SEPA Direct Debit')),
    ('card_payment', _('Card Payment')),
    ('fast_payment', _('Fast Payment')),
    ('international_transfer', _('International Transfer')),
    ('internal_transfer', _('Internal Transfer')),
]

# Country codes
COUNTRY_CODES = [
    ('AT', _('Austria')),
    ('BE', _('Belgium')),
    ('BG', _('Bulgaria')),
    ('HR', _('Croatia')),
    ('CY', _('Cyprus')),
    ('CZ', _('Czech Republic')),
    ('DK', _('Denmark')),
    ('EE', _('Estonia')),
    ('FI', _('Finland')),
    ('FR', _('France')),
    ('DE', _('Germany')),
    ('GR', _('Greece')),
    ('HU', _('Hungary')),
    ('IE', _('Ireland')),
    ('IT', _('Italy')),
    ('LV', _('Latvia')),
    ('LT', _('Lithuania')),
    ('LU', _('Luxembourg')),
    ('MT', _('Malta')),
    ('NL', _('Netherlands')),
    ('PL', _('Poland')),
    ('PT', _('Portugal')),
    ('RO', _('Romania')),
    ('SK', _('Slovakia')),
    ('SI', _('Slovenia')),
    ('ES', _('Spain')),
    ('SE', _('Sweden')),
    ('GB', _('United Kingdom')),
]