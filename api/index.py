import json
import random
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Global Configuration
TITLE_ID = "13449"
SECRET_KEY = "NHYJF5FP7SHQKQ1AU55UYPHQQHAZB4WBTJXCOFAJE4KQYSYETU"
API_KEY = "OC|1184115174791506|72ce9e5acc12fe80f2f492c249eec507"

def get_auth_headers():
    return {"Content-Type": "application/json", "X-SecretKey": SECRET_KEY}


@app.route("/", methods=["GET"])
def main():
    image_url = "https://imgs.search.brave.com/50ma5iuDOgB3FXoOqkmidyp8U88p3Y1MA-PnQBpyqio/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9iaWdz/dGFyYmlvLmNvbS93/cC1jb250ZW50L3Vw/bG9hZHMvMjAyMi8w/MS9Kb2UtQmFydG9s/b3p6aS5qcGc"
    return f"""
    <html>
      <head>
        <title>Backend Status</title>
        <style>
          body {{
            background-color: #111;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
          }}
          img {{
            max-width: 90vw;
            max-height: 90vh;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(255,255,255,0.2);
          }}
        </style>
      </head>
      <body>
        <img src="{image_url}" alt="Clean Image" />
      </body>
    </html>
    """

@app.route('/api/TD', methods=['POST'])
def titled_data():
    return jsonify({"MOTD": "Welcome to the server! Join the discord for updates and guidelines."})

@app.route("/api/PlayFabAuthentication", methods=["POST"])
def playfab_authentication():
    data = request.get_json() or {}
    oculus_id = data.get("OculusId", "Null")
    nonce = data.get("Nonce", "Null")
    platform = data.get("Platform", "Null")

    login_req = requests.post(
        url=f"https://{TITLE_ID}.playfabapi.com/Server/LoginWithServerCustomId",
        json={
            "ServerCustomId": f"OCULUS{oculus_id}",
            "CreateAccount": True
        },
        headers=get_auth_headers()
    )

    if login_req.status_code == 200:
        rjson = login_req.json().get('data', {})
        session_ticket = rjson.get('SessionTicket')
        playfab_id = rjson.get('PlayFabId')
        entity = rjson.get('EntityToken', {})
        entity_token = entity.get('EntityToken')
        entity_id = entity.get('Entity', {}).get('Id')
        entity_type = entity.get('Entity', {}).get('Type')

        # FIXED: Changed "CustomID" to "CustomId" to match PlayFab API specification
        requests.post(
            url=f"https://{TITLE_ID}.playfabapi.com/Client/LinkCustomID",
            json={"CustomId": f"OCULUS{oculus_id}", "ForceLink": True}, 
            headers={
                "content-type": "application/json",
                "x-authorization": session_ticket
            }
        )

        return jsonify({
            "PlayFabId": playfab_id,
            "SessionTicket": session_ticket,
            "EntityToken": entity_token,
            "EntityId": entity_id,
            "EntityType": entity_type,
            "Nonce": nonce,
            "OculusId": oculus_id,
            "Platform": platform
        }), 200
    else:
        ban_info = login_req.json()
        if ban_info.get("errorCode") == 1002:
            details = ban_info.get("errorDetails", {})
            ban_reason = next(iter(details.keys()), "Banned")
            ban_time = details.get(ban_reason, ["Indefinite"])[0]
            return jsonify({
                "BanMessage": ban_reason,
                "BanExpirationTime": ban_time,
            }), 403
        return jsonify({"Message": "Login failed"}), 403

@app.route("/api/CheckForBadName", methods=["POST"])
def check_for_bad_name():
    req_data = request.get_json() or {}
    
    # Fallback cascade to safely grab the name from internal custom script payloads
    rjson = req_data.get("FunctionResult") or req_data.get("FunctionArgument") or req_data
    name_val = rjson.get("name", "GORILLA")
    name = str(name_val).upper()

    bad_names = [
        "KKK", "PENIS", "NIGG", "NEG", "NIGA", "MONKEYSLAVE", "SLAVE", "FAG",
        "NAGGI", "TRANNY", "QUEER", "KYS", "DICK", "PUSSY", "VAGINA", "BIGBLACKCOCK",
        "DILDO", "HITLER", "KKX", "XKK", "NIGE", "NI6", "PORN",
        "JEW", "JAXX", "TTTPIG", "SEX", "COCK", "CUM", "FUCK",
        "ELLIOT", "JMAN", "K9", "NIGGA", "NICKER", "NICKA",
        "REEL", "NII", "@here", "!", " ", "PPPTIG", "CLEANINGBOT", "JANITOR",
        "H4PKY", "MOSA", "NIGGER", "IHATENIGGERS", "@everyone", "TTT"
    ]

    if name in bad_names:
        return jsonify({"result": 2})
    return jsonify({"result": 0})

@app.route("/api/CachePlayFabId", methods=["POST"])
def cache_playfab_id():
    data = request.get_json() or {}
    session_ticket = data.get("SessionTicket")
    if session_ticket:
        playfab_id = session_ticket.split("-")[0]
        return jsonify({"Message": "Authed", "PlayFabId": playfab_id}), 200
    return jsonify({"Message": "Try Again Later."}), 404

