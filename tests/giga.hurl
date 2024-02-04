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

POST http://localhost:5765/api/register
{
	"email": "gold@libdb.so",
	"password": "very weak password",
	"bio": "",
	"color": "#f00",
	"nickname": "gold",
	"preferred_name": "Gold",
	"genders": ["woman", "transgender woman"],
	"pronouns": ["she/her", "it/its"],
	"sexual_orientations": ["bisexual"]
}
HTTP 200
[Captures]
another_user_id: jsonpath "$.user_id"
another_token: jsonpath "$.token"

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
jsonpath "$.group" == null

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
	"color": "#f00",
	"lat": -5.122,
	"lon": 2.193,
	"has_house": true
}
HTTP 200
[Asserts]
jsonpath "$.id" exists
jsonpath "$.people" count == 1
jsonpath "$.people[0].id" == {{user_id}}
[Captures]
group_id: jsonpath "$.id"


POST http://localhost:5765/api/groups
Authorization: Bearer {{another_token}}
{
	"name": "straight house",
	"bio": "A house for straight people",
	"color": "#0f0",
	"lat": -4.122,
	"lon": 1.193,
	"has_house": true
}
HTTP 200
[Asserts]
jsonpath "$.id" exists
jsonpath "$.people" count == 1
jsonpath "$.people[0].id" == {{another_user_id}}
[Captures]
another_group_id: jsonpath "$.id"

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
jsonpath "$.group.id" == {{group_id}}
jsonpath "$.group.name" == "gay house"



PATCH http://localhost:5765/api/groups/{{group_id}}
Authorization: Bearer {{token}}
{
	"name": "gayer house",
	"bio": "A house for gayer people",
	"color": "#00f",
	"lat": -5.122,
	"lon": 2.193,
	"has_house": true
}
HTTP 200
[Asserts]
jsonpath "$.id" == {{group_id}}
jsonpath "$.name" == "gayer house"
jsonpath "$.bio" == "A house for gayer people"
jsonpath "$.color" == "#00f"

#
# Interested-in-groups testing
#

POST http://localhost:5765/api/groups/{{another_group_id}}/interested
Authorization: Bearer {{token}}
HTTP 200

POST http://localhost:5765/api/groups/{{another_group_id}}/interested
Authorization: Bearer {{token}}
HTTP 400
[Asserts]
jsonpath "$.detail" == "The interested group already is interested"

GET http://localhost:5765/api/groups/{{another_group_id}}
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.access_level" == 1
jsonpath "$.interested" == true

#
# Searching
#

GET http://localhost:5765/api/search
Authorization: Bearer {{token}}
[QueryStringParams]
lat: -4.122
lon: 1.193
radius: 100
unit: mi
HTTP 200
[Asserts]
jsonpath "$" count == 2
jsonpath "$[0].distance" == 0
jsonpath "$[1].distance" > 97 

# 
# Accepting user group requests
# 

POST http://localhost:5765/api/users/{{user_id}}/accept
Authorization: Bearer {{another_token}}
HTTP 200

POST http://localhost:5765/api/users/{{user_id}}/accept
Authorization: Bearer {{another_token}}
HTTP 400

POST http://localhost:5765/api/users/{{another_user_id}}/accept
Authorization: Bearer {{token}}
HTTP 404
[Asserts]
jsonpath "$.detail" == "Cannot find group to accept"

#
# Chatting
#

GET http://localhost:5765/api/chat/groups
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$" count == 1
jsonpath "$[0].id" == {{another_group_id}}

GET http://localhost:5765/api/chat/groups/{{another_group_id}}/messages
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$" count == 0

POST http://localhost:5765/api/chat/groups/{{another_group_id}}/messages
Authorization: Bearer {{token}}
{
	"content": {
		"type": "text",
		"markdown": "Hello, I'm Diamond!"
	}
}
HTTP 200
[Asserts]
jsonpath "$.id" exists
jsonpath "$.content.type" == "text"
jsonpath "$.content.markdown" == "Hello, I'm Diamond!"
jsonpath "$.author.id" == {{user_id}}
jsonpath "$.author_id" == {{user_id}}
