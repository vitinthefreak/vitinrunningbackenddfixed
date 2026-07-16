import requests
import random
from flask import Flask, jsonify, request

class GameInfo:
    def __init__(self):
        self.TitleId: str = "13449"
        self.SecretKey: str = "NHYJF5FP7SHQKQ1AU55UYPHQQHAZB4WBTJXCOFAJE4KQYSYETU"
        self.ApiKey: str = "OC|1184115174791506|72ce9e5acc12fe80f2f492c249eec507"
    def GetAuthHeaders(self) -> dict:
        return {
            "content-type": "application/json",
            "X-SecretKey": self.SecretKey
        }
    def GetTitle(self) -> str:
        return self.TitleId
        
settings: GameInfo = GameInfo()
app: Flask = Flask(__name__)
playfabCache: dict = {}
muteCache: dict = {}

settings.TitleId = "13449"
settings.SecretKey = "NHYJF5FP7SHQKQ1AU55UYPHQQHAZB4WBTJXCOFAJE4KQYSYETU"
settings.ApiKey = "OC|1184115174791506|72ce9e5acc12fe80f2f492c249eec507"
settings.WebhookURL = "https://discord.com/api/webhooks/1526399263406428172/Yr9y364d-Wy8_Ola_nsSvVF9aPba0qg-hEfDN9D1rSaMqO_hBMcL5uWO6QpUVMQ6icmC"


def ReturnFunctionJson(data, funcname, funcparam={}):
    rjson = data["FunctionParameter"]
    userId: str = rjson.get("CallerEntityProfile").get("Lineage").get("TitlePlayerAccountId")

    req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/ExecuteCloudScript",
        json={
            "PlayFabId": userId,
            "FunctionName": funcname,
            "FunctionParameter": funcparam
        },
        headers=settings.GetAuthHeaders()
    )

    if req.status_code == 200:
        return jsonify(req.json().get("data").get("FunctionResult")), req.status_code
    else:
        return jsonify({}), req.status_code


@app.route("/", methods=["POST", "GET"])
def main():
    return """
        <html>
            <head>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
            </head>
            <body style="font-family: 'Inter', sans-serif;">
                <h1 style="color: red; font-size: 10px;">
                   luckily none of this will work for YOU skidder
                </h1>
            </body>
        </html>
    """


# Replace https://auth-prod.gtag-cf.com/api/PlayFabAuthentication with this endpoint

def logtodiscord(title: str, description: str, color: int = 0xff0000):
    payload = {
        "username": "Nonce Logs",
        "avatar_url": "",
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color
            }
        ]
    }
    try:
        requests.post(
            settings.WebhookURL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
    except:
        pass




@app.route("/api/PlayFabAuthentication", methods=["POST", "GET"])
def PlayFabAuthentication():
    if request.content_type != "application/json":
        return jsonify({
            "BanMessage": "Your account has been traced and you have been banned.",
            "BanExpirationTime": "Indefinite"
        }), 400

    pluh = request.get_json()

    app_id = pluh.get('AppId')
    app_version = pluh.get('AppVersion')
    nonce = pluh.get('Nonce')
    oculus_id = pluh.get('OculusId')
    platform = pluh.get('Platform')


    oculus_response = requests.post(
        "https://graph.oculus.com/user_nonce_validate",
        json={
            "access_token": settings.ApiKey,
            "nonce": nonce,
            "user_id": oculus_id
        }
    )

    if oculus_response.status_code != 200 or not oculus_response.json().get("is_valid", False):
        logtodiscord(
            title="Invalid Nonce",
            description=f"**OculusId:** `{oculus_id}`\n"
                        f"**Nonce:** `{nonce}`",
            color=0xff0000
        )
        return jsonify({"Message": "Invalid Nonce", "Error": "BadRequest-Skidder"}), 400


    CustomIdNewFR = f"OCULUS{oculus_id}"
    login_req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/LoginWithServerCustomId",
        json={
            "ServerCustomId": CustomIdNewFR,
            "CreateAccount": True
        },
        headers={
            "X-SecretKey": settings.SecretKey,
            "Content-Type": "application/json"
        }
    )

    if login_req.status_code == 200:
        rjson = login_req.json().get("data")
        session_ticket = rjson.get("SessionTicket")


        logtodiscord(
            title="Valid Nonce",
            description=f"**OculusId:** `{oculus_id}`\n"
                        f"**Nonce:** `{nonce}`",
            color=0x00ff00
        )

        entity_token = rjson.get("EntityToken").get("EntityToken")
        playfab_id = rjson.get("PlayFabId")
        entity_id = rjson.get("EntityToken").get("Entity").get("Id")
        entity_type = rjson.get("EntityToken").get("Entity").get("Type")

        requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Client/LinkCustomID",
            json={
                "PlayFabId": playfab_id,
                "CustomId": CustomIdNewFR,
                "ForceLink": True
            },
            headers={
                "X-Authorization": session_ticket,
                "Content-Type": "application/json"
            }
        )

        return jsonify({
            "SessionTicket": session_ticket,
            "EntityToken": entity_token,
            "PlayFabId": playfab_id,
            "EntityId": entity_id,
            "EntityType": entity_type
        }), 200

    elif login_req.status_code == 403:
        ban_info = login_req.json()
        if ban_info.get('errorCode') == 1002:
            ban_details = ban_info.get('errorDetails', {})
            ban_expiration_key = next(iter(ban_details.keys()), None)
            ban_expiration_list = ban_details.get(ban_expiration_key, [])
            ban_expiration = ban_expiration_list[0] if len(ban_expiration_list) > 0 else "No expiration date provided."
            return jsonify({
                'BanMessage': ban_expiration_key,
                'BanExpirationTime': ban_expiration
            }), 403
        else:
            error_message = ban_info.get('errorMessage', 'Forbidden without ban information.')
            return jsonify({
                'Error': 'PlayFab Error',
                'Message': error_message
            }), 403

    else:
        playfab_error = login_req.json().get("error", {})
        error_message = playfab_error.get("errorMessage", "Login failed")
        return jsonify({
            'Error': 'PlayFab Error',
            'Message': error_message,
            'PlayFabError': playfab_error
        }), login_req.status_code


		
