import datetime
import requests
import threading
import time
import json

f = open('config.json',)
config = json.load(f)

OLD_NFTS = []
collections = config['collections']
avatar_url = config['avatar_url']


def getPrice(NFT):
    return int(NFT['price']) / 1000000000


def delete_nft(NFT):
    global OLD_NFTS
    print("Deleting : " + NFT['title'] + " in 10 minutes")
    time.sleep(600)
    OLD_NFTS.remove(NFT)


def getDate():
    return datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def sendCode(name, price, img, nft_url, webhook_name, webhook_url, footer_name, footer_image_url, collection, next_lowest_price):
    data = {
        "embeds": [
            {
                "title": name,
                "description": "Price : " + price + " sol",
                "url": nft_url,
                "fields": [
                    {
                        "name": "Collection",
                        "value": "[" + collection + "]" + "(" + "https://alpha.art/collection/" + collection + ")",
                        "inline": True
                    },
                    {
                        "name": "Next price",
                        "value": next_lowest_price + " sol",
                        "inline": True
                    }
                ],
                "thumbnail": {
                    "url": img
                },
                "footer": {
                    "text": footer_name + " | " + getDate(),
                    "icon_url": footer_image_url
                },
            }
        ],
        "username": "Alpha Art",
        "avatar_url": avatar_url
    }
    result = requests.post(webhook_url, json=data)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Webhook sent to : " + webhook_name)


def monitor(collection, price, webhooks):
    while True:
        data = '{"collectionId":"' + collection + \
            '","orderBy":"PRICE_LOW_TO_HIGH","status":["BUY_NOW"],"traits":[]}'
        response = requests.post(
            "https://apis.alpha.art/api/v1/collection", data=data)
        try:
            for NFTS in response.json()['tokens']:
                nft_price = getPrice(NFTS)
                if nft_price <= price and nft_price != 0 and nft_price is not None:
                    if NFTS not in OLD_NFTS:
                        OLD_NFTS.append(NFTS)
                        for webhook in webhooks:
                            sendCode(NFTS['title'], str(nft_price), NFTS['image'], "https://alpha.art/t/" +
                                     NFTS['mintId'], webhook['name'], webhook['url'], webhook['footer_name'], webhook['footer_image_url'], collection, str(getPrice(response.json()['tokens'][1])))
                        delete_nft_thread = threading.Thread(
                            target=delete_nft, args=(NFTS,))
                        delete_nft_thread.start()
        except json.decoder.JSONDecodeError:
            print("Can't reach Alpha Art.")


def main():
    for collection in collections:
        print("Monitoring : " + collection['collection'] +
              " <= " + str(collection['price']) + " sol")
        monitor_thread = threading.Thread(target=monitor, args=(
            collection['collection'], collection['price'], collection['webhooks'],))
        monitor_thread.start()


main()
