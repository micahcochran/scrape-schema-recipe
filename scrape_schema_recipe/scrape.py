#
# Copyright 2018 Micah Cochran
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# internal libs
import datetime
import sys


# external libs
import extruct
import isodate
import requests
# for mypy
from typing import Callable, Dict, IO, List, Optional, Union
import validators

__version__ = '0.0.1'

# Follow RFC 7231 sec. 5.5.3
USER_AGENT_STR = 'scrape-schema-recipe/{} requests/{}'.format(
                                            __version__, requests.__version__)


def scrape(location: Union[str, IO[str]], python_objects: bool = False,
           nonstandard_attrs: bool = False,
           user_agent_str: Optional[str] = None) -> List[Dict]:
    """
    Parse data in https://schema.org/Recipe format into a list of dictionaries
    representing the recipe data.

    Parameters
    ----------
    location : string or file-like object
        A url, filename, or text_string of HTML, or a file-like object.

    python_object : bool, optional
        when True it translates some data types into python objects
        dates into datetime.date, datetimes into datetime.datetimes,
        durations as dateime.timedelta.  (defaults to False)

    nonstandard_attrs : bool, optional
        when True it adds nonstandard (for schema.org/Recipe) attributes to the
        resulting dictionaries, that are outside the specification such as:
            '_format' is either 'json-ld' or 'microdata' (how schema.org/Recipe was encoded into HTML)
            '_source_url' is the source url, when 'url' has already been defined as another value
        (defaults to False)

    user_agent_str : string, optional
        overide the user_agent_string with this value.
        (defaults to None)

    Returns
    -------
    list
        a list of dictionaries in the style of schema.org/Recipe JSON-LD
        no results - an empty list will be returned
    """

    data = {}  # type: Dict[str, List[Dict]]

    if not user_agent_str:
        user_agent_str = USER_AGENT_STR

    # make sure that one and only are defined
    url = None
    if isinstance(location, str):
        # Is this a url?
        if validators.url(location):
            return scrape_url(location, python_objects=python_objects,
                              nonstandard_attrs=nonstandard_attrs,
                              user_agent_str=user_agent_str)

        # Is this is is a very long string? Perhaps it has HTML content.
        elif len(location) > 255:
            data = extruct.extract(location)

        # Maybe it is a filename?
        else:
            with open(location) as f:
                data = extruct.extract(f.read())
    elif hasattr(location, 'read'):
        # Assume this is some kind of file-like object that can be read.
        data = extruct.extract(location.read())
    else:
        raise TypeError(
                  'location type "{}" is not a string for a url, filename, or '
                  'text_string of the HTML, or a file-like object.'.format(
                      type(location)))

    scrapings = _convert_to_scrapings(data, nonstandard_attrs, url=url)

    if python_objects is True:
        scrapings = _pythonize_objects(scrapings)

    return scrapings


def load(fp: Union[str, IO[str]], python_objects: bool = False,
         nonstandard_attrs: bool = False) -> List[Dict]:
    """load a filename or file object to scrape

    Parameters
    ----------
    fp : string or file-like object
        A file name or a file-like object.

    python_object : bool, optional
        when True it translates some data types into python objects
        dates into datetime.date, datetimes into datetime.datetimes,
        durations as dateime.timedelta.  (defaults to False)

    nonstandard_attrs : bool, optional
        when True it adds nonstandard (for schema.org/Recipe) attributes to the
        resulting dictionaries, that are outside the specification such as:
            '_format' is either 'json-ld' or 'microdata' (how schema.org/Recipe was encoded into HTML)
            '_source_url' is the source url, when 'url' has already been defined as another value
        (defaults to False)

    Returns
    -------
    list
        a list of dictionaries in the style of schema.org/Recipe JSON-LD
        no results - an empty list will be returned

    """

    data = {}  # type: Dict[str, List[Dict]]

    if isinstance(fp, str):
        with open(fp) as f:
            data = extruct.extract(f.read())
    elif hasattr(fp, 'read'):
        # Assume this is some kind of file-like object that can be read.
        data = extruct.extract(fp.read())
    else:
        raise TypeError('expected, fp to be a filename or a file-like object, '
                        'fp is of type {}'.format(type(fp)))

    scrapings = _convert_to_scrapings(data, nonstandard_attrs)

    if python_objects is True:
        scrapings = _pythonize_objects(scrapings)

    return scrapings


def loads(string: str, python_objects: bool = False,
          nonstandard_attrs: bool = False) -> List[Dict]:
    """scrapes a string

    Parameters
    ----------
    string : string
        A text string of HTML.

    python_object : bool, optional
        when True it translates some data types into python objects
        dates into datetime.date, datetimes into datetime.datetimes,
        durations as dateime.timedelta.  (defaults to False)

    nonstandard_attrs : bool, optional
        when True it adds nonstandard (for schema.org/Recipe) attributes to the
        resulting dictionaries, that are outside the specification such as:
            '_format' is either 'json-ld' or 'microdata' (how schema.org/Recipe was encoded into HTML)
            '_source_url' is the source url, when 'url' has already been defined as another value
        (defaults to False)

    Returns
    -------
    list
        a list of dictionaries in the style of schema.org/Recipe JSON-LD
        no results - an empty list will be returned

    """

    if not isinstance(string, str):
        raise TypeError('string is type "{}", a string was expected'
                        ''.format(type(string)))

    data = {}  # type: Dict[str, List[Dict]]
    data = extruct.extract(string)
    scrapings = _convert_to_scrapings(data, nonstandard_attrs)

    if python_objects is True:
        scrapings = _pythonize_objects(scrapings)

    return scrapings