# Replace https://auth-prod.gtag-cf.com/api/CachePlayFabId with this endpoint
@app.route("/api/CachePlayFabId", methods=["POST", "GET"])
def cacheplayfabid():
    rjson = request.get_json()

    playfabCache[rjson.get("PlayFabId")] = rjson

    return jsonify({"Message": "Success"}), 200

# Replace https://title-data.gtag-cf.com with this endpoint
 

@app.route('/api/TitleData', methods=['POST', 'GET'])
def titledata():
    response_data = {
	"AutoMuteCheckedHours": {
            "hours": 169
        },
        "AutoName_Adverbs": [
            "Cool", "Fine", "Bald", "Bold", "Half", 
            "Only", "Calm", "Fab", "Ice", "Mad", 
            "Rad", "Big", "New", "Old", "Shy"
        ],
        "AutoName_Nouns": [
            "Gorilla", "Chicken", "Darling", "Sloth", "King", 
            "Queen", "Royal", "Major", "Actor", "Agent", 
            "Elder", "Honey", "Nurse", "Doctor", "Rebel", 
            "Shape", "Ally", "Driver", "Deputy"
        ],

    	"MOTD": "<color=#ff0000>WELCOME TO <color=#ff0000>O</color><color=#a00000>L</color><color=#870000>D</color> TAG!</color>\n\n\n<color=#00c9ff>BOOST DISCORD.GG/OLDTAG FOR EVERY COSMETIC!</color>\n\n\n<color=#cacfd2>CREDITS KRATOZZ, BT, SYSTEM</color>\n\n<color=#6fff00>THIS GAME TAKES YOU INTO OLDER GTAG UPDATES!</color>",
        "BundleBoardSign": "<color=#ff4141>DISCORD.GG/OLDTAG</color>",
        "BundleKioskButton": "<color=#ff4141>DISCORD.GG/OLDTAG</color>",
        "BundleKioskSign": "<color=#ff4141>DISCORD.GG/OLDTAG</color>",
        "BundleLargeSign": "<color=#ff4141>DISCORD.GG/OLDTAG</color>",
        "EmptyFlashbackText": "FLOOR TWO NOW OPEN\n FOR BUSINESS\n\nSTILL SEARCHING FOR\nBOX LABELED 2021",
        "EnableCustomAuthentication": True,
        "GorillanalyticsChance": 4320,
        "LatestPrivacyPolicyVersion": "2024.09.20",
        "LatestTOSVersion": "2024.09.20",
	"SeasonalStoreBoardSign": "<color=#cacfd2>SUMMER CELEBRATION!</color>",
        "TOS_2024.09.20": "DISCORD.GG/OLDTAG",
        "TOBAlreadyOwnCompTxt": "DISCORD.GG/OLDTAG",
        "TOBAlreadyOwnPurchaseBundle": "OLDTAG",
        "TOBDefCompTxt": "DISCORD.GG/OLDTAG",
        "TOBDefPurchaseBtnDefTxt": "OLDTAG",
    	"UseLegacyIAP": "false",
    }
    
    return jsonify(response_data)

