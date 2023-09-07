#!/usr/bin/env python3

#
# Copyright 2019-2020 Micah Cochran
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
from pathlib import Path
from typing import List

from scrape_schema_recipe import load, loads, scrape, scrape_url, SSRTypeError
from scrape_schema_recipe import example_output, __version__

DISABLE_NETWORK_TESTS = False
DATA_PATH = "scrape_schema_recipe/test_data"


def lists_are_equal(lst1: List, lst2: List) -> bool:
    lst1.sort()
    lst2.sort()

    if lst1 != lst2:
        print("\n[lst1 != lst2]")
        print("lst1: {}".format(lst1))
        print("lst2: {}".format(lst2))
    return lst1 == lst2


class TestParsingFileMicroData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = load(f"{DATA_PATH}/foodista-british-treacle-tart.html")
        cls.recipe = cls.recipes[0]

    def test_recipe_keys(self):
        input_keys = list(self.recipe.keys())

        expected_output = [
            "@context",
            "recipeYield",
            "@type",
            "recipeInstructions",
            "recipeIngredient",
            "name",
        ]

        assert lists_are_equal(expected_output, input_keys)

    def test_name(self):
        assert self.recipe["name"] == "British Treacle Tart"

    def test_recipe_yield(self):
        assert self.recipe["recipeYield"] == "1 servings"

    def test_num_recipes(self):
        assert len(self.recipes) == 1


class TestUnsetTimeDate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = scrape(
            f"{DATA_PATH}/allrecipes-moscow-mule.html", python_objects=True
        )
        cls.recipe = cls.recipes[0]

    def test_recipe_keys(self):
        input_keys = list(self.recipe.keys())

        expected_output = [
            "@context",
            "@type",
            "aggregateRating",
            "author",
            "datePublished",
            "description",
            "image",
            "mainEntityOfPage",
            "name",
            "nutrition",
            "prepTime",
            "recipeCategory",
            "recipeIngredient",
            "recipeInstructions",
            "recipeYield",
            "review",
            "totalTime",
            "video",
        ]

        assert lists_are_equal(expected_output, input_keys)

    def test_name(self):
        assert self.recipe["name"] == "Simple Moscow Mule"

    def test_recipe_yield(self):
        assert self.recipe["recipeYield"] == "1 cocktail"

    def test_num_recipes(self):
        assert len(self.recipes) == 1

    def test_recipe_durations(self):
        assert str(self.recipe["prepTime"]) == "0:10:00"
        assert str(self.recipe["totalTime"]) == "0:10:00"
        assert "cookTime" not in self.recipe.keys()


# also uses the old ingredients name
class TestParsingFileMicroData2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = scrape(
            f"{DATA_PATH}/sweetestkitchen-truffles.html", python_objects=True
        )
        cls.recipe = cls.recipes[0]

    def test_recipe_keys(self):
        input_keys = list(self.recipe.keys())

        expected_output = [
            "prepTime",
            "cookTime",
            "name",
            "recipeYield",
            "recipeCategory",
            "image",
            "description",
            "@type",
            "author",
            "aggregateRating",
            "recipeIngredient",
            "recipeInstructions",
            "totalTime",
            "@context",
        ]

        assert lists_are_equal(expected_output, input_keys)

    def test_name(self):
        assert self.recipe["name"] == "Rum & Tonka Bean Dark Chocolate Truffles"

    def test_recipe_yield(self):
        assert self.recipe["recipeYield"] == "15-18 3cm squares"

    def test_num_recipes(self):
        assert len(self.recipes) == 1

    def test_totalTime_sum(self):
        r = self.recipe
        assert r["prepTime"] + r["cookTime"] == r["totalTime"]


