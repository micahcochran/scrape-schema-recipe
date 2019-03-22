#!/usr/bin/env python3

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


import datetime
import isodate
import unittest

from typing import List

from scrape_schema_recipe import load, loads, scrape, scrape_url
from scrape_schema_recipe import example_output, __version__


def lists_are_equal(lst1: List, lst2: List) -> bool:
    lst1.sort()
    lst2.sort()

    if lst1 != lst2:
        print('\n[lst1 != lst2]')
        print('lst1: {}'.format(lst1))
        print('lst2: {}'.format(lst2))
    return lst1 == lst2


class TestParsingFileMicroData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = load('test_data/foodista-british-treacle-tart.html')
        cls.recipe = cls.recipes[0]

    def test_recipe_keys(self):
        input_keys = list(self.recipe.keys())

        expectated_output = ['@context', 'recipeYield', '@type',
                             'recipeInstructions', 'recipeIngredient', 'name']

        assert lists_are_equal(expectated_output, input_keys)

    def test_name(self):
        assert self.recipe['name'] == 'British Treacle Tart'

    def test_recipe_yield(self):
        assert self.recipe['recipeYield'] == '1 servings'

    def test_num_recipes(self):
        assert len(self.recipes) == 1


# also uses the old ingredients name
class TestParsingFileMicroData2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = scrape('test_data/sweetestkitchen-truffles.html',
                             python_objects=True)
        cls.recipe = cls.recipes[0]

    def test_recipe_keys(self):
        input_keys = list(self.recipe.keys())

        expectated_output = ['prepTime', 'cookTime', 'name', 'recipeYield',
                             'recipeCategory', 'image', 'description', '@type',
                             'author', 'aggregateRating', 'recipeIngredient',
                             'recipeInstructions', 'totalTime', '@context']

        assert lists_are_equal(expectated_output, input_keys)

    def test_name(self):
        assert self.recipe['name'] \
            == 'Rum & Tonka Bean Dark Chocolate Truffles'

    def test_recipe_yield(self):
        assert self.recipe['recipeYield'] == '15-18 3cm squares'

    def test_num_recipes(self):
        assert len(self.recipes) == 1

    def test_totalTime_sum(self):
        r = self.recipe
        assert r['prepTime'] + r['cookTime'] == r['totalTime']


