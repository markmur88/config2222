CREATE TABLE IF NOT EXISTS payments_errorresponse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INTEGER,
    message TEXT
);

CREATE TABLE IF NOT EXISTS payments_message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INTEGER,
    message TEXT
);

CREATE TABLE IF NOT EXISTS payments_transactionstatus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_status TEXT
);

CREATE TABLE IF NOT EXISTS payments_statusresponse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    code TEXT,
    text TEXT
);

-- Insertar datos de ejemplo para payments_errorresponse
INSERT INTO payments_errorresponse (code, message) VALUES (114, 'Unable to identify transaction by Id.');
INSERT INTO payments_errorresponse (code, message) VALUES (115, 'Time limit exceeded.');
INSERT INTO payments_errorresponse (code, message) VALUES (121, 'OTP invalid challenge response: %s.');
INSERT INTO payments_errorresponse (code, message) VALUES (122, 'Invalid OTP.');
INSERT INTO payments_errorresponse (code, message) VALUES (127, 'Booking date from must precede booking date to.');
INSERT INTO payments_errorresponse (code, message) VALUES (131, 'Invalid value for "sortBy". Valid values are "bookingDate[ASC]" and "bookingDate[DESC]".');
INSERT INTO payments_errorresponse (code, message) VALUES (132, 'not supported');
INSERT INTO payments_errorresponse (code, message) VALUES (138, 'it seems that you started a non pushTAN challenge. Please use the PATCH endpoint to continue');
INSERT INTO payments_errorresponse (code, message) VALUES (139, 'it seems that you started a pushTAN challenge. Please use the GET endpoint to continue');

-- Insertar datos de ejemplo para payments_message
INSERT INTO payments_message (code, message) VALUES (1, 'Message example');

-- Insertar datos de ejemplo para payments_transactionstatus
INSERT INTO payments_transactionstatus (transaction_status) VALUES ('ACCP');

-- Insertar datos de ejemplo para payments_statusresponse
INSERT INTO payments_statusresponse (category, code, text) VALUES ('Success', '200', 'successful operation');
INSERT INTO payments_statusresponse (category, code, text) VALUES ('Error', '400', 'Invalid value for %s.');
INSERT INTO payments_statusresponse (category, code, text) VALUES ('Error', '401', 'The requested function requires a SCA Level Authentication.');