class TestParsingFileLDJSON(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = scrape(f"{DATA_PATH}/bevvy-irish-coffee-2018.html")
        cls.recipe = cls.recipes[0]

    def test_category(self):
        assert self.recipe["recipeCategory"] == "Cocktail"

    def test_duration(self):
        assert self.recipe["totalTime"] == "PT5M"

    def test_ingredients(self):
        ingredients = [
            "1.5 oz Irish whiskey",
            "1 tsp brown sugar syrup",
            "Hot black coffee",
            "Unsweetened whipped cream",
        ]

        assert lists_are_equal(ingredients, self.recipe["recipeIngredient"])

    # in the 2019 version this was changed
    def test_instructions(self):
        expected_str = "Add Irish whiskey, brown sugar syrup, and hot coffee to an Irish coffee mug.\nTop with whipped cream."

        assert self.recipe["recipeInstructions"] == expected_str

    def test_recipe_keys(self):
        input_keys = list(self.recipe.keys())
        expected_output = [
            "author",
            "publisher",
            "recipeCategory",
            "@type",
            "recipeIngredient",
            "recipeInstructions",
            "image",
            "@context",
            "totalTime",
            "description",
            "name",
        ]

        assert lists_are_equal(expected_output, input_keys)

    def test_name(self):
        assert self.recipe["name"] == "Irish Coffee"

    def test_num_recipes(self):
        assert len(self.recipes) == 1


class TestTimeDelta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = scrape(
            f"{DATA_PATH}/crumb-lemon-tea-cakes-2018.html", python_objects=True
        )
        cls.recipe = cls.recipes[0]

    def test_timedelta(self):
        td = datetime.timedelta(minutes=10)
        assert self.recipe["prepTime"] == td

    def test_totalTime_sum(self):
        r = self.recipe
        assert r["prepTime"] + r["cookTime"] == r["totalTime"]


class TestDateTime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = load(
            f"{DATA_PATH}/google-recipe-example.html", python_objects=True
        )
        cls.recipe = cls.recipes[0]

        # input string (upload_date) is "2018-02-05T08:00:00+08:00"
        upload_date = cls.recipe["video"][0]["uploadDate"]
        cls.datetime_test = isodate.parse_datetime(upload_date)

    def test_publish_date_python_obj(self):
        assert self.recipe["datePublished"] == datetime.date(2018, 3, 10)

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
        with open(f"{DATA_PATH}/bevvy-irish-coffee-2019.html") as fp:
            s = fp.read()

        recipes = loads(s)
        recipe = recipes[0]
        assert recipe["name"] == "Irish Coffee"


# feed bad types into the functions
class BadTypes(unittest.TestCase):
    def test_load(self):
        with self.assertRaises(SSRTypeError):
            load(0xFEED)

    def test_loads(self):
        with self.assertRaises(SSRTypeError):
            loads(0xDEADBEEF)

    def test_scrape(self):
        with self.assertRaises(SSRTypeError):
            scrape(0xBEE)

    def test_scrape_url(self):
        with self.assertRaises(SSRTypeError):
            scrape_url(0xC0FFEE)


class TestURL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = "https://raw.githubusercontent.com/micahcochran/scrape-schema-recipe/master/scrape_schema_recipe/test_data/bevvy-irish-coffee-2018.html"

    @unittest.skipIf(DISABLE_NETWORK_TESTS is True, "network tests disabled")
    def test_scrape_url(self):
        self.recipes = scrape_url(self.url)
        self.recipe = self.recipes[0]
        assert self.recipe["name"] == "Irish Coffee"

    @unittest.skipIf(DISABLE_NETWORK_TESTS is True, "network tests disabled")
    def test_scrape(self):
        self.recipes = scrape(self.url)
        self.recipe = self.recipes[0]
        assert self.recipe["name"] == "Irish Coffee"


# test that the schema still works when not migrated
class TestUnMigratedSchema(unittest.TestCase):

    # Some of these examples use 'ingredients', which was superceded by
    # 'recipeIngredients' in the http://schema.org/Recipe standard for a list
    # of ingredients in a recipe.

    def test_recipe1(self):
        recipes = load(
            f"{DATA_PATH}/foodista-british-treacle-tart.html", migrate_old_schema=False
        )
        recipe = recipes[0]

        input_keys = list(recipe.keys())
        # Note: 'ingredients' has been superceded by 'recipeIngredients' in
        # the http://schema.org/Recipe standard for a list of ingredients.
        expected_output = [
            "@context",
            "recipeYield",
            "@type",
            "recipeInstructions",
            "ingredients",
            "name",
        ]

        assert lists_are_equal(expected_output, input_keys)

    def test_recipe2(self):
        recipes = scrape(
            f"{DATA_PATH}/sweetestkitchen-truffles.html",
            python_objects=True,
            migrate_old_schema=False,
        )
        recipe = recipes[0]

        input_keys = list(recipe.keys())

        expected_output = [
            "prepTime",
            "cookTime",
            "name",
            "recipeYield",
            "recipeCategory",
            "image",
            "description",
            "@type",
            "author",
            "aggregateRating",
            "ingredients",
            "recipeInstructions",
            "totalTime",
            "@context",
        ]

        assert lists_are_equal(expected_output, input_keys)


class TestExampleOutput(unittest.TestCase):
    def test_example_output(self):
        name = example_output("tea-cake")[0]["name"]
        assert name == "Meyer Lemon Poppyseed Tea Cakes"


class TestVersion(unittest.TestCase):
    def test_version_not_null(self):
        assert __version__ is not None

    def test_version_is_type_string(self):
        assert isinstance(__version__, str)


class TestPythonObjects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # these are named based on what is passed via python_objects
        cls.true = example_output("google", python_objects=True)[0]
        cls.false = example_output("google", python_objects=False)[0]
        cls.duration = example_output("google", python_objects=[datetime.timedelta])[0]
        cls.dates = example_output("google", python_objects=[datetime.date])[0]

    def testDurationTypes(self):
        assert isinstance(self.duration["cookTime"], datetime.timedelta)
        assert isinstance(self.duration["prepTime"], datetime.timedelta)
        assert isinstance(self.duration["totalTime"], datetime.timedelta)

    def testDurationEqual(self):
        assert self.duration["cookTime"] == self.true["cookTime"]
        assert self.duration["prepTime"] == self.true["prepTime"]
        assert self.duration["totalTime"] == self.true["totalTime"]

    def testDateTypes(self):
        assert isinstance(self.dates["datePublished"], datetime.date)
        # note that datePublished can also be of type datetime.dateime

    def testDatesEqual(self):
        assert self.dates["datePublished"] == self.true["datePublished"]


class TestGraph(unittest.TestCase):
    # tests @graph, also test Path
    def test_graph(self):
        recipes_old = load(
            f"{DATA_PATH}/crumb-lemon-tea-cakes-2018.html", python_objects=True
        )
        recipes_graph = load(
            Path(f"{DATA_PATH}/crumb-lemon-tea-cakes-2019.html"), python_objects=True
        )

        r_old = recipes_old[0]
        r_graph = recipes_graph[0]

        assert r_old["name"] == r_graph["name"]
        assert r_old["recipeCategory"] == r_graph["recipeCategory"]
        assert r_old["recipeCuisine"] == r_graph["recipeCuisine"]
        assert r_old["recipeIngredient"] == r_graph["recipeIngredient"]
        assert r_old["recipeYield"] == r_graph["recipeYield"]
        assert r_old["totalTime"] == r_graph["totalTime"]

        # ---- check differences ----
        # the recipeInstructions in 2019 version are HowToStep format, 2018 version are in a list
        assert r_old["recipeInstructions"] != r_graph["recipeInstructions"]

        # 2019 has a datePublished, 2018 version does not
        r_graph["datePublished"] == datetime.date(2018, 3, 19)
        assert "datePublished" not in r_old.keys()


class TestEscaping(unittest.TestCase):
    # make sure that the name contains & versus &amp; fixed in version 0.2.1
    def test_unescape_name_description(self):
        s = f"{DATA_PATH}/histfriendly-carrot-fennel-soup.html"
        recipes = load(s)
        recipe = recipes[0]

        assert "&amp;" not in recipe["name"]
        assert "&" in recipe["name"]
        assert "&amp;" not in recipe["description"]
        assert "&" in recipe["description"]

    # make sure that the name contains & versus &amp; fixed in version 0.2.1
    def test_unescape_ingredients(self):
        s = f"{DATA_PATH}/sally-coconut-cake.html"
        recipes = load(s)
        recipe = recipes[0]

        assert "&amp;" not in recipe["recipeIngredient"][0]
        assert "&" in recipe["recipeIngredient"][0]


if __name__ == "__main__":
    unittest.main()