@app.route("/api/ConsumeOculusIAP", methods=["POST"])
def consume_oculus_iap():
    data = request.get_json() or {}
    user_id = data.get("userID")
    nonce = data.get("nonce")
    sku = data.get("sku")

    response = requests.post(
        url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={user_id}&sku={sku}&access_token={API_KEY}",
        headers={"content-type": "application/json"}
    )

    if response.json().get("success"):
        return jsonify({"result": True})
    return jsonify({"error": True})

@app.route("/api/photon", methods=["POST"])
def photonauth():
        print(f"Received {request.method} request at /api/photon")
        getjson = request.get_json()
        Ticket = getjson.get("Ticket")
        Nonce = getjson.get("Nonce")
        Platform = getjson.get("Platform")
        UserId = getjson.get("UserId")
        nickName = getjson.get("username")
        if request.method.upper() == "GET":
            rjson = request.get_json()
            print(f"{request.method} : {rjson}")

            userId = Ticket.split('-')[0] if Ticket else None
            print(f"Extracted userId: {UserId}")

            if userId is None or len(userId) != 16:
                print("Invalid userId")
                return jsonify({
                    'resultCode': 2,
                    'message': 'Invalid token',
                    'userId': None,
                    'nickname': None
                })

            if Platform != 'Quest':
                return jsonify({'Error': 'Bad request', 'Message': 'Invalid platform!'}),403

            if Nonce is None:
                return jsonify({'Error': 'Bad request', 'Message': 'Not Authenticated!'}),304

            req = requests.post(
                url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
                json={"PlayFabId": userId},
                headers={
                    "content-type": "application/json",
                    "X-SecretKey": settings.SecretKey
                })

            print(f"Request to PlayFab returned status code: {req.status_code}")

            if req.status_code == 200:
                nickName = req.json().get("UserInfo",
                                          {}).get("UserAccountInfo",
                                                  {}).get("Username")
                if not nickName:
                    nickName = None

                print(
                    f"Authenticated user {userId.lower()} with nickname: {nickName}"
                )

                return jsonify({
                    'resultCode': 1,
                    'message':
                    f'Authenticated user {userId.lower()} title {settings.TitleId.lower()}',
                    'userId': f'{userId.upper()}',
                    'nickname': nickName
                })
            else:
                print("Failed to get user account info from PlayFab")
                return jsonify({
                    'resultCode': 0,
                    'message': "Something went wrong",
                    'userId': None,
                    'nickname': None
                })

        elif request.method.upper() == "POST":
            rjson = request.get_json()
            print(f"{request.method} : {rjson}")

            ticket = rjson.get("Ticket")
            userId = ticket.split('-')[0] if ticket else None
            print(f"Extracted userId: {userId}")

            if userId is None or len(userId) != 16:
                print("Invalid userId")
                return jsonify({
                    'resultCode': 2,
                    'message': 'Invalid token',
                    'userId': None,
                    'nickname': None
                })

            req = requests.post(
                 url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
                 json={"PlayFabId": userId},
                 headers={
                     "content-type": "application/json",
                     "X-SecretKey": settings.SecretKey
                 })

            print(f"Authenticated user {userId.lower()}")
            print(f"Request to PlayFab returned status code: {req.status_code}")

            if req.status_code == 200:
                 nickName = req.json().get("UserInfo",
                                           {}).get("UserAccountInfo",
                                                   {}).get("Username")
                 if not nickName:
                     nickName = None
                 return jsonify({
                     'resultCode': 1,
                     'message':
                     f'Authenticated user {userId.lower()} title {settings.TitleId.lower()}',
                     'userId': f'{userId.upper()}',
                     'nickname': nickName
                 })
            else:
                 print("Failed to get user account info from PlayFab")
                 successJson = {
                     'resultCode': 0,
                     'message': "Something went wrong",
                     'userId': None,
                     'nickname': None
                 }
                 authPostData = {}
                 for key, value in authPostData.items():
                     successJson[key] = value
                 print(f"Returning successJson: {successJson}")
                 return jsonify(successJson)
        else:
             print(f"Invalid method: {request.method.upper()}")
             return jsonify({
                 "Message":
                 "Use a POST or GET Method instead of " + request.method.upper()
             })


def ReturnFunctionJson(data, funcname, funcparam={}):
        print(f"Calling function: {funcname} with parameters: {funcparam}")
        rjson = data.get("FunctionParameter", {})
        userId = rjson.get("CallerEntityProfile",
                           {}).get("Lineage", {}).get("TitlePlayerAccountId")

        print(f"UserId: {userId}")

        req = requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Server/ExecuteCloudScript",
            json={
                "PlayFabId": userId,
                "FunctionName": funcname,
                "FunctionParameter": funcparam
            },
            headers={
                "content-type": "application/json",
                "X-SecretKey": settings.SecretKey
            })

        if req.status_code == 200:
            result = req.json().get("data", {}).get("FunctionResult", {})
            print(f"Function result: {result}")
            return jsonify(result), req.status_code
        else:
            print(f"Function execution failed, status code: {req.status_code}")
            return jsonify({}), req.status_code

# FIXED: App runner block placed at the complete bottom of the application lifecycle
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
