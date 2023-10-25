#!/bin/env python3
from pathlib import Path
from copy import deepcopy
import yaml
from collections import namedtuple as nt
import datetime

# To load the data, import linter.recipies, and linter.authors_data
# from linter import recipies
# for r in recipies():
#     print(r.title)
#     print(r.author)
#     print(r.ingredients)
#     print(30*'-')


recipies_directory = Path('recipes')
author_directories = Path('authors')
RECIPE_NAME = "recipe.md"

Recipie = nt('Recipie',
             ['file',
              'title',
              'author',
              'date',
              'time',
              'equptment',
              'ingredients',
              'difficulty',
              'tags',
              'markdown',
              ])
Recipie.api_version = "0.1"

MANDATORY, OPTIONAL = True, False
Recipie_Type = Recipie(
        file=(MANDATORY,
              lambda file: (isinstance(file, Path) and file.exists()),
              'The file containing the recipie'),

        title=(MANDATORY,
               lambda title: isinstance(title, str),
               'Display name of the recipie'),

        author=(OPTIONAL,
                lambda author: (isinstance(author, str) and author in authors),
                'The Author of the recipie, must be in te authors directory'),

        date=(OPTIONAL,
              lambda date: isinstance(date, datetime.datetime),
              'Date when the thing recipie was written, in a datetime.datetime legible format'),

        time=(OPTIONAL,
              lambda time: ((isinstance(time, int) or isinstance(time, float))
                            and time >= 0),
              'Time it takes to cook, positive intiger of float.'),

        equptment=(OPTIONAL,
                   lambda equip: (isinstance(equip, list)
                                  and all([isinstance(eq, str)
                                           for eq in equip])),
                   'Equiptment needed to make the dish'),

        ingredients=(OPTIONAL,
                     lambda ingr: (isinstance(ingr, list)
                                   and all([isinstance(ing, str)
                                            for ing in ingr])),
                     'Major neciserry ingredience needed to the dish'),

        difficulty=(OPTIONAL,
                    lambda dif: (isinstance(dif, int) and 0 <= dif <= 3),
                    'How difficulty is the recipie\n\t' +
                    '\n\t'.join(['0 = Trivial', '1 = Easy', '2 = Fuckupable', '3 = Hard to pull off']),
                    ),
        tags=(OPTIONAL,
              lambda tags: (isinstance(tags, list)
                            and all([isinstance(tag, str)
                                     for tag in tags])),
              'List of relevent tags'),

        markdown=(MANDATORY,
                  lambda md: isinstance(md, str),
                  '''The content of the notes in markdown format as string.
                  In future this should be returned as a parsed type.'''
                  ),

        )


def Make_Recipie(print=lambda *x, **y: None,
                 **properties):
    fields = Recipie._fields
    args = dict()
    for field, type_info in zip(fields, Recipie_Type):
        mandatory, predicate, docstring = type_info
        if (value := properties.get(field)) is not None:
            if predicate(value):
                args[field] = value
            else:
                raise Exception(f'Field "{field}" within file "{properties.get("file")}"is invalid, its value is {value.__repr__()}. Doc for Field is:\n' + docstring)
        else:
            if not mandatory:
                args[field] = None
            else:
                raise Exception(f'field "{field}" is missing in {properties["file"]}, but that field is mandatory')

    for unknown in (set(properties)
                    - {"yaml_string", "markdown_string"}
                    .union(set(args))):
        print(f'Warnning: Field "{unknown}" in "{properties["file"]}" with value "{properties[unknown]}" is unknown, data is disgarded.')
    return Recipie(**args)


authors_data = [dict(
    name=author_file.name,
    file=author_file
    ) for author_file in author_directories.iterdir()]

authors = [data['name'] for data in authors_data]


def load_recipies(*recipies_specific, print=lambda *x, **y: None,
                  recipies_directory=recipies_directory):

    if ((recipies_directory is not None)
            and (not recipies_directory.exists())):
        raise FileNotFoundError(f'Recipies Directory "{recipies_directory}" Does not exist.')

    for recipie in recipies_specific:
        if not recipie.exists():
            raise FileNotFoundError(f'Recipie Directory "{recipie}" Does not exist')

    recipies = [dict(
        file=recipe_file
        ) for recipe_file in [*(recipies_directory.iterdir()
                                if recipies_directory is not None else []),
                              *recipies_specific]]

    for recipie in recipies:
        print(f'Loading File:"{recipie["file"]}"')
        recipie_path = recipie['file'].joinpath(RECIPE_NAME)
        if not recipie_path.exists():
            raise Exception(f"{recipie_path} not found")

        with open(recipie_path, 'r') as f:
            raw_content = f.read()

        _, yaml_string, *markdown = raw_content.split('---\n')

        assert raw_content.split('\n')[0] == '---', f'Recipie file must start with "---", in file {recipie_path}'
        assert len(markdown) != 0, f'Recipie file must contain markdown, possibly mising end "---", in file {recipie_path}'

        yield recipie | dict(
                yaml_string=yaml_string,
                markdown='---\n'.join(markdown),
                file=recipie_path,
                )


def process_yamls(recipies, print=lambda *x, **y: None):
    for recipie in recipies:
        yield Make_Recipie(print=print,
                **(recipie | yaml.safe_load(recipie['yaml_string'])))


def clean_data(recipies, print=lambda *x, **y: None):
    for recipie in recipies:
            recipie = deepcopy(recipie)


recipies = lambda: process_yamls(load_recipies())


def tags(recipies):
    tags = dict()
    for recipie in recipies:
        if recipie.tags is not None:
            for tag in recipie.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(recipie)
    return tags


if __name__ == '__main__':
    import sys
    match len(sys.argv):
        case 1:
            author_directories = Path('authors')
        case 2:
            recipies_directory = Path(sys.argv[1])

    data = list(process_yamls(load_recipies(
            recipies_directory=recipies_directory,
            print=print), print=print))
