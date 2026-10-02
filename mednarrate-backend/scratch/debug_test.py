import re
with open("tests/test_help_center.py", "r") as f:
    c = f.read()

c = c.replace(
    "ticket = SupportTicket(",
    "print('TYPE OF CUSTOMER ID:', type(customer.id), repr(customer.id))\nticket = SupportTicket("
)
with open("tests/test_help_center.py", "w") as f:
    f.write(c)
