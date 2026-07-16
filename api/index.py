import requests
import random
from flask import Flask, jsonify, request
import json
import os


class GameInfo:
    def __init__(self):
        self.TitleId: str = "13449"
        self.SecretKey: str = "NHYJF5FP7SHQKQ1AU55UYPHQQHAZB4WBTJXCOFAJE4KQYSYETU"
        self.DiscordWebhook: str = "https://discord.com/api/webhooks/1526399263406428172/Yr9y364d-Wy8_Ola_nsSvVF9aPba0qg-hEfDN9D1rSaMqO_hBMcL5uWO6QpUVMQ6icmCv"
        self.ChangeGorilla: str = "vitinistufoboy"

        self.ApiKey: str = "OC|1184115174791506|72ce9e5acc12fe80f2f492c249eec507"
        self.ApiKey2: str = "OC|1184115174791506|72ce9e5acc12fe80f2f492c249eec507"
        self.ApiKey3: str = "OC|1184115174791506|72ce9e5acc12fe80f2f492c249eec507"

    def get_auth_headers(self):
        return {"content-type": "application/json", "X-SecretKey": self.SecretKey}


settings = GameInfo()
app = Flask(__name__)


def return_function_json(data, funcname, funcparam={}):
    user_id = data["FunctionParameter"]["CallerEntityProfile"]["Lineage"]["TitlePlayerAccountId"]

    response = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/ExecuteCloudScript",
        json={
            "PlayFabId": user_id,
            "FunctionName": funcname,
            "FunctionParameter": funcparam,
        },
        headers=settings.get_auth_headers(),
    )

    if response.status_code == 200:
        return (
            jsonify(response.json().get("data").get("FunctionResult")),
            response.status_code,
        )
    else:
        return jsonify({}), response.status_code


@app.route('/api/getrandname', methods=["POST"])
def GetRandomName():
    defaultname = f"ChangeGorilla" + str(random.randint(1000, 9999))
    return jsonify({"result": defaultname})


@app.route("/", methods=["POST", "GET"])
def main():
    return "Servers are running 😊"


@app.route("/api/PlayFabAuthentication", methods=["POST"])
def playfab_authentication():
    rjson = request.get_json()
    required_fields = ["CustomId", "Nonce", "AppId", "Platform", "OculusId"]
    missing_fields = [field for field in required_fields if not rjson.get(field)]

    if missing_fields:
        return jsonify({"Message": f"Missing parameter(s): {', '.join(missing_fields)}",
                        "Error": f"BadRequest-No{missing_fields[0]}"}), 400

    if rjson.get("AppId") != settings.TitleId:
        return jsonify({"Message": "Request sent for the wrong App ID", "Error": "BadRequest-AppIdMismatch"}), 400

    if not rjson.get("CustomId").startswith(("OC", "PI")):
        return jsonify({"Message": "Bad request", "Error": "BadRequest-IncorrectPrefix"}), 400

    discord_message(rjson)

    url = f"https://{settings.TitleId}.playfabapi.com/Server/LoginWithServerCustomId"
    login_request = requests.post(
        url=url,
        json={"ServerCustomId": rjson.get("CustomId"), "CreateAccount": True},
        headers=settings.get_auth_headers()
    )

    if login_request.status_code == 200:
        data = login_request.json().get("data")
        session_ticket = data.get("SessionTicket")
        entity_token = data.get("EntityToken").get("EntityToken")
        playfab_id = data.get("PlayFabId")
        entity_type = data.get("EntityToken").get("Entity").get("Type")
        entity_id = data.get("EntityToken").get("Entity").get("Id")

        requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Server/LinkServerCustomId",
            json={"ForceLink": True, "PlayFabId": playfab_id, "ServerCustomId": rjson.get("CustomId")},
            headers=settings.get_auth_headers()
        )

        return jsonify({
            "PlayFabId": playfab_id,
            "SessionTicket": session_ticket,
            "EntityToken": entity_token,
            "EntityId": entity_id,
            "EntityType": entity_type,
        }), 200
    else:
        error_info = login_request.json()
        if login_request.status_code == 403:
            if error_info.get("errorCode") == 1002:
                ban_details = error_info.get("errorDetails", {})
                ban_key = next(iter(ban_details.keys()), "Unknown Ban Reason")
                ban_expiration = ban_details.get(ban_key, ["Unknown"])[0]
                return jsonify({
                    "BanMessage": ban_key,
                    "BanExpirationTime": ban_expiration,
                }), 403
        return jsonify({"Error": "PlayFab Error", "Message": error_info.get("errorMessage", "Unknown error")}), login_request.status_code


