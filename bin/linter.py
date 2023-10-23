#!/bin/env python3
from pathlib import Path
import yaml
from collections import namedtuple as nt

recipies_directory = Path('recipes')
author_directories = Path('authors')
RECIPE_NAME = "recipe.md"

Recipie = nt('Recipie',
             ['file',
              'name',
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

        name=(MANDATORY,
              lambda name: isinstance(name, str),
              'Display name of the recipie'),

        author=(OPTIONAL,
                lambda author: (isinstance(author, str) and author in authors),
                'The Author of the recipie, must be in te authors directory'),

        date=(OPTIONAL,
              lambda date: isinstance(date, str),
              'Date when the thing recipie was written'),

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
                    lambda dif: (isinstance(int) and 0 <= dif <= 3),
                    'How difficulty is the recipie' +
                    '\n'.join(['0 = Trivial', '1 = Easy', '2 = Fuckupable', '3 = Hard to pull off']),
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


def Make_Recipie(**properties):
    fields = Recipie._fields
    args = dict()
    for field, type_info in zip(fields, Recipie_Type):
        mandatory, predicate, docstring = type_info
        if value := properties.get(field):
            if mandatory:
                raise Exception(f'field "{field}" is missing in {properties["file"]}, but that field is mandatory')
            else:
                args[field] = None
        else:
            if not predicate(value):
                raise Exception(f'Field "{field}" is invalid, its value is "{value}". Doc for Field is:\n' + docstring)
            else:
                args[field] = value

    for unknown in set(properties) - set(args):
        print(f'Warnning: Field "{unknown}" with value "{properties[unknown]}" is unknown, data is disgarded.')
    return Recipie(**args)


authors = [dict(
    name=author_file.name,
    file=author_file
    ) for author_file in author_directories.iterdir()]

recipies = [dict(
    id=recipe_file.name,
    file=recipe_file
    ) for recipe_file in recipies_directory.iterdir()]


def load_recipies(print=lambda *x, **y: None):
    for recipie in recipies:
        print(f'Loading File:"{recipie["id"]}"')
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
                markdown_string='---\n'.join(markdown),
                )


def process_yamls(recipies):
    for recipie in recipies:
        yield recipie | yaml.safe_load(recipie['yaml_string'])


def clean_data(recipies, print=lambda *x, **y: None):
    for recipie in recipies:
        if recipie.get('yaml_string'):
            print('removing yaml_string')
            recipie = deepcopy(recipie)


if __name__ == '__main__':
    data = list(process_yamls(load_recipies(print=print)))