class TestParsingFileLDJSON(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = scrape('test_data/bevvy-irish-coffee.html')
        cls.recipe = cls.recipes[0]

    def test_category(self):
        assert self.recipe['recipeCategory'] == 'Cocktail'

    def test_duration(self):
        assert self.recipe['totalTime'] == 'PT5M'

    def test_ingredients(self):
        ingredients = ['1.5 oz Irish whiskey',
                       '1 tsp brown sugar syrup',
                       'Hot black coffee',
                       'Unsweetened whipped cream']

        assert lists_are_equal(ingredients, self.recipe['recipeIngredient'])

    def test_instructions(self):
        expected_str = 'Add Irish whiskey, brown sugar syrup, and hot coffee to an Irish coffee mug.\nTop with whipped cream.'

        assert self.recipe['recipeInstructions'] == expected_str

    def test_recipe_keys(self):
        input_keys = list(self.recipe.keys())
        expected_output = ['author', 'publisher', 'recipeCategory', '@type',
                           'recipeIngredient', 'recipeInstructions', 'image',
                           '@context', 'totalTime', 'description', 'name']

        assert lists_are_equal(expected_output, input_keys)

    def test_name(self):
        assert self.recipe['name'] == 'Irish Coffee'

    def test_num_recipes(self):
        assert len(self.recipes) == 1


class TestTimeDelta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = scrape(
                        'test_data/crumb-lemon-tea-cakes.html',
                        python_objects=True)
        cls.recipe = cls.recipes[0]

    def test_timedelta(self):
        td = datetime.timedelta(minutes=10)
        assert self.recipe['prepTime'] == td

    def test_totalTime_sum(self):
        r = self.recipe
        assert r['prepTime'] + r['cookTime'] == r['totalTime']


class TestDateTime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = load('test_data/google-recipe-example.html',
                           python_objects=True)
        cls.recipe = cls.recipes[0]

        # input string (upload_date) is "2018-02-05T08:00:00+08:00"
        upload_date = cls.recipe['video'][0]['uploadDate']
        cls.datetime_test = isodate.parse_datetime(upload_date)

    def test_publish_date_python_obj(self):
        assert self.recipe['datePublished'] == datetime.date(2018, 3, 10)

    def test_datetime_tz_python_obj_isodate(self):
        tz8 = isodate.FixedOffset(offset_hours=8)
        expected = datetime.datetime(2018, 2, 5, 8, 0, tzinfo=tz8)
        assert self.datetime_test == expected

    def test_datetime_tz_python_obj(self):
        tz8 = datetime.timezone(datetime.timedelta(hours=8))
        expected = datetime.datetime(2018, 2, 5, 8, 0, tzinfo=tz8)
        assert self.datetime_test == expected


# test loads()
class TestLoads(unittest.TestCase):
    def test_loads(self):
        with open('test_data/bevvy-irish-coffee.html') as fp:
            s = fp.read()

        self.recipes = loads(s)
        self.recipe = self.recipes[0]
        assert self.recipe['name'] == 'Irish Coffee'


# feed bad types into the fuctions
class BadTypes(unittest.TestCase):
    def test_load(self):
        with self.assertRaises(TypeError):
            load(0xFEED)

    def test_loads(self):
        with self.assertRaises(TypeError):
            loads(0xDEADBEEF)

    def test_scrape(self):
        with self.assertRaises(TypeError):
            scrape(0xBEE)

    def test_scrape_url(self):
        with self.assertRaises(TypeError):
            scrape_url(0xC0FFEE)


class TestURL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = 'https://raw.githubusercontent.com/micahcochran/scrape-schema-recipe/master/test_data/bevvy-irish-coffee.html'

    def test_scrape_url(self):
        self.recipes = scrape_url(self.url)
        self.recipe = self.recipes[0]
        assert self.recipe['name'] == 'Irish Coffee'

    def test_scrape(self):
        self.recipes = scrape(self.url)
        self.recipe = self.recipes[0]
        assert self.recipe['name'] == 'Irish Coffee'


# test that the schema still works unmigrated
class TestUnMigratedSchema(unittest.TestCase):

    # Some of these examples use 'ingredients', which was superceeded by
    # 'recipeIngredients' in the http://schema.org/Recipe standard for a list
    # of ingredients in a recipe.

    def test_recipe1(self):
        recipes = load('test_data/foodista-british-treacle-tart.html',
                       migrate_old_schema=False)
        recipe = recipes[0]

        input_keys = list(recipe.keys())
        # Note: 'ingredients' has been superceeded by 'recipeIngredients' in
        # the http://schema.org/Recipe standard for a list of ingredients.
        expectated_output = ['@context', 'recipeYield', '@type',
                             'recipeInstructions', 'ingredients', 'name']

        assert lists_are_equal(expectated_output, input_keys)

    def test_recipe2(self):
        recipes = scrape('test_data/sweetestkitchen-truffles.html',
                         python_objects=True, migrate_old_schema=False)
        recipe = recipes[0]

        input_keys = list(recipe.keys())

        expectated_output = ['prepTime', 'cookTime', 'name', 'recipeYield',
                             'recipeCategory', 'image', 'description', '@type',
                             'author', 'aggregateRating', 'ingredients',
                             'recipeInstructions', 'totalTime', '@context']

        assert lists_are_equal(expectated_output, input_keys)


class TestExampleOutput(unittest.TestCase):
    def test_example_output(self):
        name = example_output('tea-cake')[0]['name']
        assert name == 'Meyer Lemon Poppyseed Tea Cakes'


class TestVersion(unittest.TestCase):
    def test_version_not_null(self):
        assert __version__ is not None

    def test_version_is_type_string(self):
        assert isinstance(__version__, str)


if __name__ == '__main__':
    unittest.main()
