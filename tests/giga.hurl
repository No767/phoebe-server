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
file: file,amogus.png;
alt: Red among us
HTTP 200
[Asserts]
jsonpath "$.hash" exists
jsonpath "$.alt" == "Red among us"
[Captures]
asset_hash: jsonpath "$.hash"

GET http://localhost:5765/api/assets/{{asset_hash}}
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
header "Content-Type" == "image/png"
bytes count > 10

GET http://localhost:5765/api/assets/{{asset_hash}}/metadata
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.alt" == "Red among us"
jsonpath "$.content_type" == "image/png"

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
jsonpath "$.group_id" == null

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
	"sexual_orientations": ["bisexual"],
	"avatar_hash": "{{asset_hash}}"
}
HTTP 200
[Asserts]
jsonpath "$.id" == {{user_id}}
jsonpath "$.avatar_hash" == "{{asset_hash}}"

#
# Groups testing
#

POST http://localhost:5765/api/groups
Authorization: Bearer {{token}}
{
	"name": "gay house",
	"bio": "A house for gay people",
	"color": "#f00"
}
HTTP 200
[Asserts]
jsonpath "$.id" exists
jsonpath "$.people" count == 1
jsonpath "$.people[0].id" == {{user_id}}
[Captures]
group_id: jsonpath "$.id"

GET http://localhost:5765/api/groups/{{group_id}}
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.id" == {{group_id}}
jsonpath "$.name" == "gay house"
jsonpath "$.bio" == "A house for gay people"
jsonpath "$.color" == "#f00"
jsonpath "$.people" count == 1

GET http://localhost:5765/api/users/me
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.group_id" == {{group_id}}

PATCH http://localhost:5765/api/groups/{{group_id}}
Authorization: Bearer {{token}}
{
	"name": "gayer house",
	"bio": "A house for gayer people",
	"color": "#00f"
}
HTTP 200
[Asserts]
jsonpath "$.id" == {{group_id}}
jsonpath "$.name" == "gayer house"
jsonpath "$.bio" == "A house for gayer people"
jsonpath "$.color" == "#00f"
