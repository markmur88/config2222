TRANSFER_TYPES = [
    ('standard', 'Standard'),
    ('instant', 'Instant'),
]

TYPE_STRATEGIES = [
    ('standard_only', 'Standard Only'),
    ('instant_only', 'Instant Only'),
    ('instant_if_available', 'Instant If Available'),
]

TYPE = [
    ('main', 'main'),
    ('virtual', 'virtual'),
]

STATUS_CHOICES = [
    ('RJCT', 'RJCT'),
    ('RCVD', 'RCVD'),
    ('ACCP', 'ACCP'),
    ('ACTP', 'ACTP'),
    ('ACSP', 'ACSP'),
    ('ACWC', 'ACWC'),
    ('ACWP', 'ACWP'),
    ('ACCC', 'ACCC'),
    ('CANC', 'CANC'),
    ('PDNG', 'PDNG'),
]

DIRECTION_CHOICES = [
    ('debit', 'Debit'),
    ('credit', 'Credit'),
]

SANDBOX_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("COMPLETED", "Completed"),
]

SCHEME_CHOICES = [
    ('b2b', 'B2B'),
    ('core', 'CORE'),
]

COLLECTION_STATUS_CHOICES = [
    ('pending', 'Pendiente'),
    ('scheduled', 'Programada'),
    ('confirmed', 'Confirmada'),
    ('canceled', 'Cancelada'),
    ('failed', 'Fallida'),
]

ACCOUNT_TYPES = [
    ('current_account', 'Current Account'),
    ('ring_fenced_account', 'Ring-Fenced Account'),
    ('settlement_account', 'Settlement Account'),
    ('specially_dedicated_account', 'Specially Dedicated Account'),
    ('trust_account', 'Trust Account'),
    ('meal_voucher_account', 'Meal Voucher Account'),
    ('booster_account', 'Booster Account'),
]

ACCOUNT_STATUS = [
    ('active', 'Active'),
    ('closed', 'Closed'),
]

NAME = [
    ('MIRYA TRADING CO LIMITED', 'MIRYA TRADING CO LIMITED'),
    ('ZAIBATSUS.L.', 'ZAIBATSUS.L.'),
    ('REVSTAR GLOBAL INTERNATIONAL LTD', 'REVSTAR GLOBAL INTERNATIONAL LTD'),
    ('ECLIPS CORPORATION LTD.', 'ECLIPS CORPORATION LTD.'),
]

IBAN = [
    ('DE86500700100925993805', 'DE86500700100925993805'),
    ('ES3901821250410201520178', 'ES3901821250410201520178'),
    ('GB69BUKB20041558708288', 'GB69BUKB20041558708288'),
    ('GB43HBUK40127669998520', 'GB43HBUK40127669998520'),
]

BIC = [
    ('DEUTDEFFXXX', 'DEUTDEFFXXX'),
    ('BBVAESMMXXX', 'BBVAESMMXXX'),
    ('BUKBGB22XXX', 'BUKBGB22XXX'),
    ('HBUKGB4BXXX', 'HBUKGB4BXXX'),
]

BANK = [
    ('DEUTSCHE BANK AG', 'DEUTSCHE BANK AG'),
    ('BANCO BILBAO VIZCAYA ARGENTARIA, S.A.', 'BANCO BILBAO VIZCAYA ARGENTARIA, S.A.'),
    ('BARCLAYS BANK UK PLC', 'BARCLAYS BANK UK PLC'),
    ('HSBC UK BANK PLC', 'HSBC UK BANK PLC'),
]

