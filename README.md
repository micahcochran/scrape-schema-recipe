# scrape-schema-recipe

[![Build Status](https://travis-ci.org/micahcochran/scrape-schema-recipe.svg?branch=master)](https://travis-ci.org/micahcochran/scrape-schema-recipe)

Scrapes recipes from HTML https://schema.org/Recipe (Microdata/JSON-LD) into Python dictionaries.


## Install

```
pip install scrape-schema-recipe
```

## Requirements

Python version 3.5+

This library relies heavily upon [extruct](https://github.com/scrapinghub/extruct).

Other requirements: 
* isodate (>=0.5.1)
* requests
* validators (>=12.4).

## Online Example

```python
>>> import scrape_schema_recipe

>>> url = 'https://www.foodnetwork.com/recipes/alton-brown/honey-mustard-dressing-recipe-1939031'
>>> recipe_list = scrape_schema_recipe.scrape_url(url, python_objects=True)
>>> len(recipe_list)
1
>>> recipe = recipe_list[0]

# Name of the recipe
>>> recipe['name']
'Honey Mustard Dressing'

# List of the Ingredients
>>> recipe['recipeIngredient']
['5 tablespoons medium body honey (sourwood is nice)',
 '3 tablespoons smooth Dijon mustard',
 '2 tablespoons rice wine vinegar']

# List of the Instructions
>>> recipe['recipeInstructions']
['Combine all ingredients in a bowl and whisk until smooth. Serve as a dressing or a dip.']

# Author
>>> recipe['author']
[{'@type': 'Person',
  'name': 'Alton Brown',
  'url': 'https://www.foodnetwork.com/profiles/talent/alton-brown'}]
```
'@type': 'Person' is a [https://schema.org/Person](https://schema.org/Person) object


```python
# Preparation Time
>>> recipe['prepTime']
datetime.timedelta(0, 300)

# The library pendulum can give you something a little easier to read.
>>> import pendulum

# for pendulum version 1.0
>>> pendulum.Interval.instanceof(recipe['prepTime'])
<Interval [5 minutes]>

# for version 2.0 of pendulum
>>> pendulum.Duration(seconds=recipe['prepTime'].total_seconds())
<Duration [5 minutes]>
```

If `python_objects` is set to `False`, this would return the string ISO8611 representation of the duration, `'PT5M'`

[pendulum's library website](https://pendulum.eustace.io/).


```python
# Publication date
>>> recipe['datePublished']
datetime.datetime(2016, 11, 13, 21, 5, 50, 518000, tzinfo=<FixedOffset '-05:00'>)

>>> str(recipe['datePublished'])
'2016-11-13 21:05:50.518000-05:00'

# Identifying this is http://schema.org/Recipe data (in LD-JSON format)
 >>> recipe['@context'], recipe['@type']
('http://schema.org', 'Recipe')

# Content's URL
>>> recipe['url']
'https://www.foodnetwork.com/recipes/alton-brown/honey-mustard-dressing-recipe-1939031'

# all the keys in this dictionary
>>> recipe.keys()
dict_keys(['recipeYield', 'totalTime', 'dateModified', 'url', '@context', 'name', 'publisher', 'prepTime', 'datePublished', 'recipeIngredient', '@type', 'recipeInstructions', 'author', 'mainEntityOfPage', 'aggregateRating', 'recipeCategory', 'image', 'headline', 'review'])
```

## Example from a File (alternative representations)

Also works with locally saved [HTML example file](/test_data/google-recipe-example.html).
```python
>>> filelocation = 'test_data/google-recipe-example.html'
>>> recipe_list = scrape_schema_recipe.scrape(filelocation, python_objects=True)
>>> recipe = recipe_list[0]

>>> recipe['name']
'Party Coffee Cake'

>>> repcipe['datePublished']
datetime.date(2018, 3, 10)

# Recipe Instructions using the HowToStep
>>> recipe['recipeInstructions']
[{'@type': 'HowToStep',
  'text': 'Preheat the oven to 350 degrees F. Grease and flour a 9x9 inch pan.'},
 {'@type': 'HowToStep',
  'text': 'In a large bowl, combine flour, sugar, baking powder, and salt.'},
 {'@type': 'HowToStep', 'text': 'Mix in the butter, eggs, and milk.'},
 {'@type': 'HowToStep', 'text': 'Spread into the prepared pan.'},
 {'@type': 'HowToStep', 'text': 'Bake for 30 to 35 minutes, or until firm.'},
 {'@type': 'HowToStep', 'text': 'Allow to cool.'}]

```


## What Happens When Things Go Wrong

If there aren't any http://schema.org/Recipe formatted recipes on the site.
```python
>>> url = 'https://www.google.com'
>>> recipe_list = scrape_schema_recipe.scrape(url, python_objects=True)

>>> len(recipe_list)
0
```

Some websites will cause an `HTTPError`.

You may get around a 403 - Forbidden Errror by putting in an alternative user-agent
via the variable `user_agent_str`.


## Functions

* `load()` - load HTML schema.org/Recipe structured data from a file or file-like object
* `loads()` - loads HTML schema.org/Recipe structured data from a string
* `scrape_url()` - scrape a URL for HTML schema.org/Recipe structured data 
* `scrape()` - load HTML schema.org/Recipe structured data from a file, file-like object, string, or URL

```
    Parameters
    ----------
    location : string or file-like object
        A url, filename, or text_string of HTML, or a file-like object.

    python_objects : bool, list, or tuple  (optional)
        when True it translates certain data types into python objects
          dates into datetime.date, datetimes into datetime.datetimes,
          durations as dateime.timedelta.
        when set to a list or tuple only converts types specified to
          python objects:
            * when set to either [dateime.date] or [datetime.datetimes] either will
              convert dates.
            * when set to [datetime.timedelta] durations will be converted
        when False no conversion is performed
        (defaults to False)

    nonstandard_attrs : bool, optional
        when True it adds nonstandard (for schema.org/Recipe) attributes to the
        resulting dictionaries, that are outside the specification such as:
            '_format' is either 'json-ld' or 'microdata' (how schema.org/Recipe was encoded into HTML)
            '_source_url' is the source url, when 'url' has already been defined as another value
        (defaults to False)

    migrate_old_schema : bool, optional
        when True it migrates the schema from older version to current version
        (defaults to True)

    user_agent_str : string, optional  ***only for scrape_url() and scrape()***
        overide the user_agent_string with this value.
        (defaults to None)

    Returns
    -------
    list
        a list of dictionaries in the style of schema.org/Recipe JSON-LD
        no results - an empty list will be returned
```

These are also available with `help()` in the python console.

## Example function
The `example_output()` function gives quick access to data for prototyping and debugging.
It accepts the same parameters as load(), but the first parameter, `name`, is different.

```python
>>> from scrape_schema_recipes import example_names, example_output

>>> example_names
('irish-coffee', 'google', 'tart', 'tea-cake', 'truffles')

>>> recipes = example_output('truffles')
>>> recipes[0]['name']
'Rum & Tonka Bean Dark Chocolate Truffles'
```


## Files

License: Apache 2.0   see [LICENSE](LICENSE)

Test data attribution and licensing: [ATTRIBUTION.md](ATTRIBUTION.md)

## Development

Unit testing can be run by:
```
schema-recipe-scraper$ python3 test_scrape.py
```

mypy is used for static type checking

from the project directory:
```
 schema-recipe-scraper$ mypy schema_recipe_scraper/scrape.py
```

If you run mypy from another directory the `--ignore-missing-imports` flag will need to be added,
thus `$ mypy --ignore-missing-imports scrape.py`

`--ignore-missing-imports` flag is used because most libraries don't have static typing information contained
in their own code or typeshed.

## Reference Documentation
Here are some references for how schema.org/Recipe *should* be structured:

* [https://schema.org/Recipe](https://schema.org/Recipe) - official specification
* [Recipe Google Search Guide](https://developers.google.com/search/docs/data-types/recipe) - material teaching developers how to use the schema (with emphasis on how structured data impacts search results)


## Other Similar Python Libraries

* [recipe_scrapers](https://github.com/hhursev/recipe-scrapers) - library scrapes
recipes by using the HTML tags using BeautifulSoup.  It has drivers for each and every
supported website.  This is a great fallback for when schema-recipe-scraper will not
scrape a site.
