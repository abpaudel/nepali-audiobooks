from datetime import datetime
from pathlib import Path


def save_rss_feed(audiobooks, save_path):
    '''Generates an rss feed for the audiobooks to be used with podcast apps'''
    save_path = Path(save_path)
    save_path.parent.mkdir(exist_ok=True)
    github_url = 'https://github.com/abpaudel/nepali-audiobooks'
    cover_image = 'https://abpaudel.com/nepali-audiobooks/nepali-audiobooks.jpg'
    summary = ('A curated collection of Nepali audiobooks, novels and stories from Shruti Sambeg and other programs. '
               'The audiobooks are collected from publicly available sources.\n'
               f'Find more details at <a href="{github_url}">{github_url}</a>')
    current_datetime = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    rss_feed_start = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">\n'
        '<channel>\n'
        '    <itunes:block>yes</itunes:block>\n'
        '    <title>Nepali Audiobooks</title>\n'
        f'    <lastBuildDate>{current_datetime}</lastBuildDate>\n'
        f'    <link>{github_url}</link>\n'
        '    <language>en-us</language>\n'
        '    <itunes:author>github.com/abpaudel</itunes:author>\n'
        '    <image>\n'
        f'        <url>{cover_image}</url>\n'
        '        <title>Nepali Audiobooks</title>\n'
        f'        <link>{github_url}</link>\n'
        '    </image>\n'
        '    <itunes:summary\n>'
        f'       <![CDATA[{summary}]]>\n'
        '    </itunes:summary>\n'
        '    <description>\n'
        f'       <![CDATA[{summary}]]>\n'
        '    </description>\n'
        f'    <itunes:image href="{cover_image}"/>\n'
        '    <itunes:category text="Arts"/>\n'
        '    <itunes:category text="Literature"/>\n'
        '    <itunes:category text="Books"/>\n'
        '    <itunes:explicit>no</itunes:explicit>\n'
        '    <itunes:keywords>shruti sambeg, nepali novels, nepali audiobooks, nepali books</itunes:keywords>\n'
        '    <itunes:type>episodic</itunes:type>\n'
    )

    rss_items = ''
    audiobook_count = 0
    total_episode_count = 0
    print('\nExporting audiobooks to RSS feed...')

    for audiobook in audiobooks:
        print(f"\t{audiobook['title']} ({len(audiobook['episodes'])} episodes)")
        for episode in audiobook['episodes']:
            title = f"{audiobook['title']} - {episode['episode_number']}"
            description = f'{title}\n'
            description += f'Report issues with episodes at <a href="{github_url}">{github_url}</a>.\n\n'
            description += audiobook['description']
            description += '\nEpisode description/links courtesy of https://hamroawaz.blogspot.com.'
            pubdate = audiobook['timestamp']
            image = audiobook['cover_image_link']
            image = cover_image if image == '' else image
            audiobook_link = audiobook['link']
            subtitle = episode['episode_name'] if episode['episode_name'] != '' else title
            episode_link = episode['link']
            rss_item = (
                '       <item>\n'
                f'            <title>{title}</title>\n'
                '            <description>\n'
                f'                <![CDATA[{description}]]>\n'
                '            </description>\n'
                f'            <pubDate>{pubdate}</pubDate>\n'
                f'            <link>{audiobook_link}</link>\n'
                f'            <itunes:subtitle>{subtitle}</itunes:subtitle>\n'
                f'            <enclosure url="{episode_link}" type="audio/mpeg"/>\n'
                f'            <itunes:image href="{image}"/>\n'
                '            <itunes:explicit>no</itunes:explicit>\n'
                '        </item>\n'
            )
            rss_items += rss_item
            total_episode_count += 1
        audiobook_count += 1

    rss_feed_end = '</channel>\n</rss>\n'
    rss_feed = rss_feed_start + rss_items + rss_feed_end
    with open(save_path, 'w') as f:
        f.write(rss_feed)
    print(f'Saved RSS feed with {audiobook_count} audiobooks '
          f'with a total of {total_episode_count} episodes at {save_path}.')