def scrape_url(url: str, python_objects: bool = False,
               nonstandard_attrs: bool = False, user_agent_str: str = None):
    """scrape from a URL

    Parameters
    ----------
    url : string
        A url to download data from and scrape.

    python_object : bool, optional
        when True it translates some data types into python objects
        dates into datetime.date, datetimes into datetime.datetimes,
        durations as dateime.timedelta.  (defaults to False)

    nonstandard_attrs : bool, optional
        when True it adds nonstandard (for schema.org/Recipe) attributes to the
        resulting dictionaries, that are outside the specification such as:
            '_format' is either 'json-ld' or 'microdata' (how schema.org/Recipe was encoded into HTML)
            '_source_url' is the source url, when 'url' has already been defined as another value
        (defaults to False)

    user_agent_str : string, optional
        overide the user_agent_string with this value.
        (defaults to None)

    Returns
    -------
    list
        a list of dictionaries in the style of schema.org/Recipe JSON-LD
        no results - an empty list will be returned


    """

    if not isinstance(url, str):
        raise TypeError('url is type "{}", a string was expected'
                        ''.format(type(url)))

    data = {}  # type: Dict[str, List[Dict]]
    if not user_agent_str:
        user_agent_str = USER_AGENT_STR

    r = requests.get(url, headers={'user_agent': user_agent_str})
    r.raise_for_status()
    data = extruct.extract(r.text, r.url)
    url = r.url

    scrapings = _convert_to_scrapings(data, nonstandard_attrs, url=url)

    if python_objects is True:
        scrapings = _pythonize_objects(scrapings)

    return scrapings


def _convert_to_scrapings(data: Dict[str, List[Dict]],
                          nonstandard_attrs: bool = False,
                          url: str = None) -> List[Dict]:
    out = []
    if data['json-ld'] != []:
        for rec in data['json-ld']:
            if rec['@type'] == 'Recipe':
                d = rec.copy()
                if nonstandard_attrs is True:
                    d['_format'] = 'json-ld'
                # store the url
                if url:
                    if d.get('url') and d.get('url') != url and \
                                            nonstandard_attrs is True:
                        d['_source_url'] = url
                    else:
                        d['url'] = url
                out.append(d)

    if data['microdata'] != []:
        for rec in data['microdata']:
            if rec['type'] == 'http://schema.org/Recipe':
                d = rec['properties'].copy()
                if nonstandard_attrs is True:
                    d['_format'] = 'microdata'
                # add @context and @type for conversion to the JSON-LD
                # style format
                d['@context'] = 'http://schema.org'
                d['@type'] = 'Recipe'

                # store the url
                if url:
                    if d.get('url') and nonstandard_attrs is True:
                        d['_source_url'] = url
                    else:
                        d['url'] = url
                out.append(d)

    return out


# properties that will be passed into datetime objects
DATETIME_PROPERTIES = frozenset(['dateCreated', 'dateModified',
                                 'datePublished', 'expires'])
DURATION_PROPERTIES = frozenset(['cookTime', 'performTime', 'prepTime',
                                 'totalTime', 'timeRequired'])


def _parse_determine_date_datetime(s: str) -> Union[datetime.datetime,
                                                    datetime.date]:
    """Parse function parses a date, if time is included it parses as a
    datetime.
    """
    if sys.version_info >= (3, 7):
        # Check if the date includes time.
        if 'T' in s:
            return datetime.datetime.fromisoformat(s)
        else:
            return datetime.date.fromisoformat(s)
    else:
        # Check if the date includes time.
        if 'T' in s:
            return isodate.parse_datetime(s)
        else:
            return isodate.parse_date(s)


def _pythonize_objects(scrapings: List[Dict]) -> List[Dict]:
    # convert ISO 8601 date times into timedelta
    scrapings = _convert_properties_scrape(scrapings, DURATION_PROPERTIES,
                                           isodate.parse_duration)

    # convert ISO 8601 date times into datetimes.datetime objects
    scrapings = _convert_properties_scrape(scrapings, DATETIME_PROPERTIES,
                                           _parse_determine_date_datetime)

    return scrapings


def _convert_properties_scrape(recipes: List[Dict], properties: frozenset,
                               function: Callable[[str], Union[datetime.datetime, datetime.date]]) -> List[Dict]:
    for i in range(len(recipes)):
        key_set = set(recipes[i].keys())
        for p in key_set.intersection(properties):
                try:
                    recipes[i][p] = function(recipes[i][p])
                except (isodate.ISO8601Error, ValueError):
                    # parse error, just leave the value as is
                    pass

    return recipes
