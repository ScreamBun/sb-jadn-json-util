ORIG_REF = "orig_ref"
UPDATED_REF = "updated_ref"
PATH_TO_VAL = "path_to_val"
ACTUAL_VAL = "actual_val"

CONTENT_ENCODING = "contentEncoding"
BASE_64_URL = "base64url"
BASE_64 = "base-64"
BASE64 = "base64"
BASE_32 = "base-32"
BASE32 = "base32"
BASE_16 = "base-16"
BASE16 = "base16"


POUND = "#"
POUND_SLASH = "#/"
POUND_SLASH_DEFINITIONS = "#/definitions"
DEFINITIONS = "definitions"
PROPERTIES = "properties"                
SLASH_DOL_REF = "/$ref"
DOL_REF = "$ref"

# Regex Patterns
DATETIME_TIMEZONE_ORIG = "^(((2000|2400|2800|(19|2[0-9](0[48]|[2468][048]|[13579][26])))-02-29)|(((19|2[0-9])[0-9]{2})-02-(0[1-9]|1[0-9]|2[0-8]))|(((19|2[0-9])[0-9]{2})-(0[13578]|10|12)-(0[1-9]|[12][0-9]|3[01]))|(((19|2[0-9])[0-9]{2})-(0[469]|11)-(0[1-9]|[12][0-9]|30)))T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\\.[0-9]+)?(Z|(-((0[0-9]|1[0-2]):00|0[39]:30)|\\+((0[0-9]|1[0-4]):00|(0[34569]|10):30|(0[58]|12):45)))$"
DATETIME_TIMEZONE_REVISED = "/(\\d{4})-?(\\d{2})-?(\\d{2})[T\\s]?(\\d{2}):?(\\d{2})(?::?(\\d{2})(\\.\\d+)?)?(Z|(?:([+-]\\d{2})(?::?(\\d{2}))?))?/i"

# File Paths
TESTS_PATH = "/tests/data/"