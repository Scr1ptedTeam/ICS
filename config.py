import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# ========== КУКИ (обновите при необходимости) ==========
COOKIES = {
    '__ddg1_': '9XPjSXZG9a6WDFAprBid',
    '_ym_uid': '1783955517502440301',
    '_ym_d': '1783955517',
    '_ym_isad': '2',
    '__ddg8_': 'SiwqkWBdkTbFJtVd',
    '__ddg10_': '1785578739',
    '__ddg9_': '104.28.165.105',
    '_ym_visorc': 'w',
    'XSRF-TOKEN': 'eyJpdiI6InZTbE1TNURhUTJWNE81TDYzdlQ5eEE9PSIsInZhbHVlIjoic0JHSFE2Q3dRclh6TU5pQldrV2NmTU9mcWpKdVZHak9Nc1o3QzlBOVM0VHhjbDUxaDZuZmtwdHpUYjRKMENMTVQrUFN2Ti9zVEpwck9ncitvZ1h1Z2ZxdDZjTkVCOW1uV29VWWxIb3Y2MTFqUUhtQlF4aFlrNWF1QnVuU1ZROWMiLCJtYWMiOiJlODYzZGZlYWJiM2EyNDlkYjE3Y2JjNmY0Y2UxOTFiZjAxODc5NDQxZmQ2YTI2YjhiYzgwM2EzMWNlMDBkZmQ2IiwidGFnIjoiIn0%3D',
    'incloudgame_session': 'eyJpdiI6IjhUMXZrdnBQdzk5L0lSME5oaEdrcnc9PSIsInZhbHVlIjoiSEtLZFQzTEJTMkUvMlRlM2hERktCZFQxMGhmdjkvV2ZXVmNlQ1FmZnRUdzgra2dWOGVFYjM1V1RVcktkcXMvNUdwR1YrRXZjWXFtR0xJdlluYVdHVlF0Qm1GRUNIQi8zUlBjZWtIVHI0ZkE3SnI0QTErOUo1aUpsM1d3WUtudzkiLCJtYWMiOiJkOGYyOWE0Y2NjMzRhMjM3NGY2MzY0OWFiMzY3ZTQ4YmNlMDBhNTViYWQ5MzllM2UzNDk0YTg0YWU1NTk2NDQwIiwidGFnIjoiIn0%3D',
}

# ID канала для логов (опционально)
LOG_CHANNEL_ID = 1533064838723534858