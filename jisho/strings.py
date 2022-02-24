# "Constants"
BOT_DESC = 'wip bot for jisho.org'
BOT_VERSION = 'Beta 2'
JISHOHOME_URL = 'https://jisho.org'
JISHO_API_SEARCH = "http://jisho.org/api/v1/search/words"
EMOJI_NUMS = {1: ':one:', 2: ':two:', 3: ':three:', 4: ':four:', 5: ':five:'} # mabye this should be combined with REACT_NUMS
ERROR_BADSTATUS_STEM = 'Bad response status - expected 200 OK, got {status} instead'
ERROR_INDEXERROR_STEM = 'Unable to find result number {number} for {query}'

# Reaction emojis
REACT_ARROW_LEFT = "\u25C0\uFE0F"
REACT_ARROW_RIGHT = "\u25B6\uFE0F"
REACT_NUM_ONE = "\N{KEYCAP DIGIT ONE}"
REACT_NUM_TWO = "\N{KEYCAP DIGIT TWO}"
REACT_NUM_THREE = "\N{KEYCAP DIGIT THREE}"
REACT_NUM_FOUR = "\N{KEYCAP DIGIT FOUR}"
REACT_NUM_FIVE = "\N{KEYCAP DIGIT FIVE}"
REACT_RETURN = "\u21A9\uFE0F"
REACT_X = "\u274C"
REACTS_ARROWS = [REACT_ARROW_LEFT, REACT_ARROW_RIGHT]
REACTS_NUMS = [REACT_NUM_ONE, REACT_NUM_TWO, REACT_NUM_THREE, REACT_NUM_FOUR, REACT_NUM_FIVE]
REACTS_ALL = REACTS_ARROWS + REACTS_NUMS + [REACT_RETURN, REACT_X]

COMMAND_HELP = 'help'
# COMMAND_HELP_ALIAS = 'h'
# COMMAND_HELP_SYNTAX = f'`{COMMAND_PREFIX} {COMMAND_HELP}`'
# COMMAND_HELP_DESC = f'{COMMAND_HELP_SYNTAX} - Shows this help message - *alias: `{COMMAND_HELP_ALIAS}`*'

COMMAND_SEARCH = 'search'
COMMAND_SEARCH_ALIAS = 's'
#COMMAND_SEARCH_SYNTAX = f'`{COMMAND_PREFIX} {COMMAND_SEARCH} <query>`'
COMMAND_SEARCH_DESC_SHORT = 'Searches jisho.org for <query>'
# COMMAND_SEARCH_DESC = f'{COMMAND_SEARCH_SYNTAX} - Searches jisho.org for `query` - *alias: `{COMMAND_SEARCH_ALIAS}`*'

COMMAND_DETAILS = 'details'
COMMAND_DETAILS_ALIAS = 'd'
#COMMAND_DETAILS_SYNTAX = f'`{COMMAND_PREFIX} {COMMAND_DETAILS} <num> <query>`'
COMMAND_DETAILS_DESC_SHORT = 'Shows details for the <num>th result for <query>'
# COMMAND_DETAILS_DESC = f'{COMMAND_DETAILS_SYNTAX} - Shows details for the `num`th result for `query` - *alias: `{COMMAND_DETAILS_ALIAS}`*'

COMMAND_PING = 'ping'
COMMAND_PING_ALIAS = 'p'
#COMMAND_PING_SYNTAX = f'`{COMMAND_PREFIX} {COMMAND_PING}`'
COMMAND_PING_DESC_SHORT = 'Pings jisho-bot'
# COMMAND_PING_DESC = f'{COMMAND_PING_SYNTAX} - Pings jisho-bot to respond with a pong - *alias: `{COMMAND_PING_ALIAS}`*'

COMMAND_LINK = 'link'
COMMAND_LINK_ALIAS = 'l'
#COMMAND_LINK_SYNTAX = f'`{COMMAND_PREFIX} {COMMAND_LINK} <link>`'
COMMAND_LINK_DESC_SHORT = 'Analyzes a jisho.org link and tries to show details'
# COMMAND_LINK_DESC = f'{COMMAND_LINK_SYNTAX} - Analyzes a jisho.org link and tries to show details - *alias: `{COMMAND_LINK_ALIAS}`*'

COMMAND_VERSION = 'version'
COMMAND_VERSION_ALIAS = 'v'
#COMMAND_VERSION_SYNTAX = f'`{COMMAND_PREFIX} {COMMAND_VERSION}'
COMMAND_VERSION_DESC_SHORT = 'Checks jisho-bot version'


