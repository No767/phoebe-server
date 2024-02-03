#
# Account creation
#

POST http://localhost:5765/api/register
{
	"email": "diamond@libdb.so",
	"password": "very weak password",
	"bio": "",
	"color": "#f00",
	"nickname": "silver",
	"preferred_name": "Diamond",
	"genders": ["woman", "transgender woman"],
	"pronouns": ["she/her", "it/its"],
	"sexual_orientations": ["bisexual"]
}
HTTP 200
[Asserts]
jsonpath "$.token" exists
jsonpath "$.user_id" exists
[Captures]
user_id: jsonpath "$.user_id"

POST http://localhost:5765/api/login
{
	"email": "diamond@libdb.so",
	"password": "very weak password"
}
HTTP 200
[Asserts]
jsonpath "$.token" exists
jsonpath "$.user_id" == {{user_id}}
[Captures]
token: jsonpath "$.token"

#
# Asset handling
#

POST http://localhost:5765/api/assets
Authorization: Bearer {{token}}
[MultipartFormData]
file: file,giga.hurl; text/plain
alt: The current test file
HTTP 200
[Asserts]
jsonpath "$.hash" exists
jsonpath "$.alt" == "The current test file"
[Captures]
asset_hash: jsonpath "$.hash"

GET http://localhost:5765/api/assets/{{asset_hash}}
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
header "Content-Type" == "text/plain; charset=utf-8"
bytes count > 10

GET http://localhost:5765/api/assets/{{asset_hash}}/metadata
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.alt" == "The current test file"
jsonpath "$.content_type" == "text/plain"

#
# Current User testing
#

GET http://localhost:5765/api/users/me
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.id" == {{user_id}}
jsonpath "$.email" == "diamond@libdb.so"
jsonpath "$.nickname" == "silver"
jsonpath "$.bio" == ""

PATCH http://localhost:5765/api/users/me
Authorization: Bearer {{token}}
{
	"email": "diamond@libdb.so",
	"password": "very weak password",
	"bio": "I'm a diamond, but I'm also gold.",
	"color": "#f00",
	"nickname": "gold",
	"preferred_name": "Diamond",
	"genders": ["woman", "transgender woman"],
	"pronouns": ["she/her", "it/its"],
	"sexual_orientations": ["bisexual"]
}
HTTP 200
[Asserts]
jsonpath "$.id" == {{user_id}}
jsonpath "$.email" == "diamond@libdb.so"
jsonpath "$.nickname" == "gold"
jsonpath "$.bio" == "I'm a diamond, but I'm also gold."
