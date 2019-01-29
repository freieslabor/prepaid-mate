todo
====

ui
--
* login: initial focus on username field
* login: enable submit via enter key
* dashboard: fix balance (/100)
* dashboard: add link for json export
* charge money
* account modification
* account creation (with disclaimer)

backend
-------
* check transaction safety
* make sure saldo does not get negative
* /api/payment/perform should return user's balance
* do not accept known order barcode as user barcode
* improve SQL queries
* extensive logging
* tests

barcode-scanner-client
----------------------
* timeout after user identification
* confirmation sounds
* current balance text2speech
* extensive logging
* tests