ERROR_INCORRECTARGS_STEM = 'Incorrect arguments - correct syntax is {syntax}'
#UNKNOWN_RESPONSE = f'Unrecognized command, try `{COMMAND_PREFIX} {COMMAND_HELP}` to see a list of recognized commands'

# Link analysis constants
LINK_BASE = 'jisho.org'
LINK_SEARCH = 'search'
LINK_DETAILS = 'word'
LINK_KANJI = '%23kanji'  # or '#kanji'
LINK_SLUGSEARCH_STEM = '&slug={slug}'
ERROR_LINK_NOTJISHO = 'Not a recognized jisho.org link'
ERROR_LINK_NOTYPE = 'Unable to analyze link (error: NOTYPE)'
ERROR_LINK_NOQUERY = 'Unable to determine search query'
ERROR_LINK_NOKANJI = 'Kanji data not currently supported by API'

# Embed constants
EMBED_THUMBNAIL_JISHO = 'https://assets.jisho.org/assets/touch-icon-017b99ca4bfd11363a97f66cc4c00b1667613a05e38d08d858aa5e2a35dce055.png'

# EMBED_HELP_TITLE = 'jisho-bot help'
# EMBED_HELP_FOOTER = 'jisho-bot is not affiliated with jisho.org in any way.'
# EMBED_HELP_FIELD_ABOUT_NAME = '__About__'
# EMBED_HELP_FIELD_ABOUT_VALUE = 'jisho-bot is currently a work-in-progress bot that searches jisho.org directly ' \
#                                + f'from Discord, powered by [jisho.org]({JISHOHOME_URL})\'s beta API.'
# EMBED_HELP_FIELD_LOOKUP_NAME = '__Lookup commands__'
# EMBED_HELP_FIELD_LOOKUP_VALUE = '\n'.join([COMMAND_SEARCH_DESC, COMMAND_DETAILS_DESC, COMMAND_LINK_DESC])
# EMBED_HELP_FIELD_UTILITY_NAME = '__Utility commands__'
# EMBED_HELP_FIELD_UTILITY_VALUE = '\n'.join([COMMAND_HELP_DESC, COMMAND_PING_DESC])

EMBED_SEARCH_TITLE_STEM = 'jisho.org search results for {query}'
EMBED_SEARCH_DESCRIPTION_STEM = '*Showing results {start} to {end} (out of {total})*\n'
EMBED_SEARCH_DESCRIPTION_NORESULTS = '*Sorry, no results were found*'
EMBED_SEARCH_RESULT_FORMAT = '{emoji}: {result}\n'
EMBED_SEARCH_URL_STEM = 'https://jisho.org/search/{query}'
EMBED_SEARCH_FOOTER = 'Use the reacts for more actions\nPowered by jisho.org\'s beta API'

EMBED_DETAILS_TITLE_STEM = 'jisho.org entry for {slug}'
EMBED_DETAILS_URL_STEM = 'https://jisho.org/word/{slug}'
EMBED_DETAILS_FOOTER_STEM = 'jisho.org entry data from {sources}\nPowered by jisho.org\'s beta API'
EMBED_DETAILS_FIELD_WORD_NAME = '__Word__'
EMBED_DETAILS_FIELD_TAGS_NAME = '__Tags__'
EMBED_DETAILS_FIELD_DEFINITIONS_NAME = '__Definition(s)__'
EMBED_DETAILS_FIELD_DEFINITIONSTRUNC_NAME = '__Defintions(s) *(some results have been truncated)*__'
EMBED_DETAILS_FIELD_OTHERFORMS_NAME = '__Other forms__'
EMBED_DETAILS_TAGS_COMMON = 'Common word'
EMBED_DETAILS_TAGS_JLPTLEVEL_STEM = 'JLPT N{level}'
EMBED_DETAILS_TAGS_WKURL_STEM = 'https://www.wanikani.com/search?query={query}'
EMBED_DETAILS_TAGS_WKLEVEL_STEM = 'WaniKani level {level}'
EMBED_DETAILS_TAGS_WANIKANI_STEM = f'[{EMBED_DETAILS_TAGS_WKLEVEL_STEM}]({EMBED_DETAILS_TAGS_WKURL_STEM})'
EMBED_DETAILS_TAGS_NONE = '*None*'

EMBED_ERROR_TITLE = 'An error has occurred'
EMBED_ERROR_FOOTER = 'Please report any unexpected errors'
