import tweepy
import random
from PIL import Image
from PIL import ImageEnhance
import os
import logging
import time

# initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# initialize lyric and photo store to prevent repeats
last_lyric_index = -1
lyric_store = [None]*12

last_photo_index = -1
photo_store = [None]*12

# begin helper functions
def create_api():
    file = open('credentials.txt', 'r')
    CONSUMER_KEY = file.readline().strip()
    CONSUMER_SECRET = file.readline().strip()
    ACCESS_TOKEN = file.readline().strip()
    ACCESS_TOKEN_SECRET = file.readline().strip()

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    file.close()
    return api


def get_rand_lyric():
    file = open('lyrics.txt', 'r')
    lines = file.readlines()
    lyric = ''
    # want a random line but some of them are just new line characters or dashes for ease of reading
    while (lyric == '' or lyric == '----'):
        r = random.randrange(len(lines))
        lyric = lines[r].strip().lower()
    file.close()
    return lyric


def write_last_seen_id(file_name, id):
    file = open(file_name, 'w')
    file.write(str(id))
    file.close()


def read_last_seen_id(file_name):
    file = open(file_name, 'r')
    last_id = int(file.read())
    file.close()
    return last_id


def fry_image():
    # fetch suitable stock photo
    photo = random.choice(os.listdir('./stock-photos'))
    while photo in photo_store:
        photo=random.choice(os.listdir('./stock-photos'))
    update_store('photo', photo)
    logger.info(f'frying {photo}')

    # fry stock-photo
    img = Image.open('./stock-photos/' + photo)
    saturater = ImageEnhance.Color(img)
    img = saturater.enhance(6)
    sharpener = ImageEnhance.Sharpness(img)
    img = sharpener.enhance(6)
    img.save('./fried-image.jpg')

# api interacts with tweets here
def respond_to_tweet(api, tweet):
    # favorite tweet
    try:
        api.create_favorite(tweet.id)
    except:
        logger.info(f'Already favorited')
    # prepare image
    fry_image()
    # find suitable lyric
    lyric=get_rand_lyric()
    while lyric in lyric_store:
        lyric=get_rand_lyric()
    update_store('lyric', lyric)
    # send tweet
    api.update_with_media(
        './fried-image.jpg',
        status=lyric,
        in_reply_to_status_id=tweet.id,
        auto_populate_reply_metadata=True
    )


def check_mentions(api, last_seen_id):
    logger.info(f'Retrieving mentions')
    new_last_seen_id = last_seen_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=last_seen_id).items():
        # update id
        new_last_seen_id = max(tweet.id, new_last_seen_id)
        logger.info(f'Answering to {tweet.user.name}')
        # request to follow user
        if not tweet.user.following:
            try:
                tweet.user.follow()
            except:
                logger.info(f'Already following {tweet.user.name}')
        respond_to_tweet(api, tweet)
    return new_last_seen_id

# api interacts with followers here
def follow_followers(api):
    logger.info(f'Retrieving and following followers')
    for follower in tweepy.Cursor(api.followers).items():
        if not follower.following:
            logger.info(f'Following {follower.name}')
            try:
                follower.follow()
            except:
                logger.info(f'Already following {follower.name}')


def check_mag_tweets(api, last_seen_id):
    logger.info(f'Retrieving magazine beaches tweets')
    new_last_seen_id = last_seen_id
    for tweet in tweepy.Cursor(api.user_timeline, id='@magazinebeans', since_id=last_seen_id, include_rts=False, exclude_replies=True).items():
        # update id
        new_last_seen_id = max(tweet.id, new_last_seen_id)
        logger.info(f'thirsting the beach')
        respond_to_tweet(api, tweet)
    return new_last_seen_id

def update_store(store, value):
    logger.info(f'Updating {store}_store')
    if store == 'lyric':
        global last_lyric_index 
        last_lyric_index += 1
        last_lyric_index = last_lyric_index % 12
        lyric_store[last_lyric_index] = value
    else:
        global last_photo_index 
        last_photo_index += 1
        last_photo_index = last_photo_index % 12
        photo_store[last_photo_index] = value


# end helper functions

def main():
    api = create_api()
    last_seen_mention_id = read_last_seen_id('last-seen-mention-id.txt')
    last_seen_mag_id = read_last_seen_id('last-seen-mag-id.txt')
    while True:
        follow_followers(api)
        last_seen_mention_id = check_mentions(api, last_seen_mention_id)
        write_last_seen_id('last-seen-mention-id.txt', last_seen_mention_id)
        logger.info('Waiting...')
        time.sleep(60)


if __name__ == '__main__':
    main()
