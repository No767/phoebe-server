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

POST http://localhost:5765/api/login
{
	"email": "diamond@libdb.so",
	"password": "very weak password"
}
HTTP 200
[Asserts]
jsonpath "$.token" exists
jsonpath "$.user_id" exists
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