@app.route('/api/CachePlayFabId', methods=['POST'])
def cache_playfab_id():
    data = request.json
    send_to_discord(data)
    required_fields = ['Platform', 'SessionTicket', 'PlayFabId']
    missing_fields = [field for field in required_fields if field not in data]

    if not missing_fields:
        return jsonify({"Message": "PlayFabId Cached Successfully"}), 200
    return jsonify({"Error": "Missing Data", "MissingFields": missing_fields}), 400


def validate_nonce(user_id: str, nonce: str):
    url1 = f"https://graph.oculus.com/user_nonce_validate?nonce={nonce}&user_id={user_id}&access_token={settings.ApiKey}"
    url2 = f"https://graph.oculus.com/user_nonce_validate?nonce={nonce}&user_id={user_id}&access_token={settings.ApiKey2}"
    url3 = f"https://graph.oculus.com/user_nonce_validate?nonce={nonce}&user_id={user_id}&access_token={settings.ApiKey3}"
    headers = {'Content-Type': 'application/json'}

    def get_valid():
        try:
            for url in [url1, url2, url3]:
                result = requests.post(url=url, headers=headers)
                if result.json().get('is_valid'):
                    return True
            print('Warning: is_valid not in data')
        except Exception as e:
            print(f'Error checking nonce validity: {e}')
        return False

    return get_valid()


@app.route("/api/TitleData", methods=["POST", "GET"])
def title_data():
    response = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/GetTitleData",
        headers=settings.get_auth_headers()
    )

    if response.status_code == 200:
        response_json = response.json()
        data = response_json.get("data", {}).get("Data", {})
        return jsonify(json.loads(json.dumps(data).replace("\\\\", "\\")))
    return jsonify({"error": "Failed to fetch data"}), response.status_code


@app.route("/api/TitleDataQuest", methods=["POST", "GET"])
def titled_data():
    return title_data()


@app.route('/api/dlcownership', methods=['POST'])
def aordlcownership():
    return jsonify({"result": True}), 200


@app.route("/api/CheckForBadName", methods=["POST", "GET"])
def check_for_bad_name():
    return jsonify({"result": 0})


@app.route("/api/GetAcceptedAgreements", methods=["POST", "GET"])
def get_accepted_agreements():
    rjson = request.get_json()["FunctionResult"]
    return jsonify(rjson)


@app.route("/api/SubmitAcceptedAgreements", methods=["POST", "GET"])
def submit_accepted_agreements():
    rjson = request.get_json()["FunctionResult"]
    return jsonify(rjson)


@app.route("/api/UploadGorillanalytics", methods=["POST"])
def Upload_Gorillanalytics():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    function_result = data.get("FunctionResult", {})

    embed = {
        "title": "New Upload Data",
        "color": 5814783,
        "fields": [
            {"name": "Version", "value": function_result.get("version", "N/A"), "inline": True},
            {"name": "Upload Chance", "value": function_result.get("upload_chance", "N/A"), "inline": True},
            {"name": "Map", "value": function_result.get("map", "N/A"), "inline": True},
            {"name": "Mode", "value": function_result.get("mode", "N/A"), "inline": True},
            {"name": "Queue", "value": function_result.get("queue", "N/A"), "inline": True},
            {"name": "Player Count", "value": str(function_result.get("player_count", "N/A")), "inline": True},
            {"name": "Position", "value": f"({function_result.get('pos_x', 'N/A')}, {function_result.get('pos_y', 'N/A')}, {function_result.get('pos_z', 'N/A')})", "inline": False},
            {"name": "Velocity", "value": f"({function_result.get('vel_x', 'N/A')}, {function_result.get('vel_y', 'N/A')}, {function_result.get('vel_z', 'N/A')})", "inline": False},
            {"name": "Cosmetics Owned", "value": function_result.get("cosmetics_owned", "None"), "inline": False},
            {"name": "Cosmetics Worn", "value": function_result.get("cosmetics_worn", "None"), "inline": False},
        ],
    }

    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        "https://discord.com/api/webhooks/1383507052617273496/SLZTzdWPfrJ2y0oSn_kCscXWxSOuNvW8PqakcK7-R2R3lENAyA32nPGaiqH0B7xFRxcZ",
        json=payload,
        headers=headers,
    )

    if response.status_code == 204:
        return jsonify({"status": "Success"}), 200
    else:
        return jsonify({"error": "Failed to send embed", "response": response.text}), 500


