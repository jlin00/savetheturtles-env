import urllib3,json

NEWDECK = 'https://deckofcardsapi.com/api/deck/new/shuffle/'
DRAWCARDS = 'https://deckofcardsapi.com/api/deck/{deck_id}/draw/'

def newdeck():
    ''' newdeck(): calls deck of cards API to create a new deck '''
    http = urllib3.PoolManager()
    response = http.request('GET',NEWDECK)
    data = json.loads(response.data.decode('utf-8'))
    if data and data['success'] = true:
        return data['deck_id']
    # if we didn't get data we go here
    print(data)
    return 'yikes'
