import api, threading
import json
from urllib.parse import urlparse, parse_qs, urlsplit
from datetime import datetime, timezone

hmac_key = 'INSERT_KEY_HERE'
hmac_secret = 'INSERT_SECRET_HERE'

conn = api.hmac(hmac_key, hmac_secret)

#Fetch Listings and pick for Specific Bank : VENEZUELA
def auto_pick (qty, listings, list):
    for bdv in listings['data']['ad_list']:
        #and (bdv['data']['is_low_risk'])
        if ('Venezuela' in bdv['data']['bank_name']) or ('VENEZUELA' in bdv['data']['bank_name']) or ('BDV' in bdv['data']['bank_name']):
            time = datetime.strptime(bdv['data']['profile']['last_online'], "%Y-%m-%dT%H:%M:%S%z")
            now = datetime.now(timezone.utc)
            delta = now - time
            delta= delta.seconds
            hour = delta//3600
            minutes = (delta % 3600)//60
            seconds = (delta % 3600)%60
            last_seen = 'hace '+str(hour)+'h '+str(minutes)+'m '+str(seconds)+'s.'
            ad_id = bdv['data']['ad_id']
            ad_id = str(ad_id)
            show=""
            mini = 0
            maxi = 0
            if (bdv['data']['max_amount'] != None and bdv['data']['min_amount'] != None):
                mini = int(bdv['data']['min_amount'])
                maxi = int(bdv['data']['max_amount'])
            if ( mini != 0 and maxi != 0 and qty >= mini and qty <= maxi):
                price = int(bdv['data']['temp_price'][:-3])
                costo = qty/price
                costo = str(costo)
                show ='costo: '+costo[:6]+' '+last_seen + ad_id
            show = ''.join(show)
            list.append(show)
    return list

#Get listing from specific bank and quantity
def get_listings (qty):
    listings = conn.call('GET', '/sell-bitcoins-online/VES/transfers-with-specific-bank/.json').json()
    parsed = urlparse(listings['pagination']['next'])
    params = parse_qs(parsed.query)
    second = conn.call('GET', '/sell-bitcoins-online/VES/transfers-with-specific-bank/.json', params=params).json()
    list=[]
    pag_uno = auto_pick(qty, listings, list)
    pag_dos = auto_pick(qty, second, list)
    return list

#Get released bitcoins time
def released_at(contact_info):
    gege = conn.call('GET', '/api/contact_info/'+contact_info+'/').json()
    return gege['data']['released_at']

#Get Payment completed Time
def payment_completed(contact_info):
    gege = conn.call('GET', '/api/contact_info/'+contact_info+'/').json()
    return gege['data']['payment_completed_at']

#Get Last Contact ID
def get_contact_id():
    try:
        get=conn.call('GET','/api/dashboard/seller/').json()
        return get['data']['contact_list'][0]['data']['contact_id']
    except Exception as error:
            print('An exception occurred: {}'.format(error))

#Get Open Trades
def is_trade():
    get=conn.call('GET','/api/dashboard/seller/').json()
    if (get != None):
        return get['data']['contact_count']

#Open trade
def open_trade(ad_id, amount):
    params = {'amount': amount, 'message': 'Specific message with bank account details in order to get transfers'}
    trade = conn.call('POST', '/api/contact_create/'+ad_id+'/', params=params).json()
    return trade

#Send message to contact
def send_message(text, contact_id):
    params = {'msg': text}
    mssg = conn.call('POST', '/api/contact_message_post/'+contact_id+'/', params=params).json()
    return mssg


#Read coversation with contact
def read_messages():
    contact_id = get_contact_id()
    contact_id = str(contact_id)
    messages = conn.call('GET', '/api/contact_messages/'+contact_id+'/').json()
    conversation = []
    if messages != None:
        for msg in messages['data']['message_list']:
            if msg['msg'] != '':
                conversation.append(msg['msg'])
            else:
                a = 'attachment_type' in msg
                if a == True:
                    link = msg['attachment_url']
                    attachment_num = urlsplit(link)[2]#.split('/')[-2]
                    call = conn.call('GET', attachment_num )
                    name = msg['attachment_name']
                    print(name)
                    with open('C:/inetpub/dist/lbc_images/'+name, 'wb') as file:
                        file.write(call.content)
                    conversation.append(name)
    return conversation

#Release bitcoins
def release_bitcoins (contact_id):
    #emergency pin
    #params = {'pincode': pin, }
    contact_id = str(contact_id)
    release = conn.call('POST', '/api/contact_release/'+contact_id+'/').json()
    return release


#Get exchange rate for specfic local currency
def cost_aprox(qty):
    ves = conn.call('GET','/bitcoinaverage/ticker-all-currencies/').json()
    ves = float(ves['VES']['rates']['last'])
    costo = round(qty/ves,4)
    costo = str(costo)
    return costo

#Get Wallet Balance and show in currencies
def get_balance():
    wallet = conn.call('GET','/api/wallet-balance/').json()
    bits = float(wallet['data']['total']['sendable'])
    cur = conn.call('GET','/bitcoinaverage/ticker-all-currencies/').json()
    ves = float(cur['VES']['rates']['last'])
    usd = float(cur['USD']['rates']['last'])
    bolivares = round(bits*ves,2)
    bolivares = str(bolivares)
    dolares = round(bits*usd,2)
    dolares = str(dolares)
    balance = wallet['data']['total']['sendable'],' BTC o ~',bolivares,' Bolivares o ~',dolares, ' $'
    balance = ''.join(balance)
    print(balance)
    return balance

#Get Deposit Address
def get_deposit():
    wallet = conn.call('GET','/api/wallet-balance/').json()
    address = wallet['data']['receiving_address']
    address = ''.join(address)
    return address