@app.route("/api/ConsumeOculusIAP", methods=["POST"])
def consume_oculus_iap():
    rjson = request.get_json()

    for key in [settings.ApiKey, settings.ApiKey2, settings.ApiKey3]:
        response = requests.post(
            url=f"https://graph.oculus.com/consume_entitlement?nonce={rjson.get('nonce')}&user_id={rjson.get('userID')}&sku={rjson.get('sku')}&access_token={key}",
            headers={"content-type": "application/json"},
        )
        if response.json().get("success"):
            return jsonify({"result": True})
    return jsonify({"error": True})


@app.route('/api/returnmyoculushash', methods=["POST"])
def returnmyoculushashv2():
    return return_function_json(request.get_json(), "ReturnMyOculusHash")


@app.route('/api/returncurrentversion', methods=["POST"])
def returncurrentversionv2():
    return return_function_json(request.get_json(), "ReturnCurrentVersion")


@app.route('/api/trydistributecurrency', methods=["POST"])
def trydistributecurrencyv2():
    return return_function_json(request.get_json(), "TryDistributeCurrency")


@app.route('/api/broadcastmyroom', methods=["POST"])
def broadcastmyroomv2():
    return return_function_json(request.get_json(), "BroadcastMyRoom", request.get_json()["FunctionParameter"])


@app.route('/api/ShouldUserAutomutePlayer', methods=["POST"])
def shoulduserautomuteplayer():
    data = request.get_json()
    return jsonify(data.get("muteCache", {}))


@app.route("/api/photon/authenticate", methods=["POST"])
def photon_authenticate():
    user_id = request.args.get("username")
    return jsonify({"ResultCode": 1, "UserId": user_id.upper()})


@app.route("/api/photon/authenticate/pcvr", methods=["POST"])
def photon_authenticate_pcvr():
    user_id = request.args.get("username")
    try:
        response = requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
            json={"PlayFabId": user_id},
            headers=settings.get_auth_headers(),
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({
            "resultCode": 0,
            "message": f"Something went wrong: {str(e)}",
            "userId": None,
            "nickname": None,
        })

    try:
        nickname = response.json().get("UserInfo", {}).get("UserAccountInfo", {}).get("Username", None)
    except Exception as e:
        return jsonify({
            "resultCode": 0,
            "message": f"Error parsing response: {str(e)}",
            "userId": None,
            "nickname": None,
        })

    return jsonify({"ResultCode": 1, "UserId": user_id.upper()})


def log_bad_name(name, id):
    filepath = f'Users/{id}.json'
    logs = {}

    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            logs = json.load(f)

    logs.setdefault(id, {}).setdefault(name, 0)
    logs[id][name] += 1

    with open(filepath, 'w') as f:
        json.dump(logs, f)


def send_to_discord(data):
    payload = {"content": json.dumps(data)}
    headers = {'Content-Type': 'application/json'}
    requests.post(settings.DiscordWebhook, json=payload, headers=headers)


def discord_message(message):
    payload = {"content": str(message)}
    headers = {'Content-Type': 'application/json'}
    requests.post(settings.DiscordWebhook, json=payload, headers=headers)


if os.path.exists('data.json'):
    with open('data.json', 'r') as f:
        config = json.load(f)
else:
    config = {}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1010)
