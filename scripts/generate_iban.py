def calculate_iban_check_digits(country_code, bank_code, account_number):
    bban = bank_code + account_number
    rearranged_iban = bban + country_code + '00'
    numeric_iban = ''.join(str(int(ch, 36)) for ch in rearranged_iban)
    check_digits = 98 - (int(numeric_iban) % 97)
    return f'{check_digits:02}'

country_code = 'US'
bank_code = 'PORG'
account_number = '741000942110'
check_digits = calculate_iban_check_digits(country_code, bank_code, account_number)
iban = f'{country_code}{check_digits} {bank_code} {account_number[:4]} {account_number[4:8]} {account_number[8:]}'
print(iban)