# replace https://voting-prod.gtag-cf.com with this endpoint

@app.route("/api/FetchPoll", methods=["POST"])
def FetchPoll():
    global poll_shit

    whatsabool = request.get_json()

    TitleId = whatsabool.get("TitleId")
    PlayFabId = whatsabool.get("PlayFabId")
    PlayFabTicket = whatsabool.get("PlayFabTicket")

    vote_stuff = [
        {
            "PollId": 2,
            "Question": "DO YOU LIKE THIS UPDATE?",
            "VoteOptions": ["YES", "NO"],
            "VoteCount": [],
            "PredictionCount": [],
            "StartTime": f"{date.today().strftime('%Y-%m-%d')}",
            "EndTime": "2025-12-17T17:00:00",
            "isActive": True
        },
        {
            "PollId": 3,
            "Question": "ARE YOU IN THE DISCORD?",
            "VoteOptions": ["YES", "NO!"],
            "VoteCount": [50, 1000],
            "PredictionCount": [102522, 110490],
            "StartTime": "2025-03-07T18:00:00",
            "EndTime": "2025-12-14T17:00:00",
            "isActive": False
        }
    ]

    poll_shit = vote_stuff  # Connects The Global Variable

    return jsonify(vote_stuff), 200

@app.route("/api/Vote", methods=["POST"])
def Voting():
    VOTING_WEBHOOK = "https://discord.com/api/webhooks/1398705263082606723/kuZl7Kdz6kMT2mMPf25N1GHY2Dlqe_d1wxvljaXfcFzhFEwbzB1qTMBd2dPEO6I0075y" 

    get = request.get_json()

    PollId = get.get("PollId")
    TitleId = get.get("TitleId")
    PlayFabId = get.get("PlayFabId")
    OculusId = get.get("OculusId")
    UserNonce = get.get("UserNonce")
    UserPlatform = get.get("UserPlatform")
    OptionIndex = get.get("OptionIndex")
    IsPrediction = get.get("IsPrediction")
    PlayFabTicket = get.get("PlayFabTicket")
    AppVersion = get.get("AppVersion")

    if get is None:
        return jsonify({"Message": "Something Happened"}), 400

    find = next((p for p in poll_shit if p["PollId"] == PollId), None)

    if not find:
        return jsonify({"Message": "Poll not found"}), 404

    embed = {
        "embeds": [
            {
                "title": "** A PLAYER HAS VOTED :pencil: **",
                "description": (
                    "\n\n**↓ Vote Details ↓**\n\n"
                    "```"
                    f"VOTE QUESTION: {find['Question']}\n"
                    f"VOTING FOR: {find['VoteOptions'][OptionIndex]}\n"
                    f"PREDICTION: {str(IsPrediction)}\n"
                    f"PollId: {str(PollId)}\n"
                    "```\n\n"
                    "**↓ Player Details ↓**\n\n"
                    "```"
                    f"USER ID: {str(PlayFabId)}\n"
                    f"OCULUS ID: {str(OculusId)}\n"
                    f"PLATFORM: {str(UserPlatform)}\n"
                    f"PlayFabTicket: {str(PlayFabTicket)}\n"
                    f"NONCE: {str(UserNonce)}\n"
                    f"APPVERSION: {str(AppVersion)}\n"
                    f"Finally, Game Is {str(TitleId)}"
                    "```"
                ),
                "color": 63488
            }
        ]
    }

    requests.post(url=VOTING_WEBHOOK, json=embed)

    return jsonify({"Message": "Yay Votes Are Fixed, Very Cool"}), 200
	
# Replace https://iap.gtag-cf.com/api/ConsumeOculusIAP with this endpoint
@app.route("/api/ConsumeOculusIAP", methods=["POST", "GET"])
def ConsumeOculusIAP():
    rjson = request.get_json()
    uid = rjson.get("userID")
    nonce = rjson.get("nonce")
    sku = rjson.get("sku")
    iap = requests.post(url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={uid}&sku={sku}&access_token={ZGxrNVQ3OEYmTEhTe3dl}",headers={"content-type": "application/json"})
    iap1 = requests.post(url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={uid}&sku={sku}&access_token={ZHppSkpKTXZgNURiWVl}",headers={"content-type": "application/json"})
    if iap.json().get("success"):return jsonify({"result":True})
    if iap1.json().get("success"):return jsonify({"result":True})

    
if __name__ == "__main__":
    app.run("0.0.0.0", 8080)
