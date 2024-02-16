import requests
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
from rss import save_rss_feed


def get_all_audiobooks(main_page_url, post_class='post hentry', content_class='post-body entry-content'):
    response = requests.get(main_page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Look for links within li tags
    li_tags = soup.find('div', class_=content_class).find_all('li')
    links = [li.find('a', href=True) for li in li_tags]
    audiobooks = []
    for i, link in enumerate(links):
        link['href'] = clean_link(link['href'])
        title = link.get('title', link.text).strip()
        link['title'] = title[0].upper() + title[1:]
        print(f"Scraping {i+1}/{len(links)}: {link['href']}")
        print(f"\tTitle: {link['title']}")
        audiobook = scrape_audiobook_episodes(link['href'], post_class, content_class)
        if audiobook is None:
            continue
        # If audio files were not found, go one link further
        if 'episodes' not in audiobook:
            print("\tGoing one link deeper...")
            response_ = requests.get(link['href'])
            soup_ = BeautifulSoup(response_.text, 'html.parser').find('div', class_=content_class)
            # Find and scrape each link to look for audio files
            ahref_tags = soup_.find_all('a', href=True)
            for ahref_tag in ahref_tags:
                ahref_tag['href'] = clean_link(ahref_tag['href'])
                if not verify_link(ahref_tag['href'], title=link['title']):
                    continue
                audiobook_ = scrape_audiobook_episodes(ahref_tag['href'], post_class, content_class, is_retry=True)
                if 'episodes' in audiobook_:
                    audiobook['episodes'] = audiobook_['episodes']
                    print(f"\t\tValid link at {ahref_tag['href']}")
                    break
        audiobook['title'] = link['title']
        if 'episodes' in audiobook:
            audiobooks.append(audiobook)
            print(f"\tFound {len(audiobook['episodes'])} episodes for {audiobook['title']}.")
        else:
            print(f"\tNo episodes found for {audiobook['title']}.")
    # Sort audiobooks by title
    audiobooks = sorted(audiobooks, key=lambda x: x['title'])
    return audiobooks


def scrape_audiobook_episodes(link, post_class, content_class, is_retry=False):
    if link.startswith('javascript'):
        return {}
    response = requests.get(link)
    soup_page = BeautifulSoup(response.text, 'html.parser')
    soup = soup_page.find('div', class_=post_class)
    if soup is None:
        print(f"\tCannot scrape {link}")
        return {}
    audiobook = {}
    if not is_retry:
        # Find date/time published
        timestamp_tag = soup.find('abbr', class_='published')
        if timestamp_tag is None:
            timestamp_tag = soup_page.find('abbr', class_='published')
        # Find description and cover image
        soup = soup.find('div', class_=content_class)
        description = soup.text.strip()
        description = description.replace('Your browser does not support the audio element', '')
        description = description.replace('Sorry, your browser does not support HTML5 audio.', '')
        description = ' '.join(description.split())
        cover_image = soup.find('img')
        cover_image_link = clean_link(cover_image['src']) if cover_image is not None else ''
        timestamp = datetime.strptime(timestamp_tag['title'], '%Y-%m-%dT%H:%M:%S%z')
        timestamp = timestamp.strftime('%a, %d %b %Y %H:%M:%S %z')
        print(f"\tDescription: {description[:150]}")
        print(f"\tImage: {cover_image_link}")
        print(f"\tPublished: {timestamp}")
        audiobook['link'] = link
        audiobook['description'] = description
        audiobook['cover_image_link'] = cover_image_link
        audiobook['timestamp'] = timestamp

    # Look for ahref links to mp3 files
    audio_tags = soup.find_all('a', href=lambda href: (href and href.strip().endswith('.mp3')))
    if audio_tags:
        for audio_tag in audio_tags:
            audio_tag['link'] = clean_link(audio_tag['href'])
        episodes_ahref = get_episodes_from_audio_tag(audio_tags)
    else:
        episodes_ahref = []
    # Look for audio tags
    audio_tags = soup.find_all('audio')
    if audio_tags:
        for audio_tag in audio_tags:
            audio_tag['link'] = clean_link(audio_tag.find('source')['src'])
        episodes_audio = get_episodes_from_audio_tag(audio_tags)
    else:
        episodes_audio = []
    # Verify that at least one of them has contents
    if len(episodes_ahref) + len(episodes_audio) > 0:
        audiobook['episodes'] = episodes_ahref if len(episodes_ahref) > len(episodes_audio) else episodes_audio
    return audiobook


def get_episode_name(audio_tag):
    tag_name = audio_tag.name
    if tag_name == 'a':
        return audio_tag.text.strip()
    if tag_name == 'audio':
        strong_tag = audio_tag.find_previous('strong')
        if strong_tag:
            title = strong_tag.text.strip()
            next_sibling = strong_tag.next_sibling
            if next_sibling and next_sibling.name != 'br' and next_sibling.strip() != '':
                episode_name = f'{title} - {next_sibling.strip()}'
            else:
                episode_name = title
            return episode_name[:70].replace('&', '|')
    return ''


def verify_link(link, title):
    '''Naively verify that the link corresponds to the given title.'''
    if not link.startswith('http'):
        return False
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser').find('post-title')
    if soup is None:
        return False
    post_title = soup.text
    if title.split()[0] in post_title:
        return True
    return False


def clean_link(link):
    if link.startswith("//"):
        link = 'https:' + link
    elif link.startswith("http://"):
        link = link[:4] + 's' + link[4:]
    return link.strip()


def get_episodes_from_audio_tag(audio_tags):
    episodes = []
    added_links = []  # Maintain a list of links to avoid duplicates
    for audio_tag in audio_tags:
        if audio_tag['link'] in added_links:
            continue
        added_links.append(audio_tag['link'])
        episodes.append({'link': audio_tag['link'],
                         'episode_name': get_episode_name(audio_tag),
                         'episode_number': len(added_links)})
    return episodes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--main-page-url', default="https://hamroawaz.blogspot.com/2012/04/shruti-sambeg.html")
    parser.add_argument('--rss-path', default='./feed/rss.xml', help='Path of XML file where RSS feed is generated.')
    args = parser.parse_args()

    audiobooks = get_all_audiobooks(args.main_page_url)
    save_rss_feed(audiobooks, save_path=args.rss_path)
