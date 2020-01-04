import urllib3, json

NEWDECK = 'https://deckofcardsapi.com/api/deck/new/shuffle/'
DRAWCARDS = 'https://deckofcardsapi.com/api/deck/{}/draw/'

class RequestException(Exception):
    pass

def newdeck():
    ''' newdeck(): calls deck of cards API to create a new deck '''
    http = urllib3.PoolManager()
    response = http.request('GET',NEWDECK)
    data = json.loads(response.data.decode('utf-8'))
    if data and data['success']:
        return data['deck_id']
    # if we didn't get data we go here
    print(data)
    raise RequestException("new deck call: data printed to console")

def drawcards(deck_id,n):
    ''' drawcards(): calls deck of cards API to draw n cards from the specified deck id '''
    http = urllib3.PoolManager()
    response = http.request(
        'GET',
        DRAWCARDS.format(deck_id),
        { 'count':n }
        )
    data = json.loads(response.data.decode('utf-8'))
    if data and data['success']:
        return data['cards']
    # if we didn't get data we go here
    print(data)
    raise RequestException("draw card call: data printed to console")
