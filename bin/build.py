#!/bin/env python

import linter
from pathlib import Path
from copy import deepcopy

from lxml import etree
import lxml.html as lhtml
from lxml.html import builder as E

Path.__call__ = lambda self, *args: self.joinpath(*args)

def get(*args):
    L = args[-1]
    keys = args[:-1]
    get_lambda = lambda key: list(map(lambda l: l[key], L))
    if len(keys) == 0:
        key = L
        return lambda L: list(map(lambda l: l[key], L))
    if len(keys) == 1:
        key = keys[0]
        return get_lambda(key)
    else:
        return [get_lambda(key) for key in keys]


def Tag(tag_name, **kwargs):
    elem_base = etree.Element(tag_name, **kwargs)

    def tag(*args):
        elem = deepcopy(elem_base)
        for arg in args:
            if isinstance(arg, etree._Element):
                elem.append(arg)
            else:
                if len(elem) == 0:
                    elem.text = (elem.text or '') + str(arg)
                else:
                    elem[-1].tail = (elem[-1].tail or '') + str(arg)
        return elem

    return tag


Recipies = [{'data': recipie} for recipie in linter.recipies()]

build_dir = Path('build')
if not build_dir.exists():
    print(f'Creating Build Directory {build_dir}')
    build_dir.mkdir()
else:
    print('buid directory found')

index_page = build_dir('index.html')
recipies_directory = build_dir('recipies')
recipies_directory.mkdir(exist_ok=True)

html_template = E.HTML(
        E.HEAD(
            E.TITLE("Vibe.Cooking"),
            ),
        E.BODY(
            Tag('nav')(
                    E.H1(Tag('a', href="../index.html")(
                                 "Vibe.Cooking")),
                    E.P("A simple place for cimple recipies"),
                    ),
        ), lang='en')


def dump_to_file(file: Path,
                 doc: etree._Element):
    with open(file, 'w') as f:
        f.write(etree.tostring(doc,
                               doctype='<!DOCTYPE htlm>',
                               pretty_print=True,
                               encoding='utf-8').decode('utf-8'))


if __name__ == "__main__":
    for R in Recipies:
        data = R['data']
        file = recipies_directory(data.title).with_suffix('.html')
        R['html_file'] = file
        recipie_doc = deepcopy(html_template)
        recipie_doc.title = data.title
        recipie_doc.body.append(Tag('h-group')(Tag('h1')(data.title),
                                               Tag('p')(data.author or '')))
        recipie_doc.body.append(lhtml.fromstring(data.markdown))
        dump_to_file(file, recipie_doc)

    index_page_doc = deepcopy(html_template)
    index_page_doc.xpath('//nav/h1/a')[0].attrib['href']='index.html'
    index_page_doc.body.append(Tag('section')(
        E.H2('Tags'),
        *[Tag('details')(Tag('summary')(tag), Tag('ol')(
            *[Tag('li')(recipie.title)
              for recipie in recipies]))
          for tag, recipies in linter.tags(get('data', Recipies)).items()]
        ))

    index_page_doc.body.append(Tag('section')(
        E.H2('Authors'),
        *[Tag('details')(Tag('summary')(author)) for author in linter.authors]))

    index_page_doc.body.append(Tag('section')(
        E.H2('Recipies'),
        *[Tag('details')(Tag('summary')(Tag('a', href=str(file.relative_to(build_dir)))(recipie.title)))
          for recipie, file in zip(*get('data', 'html_file', Recipies))]))

    dump_to_file(index_page, index_page_doc)
