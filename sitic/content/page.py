# -*- condig: utf-8 -*-
import os
from datetime import datetime

import markdown
from jinja2.utils import Markup

from sitic.utils import boolean, get_valid_date
from sitic.config import config
from sitic.content.base_content import BaseContent


class Page(BaseContent):
    section = None
    name = ""
    frontmatter = {}
    content = ""
    draft = False
    publication_date = None
    expiration_date = None
    template_fields = ['template', 'type', 'section', 'name']
    relative_path = []

    def __init__(self, frontmatter, content, name, relative_path = [], language = None, section = None):
        self.frontmatter = frontmatter or {}
        self.content = content or ""
        self.name = name
        self.section = section
        self.relative_path = relative_path

        self.language = language

        self.draft = boolean(self.frontmatter.pop('draft', None))
        self.taxonomies = []

        date_fields = ['publication_date', 'expiration_date']
        self.modification_date = datetime.now()
        for field in date_fields:
            value = get_valid_date(self.frontmatter.pop(field, None), None)
            setattr(self, field, value)

    def __getattr__(self, attribute):
        return self.frontmatter.get(attribute, None)

    def _get_url(self):
        alternative_url = self.relative_path + [self.name]
        url = self.frontmatter.get('url', None) or '/'.join(alternative_url)
        return url

    def get_simple_context(self):
        if self.simple_context is None:
            self.simple_context = super(Page, self).get_simple_context()
            self.simple_context.update(dict(self.frontmatter))
            self.simple_context['modification_date'] = self.modification_date
        return self.simple_context

    def get_context(self):
        if self.context is None:
            self.context = super(Page, self).get_context()
            self.context['content'] = Markup(markdown.markdown(self.content))
            self.context['raw_content'] = self.content
        return self.context

    def to_publish(self):
        to_publish = True
        now = datetime.now()

        if not config.build_draft and self.draft:
            to_publish = False
        elif not config.build_future \
                and self.publication_date  \
                and self.publication_date > now:
            to_publish = False
        elif self.is_expired():
            to_publish = False

        return to_publish

    def is_expired(self):
        now = datetime.now()
        return not config.build_expired \
                and self.expiration_date \
                and self.expiration_date <= now

    def add_taxonomy(self, taxonomy):
        if taxonomy not in self.taxonomies:
            self.taxonomies.append(taxonomy)
            if taxonomy.definition.plural in self.frontmatter:
                del self.frontmatter[taxonomy.definition.plural]

    def get_templates(self):
        templates = []
        page_type = self.frontmatter.get('type', None)
        template_name = self.frontmatter.get('template', None)

        if template_name:
            if page_type:
                templates.append('{}/{}.html'.format(page_type, template_name))
            templates.append('{}/{}.html'.format(self.section.name, template_name))

        if page_type:
            templates.append("{}/page.html".format(page_type))

        templates += [
            "{}/page.html".format(self.section.name),
            "default/page.html",
        ]

        return templates

    def get_publication_date(self):
        return self.publication_date if self.publication_date else datetime.now()

    @property
    def id(self):
        page_id = self.frontmatter.get('id', None)
        if not page_id:
            paths = self.relative_path + [self.name]
            page_id = '-'.join(paths)
        return page_id

    @property
    def weight(self):
        return self.frontmatter.get('weight', 0)

    def menus(self):
        menus = self.frontmatter.get('menus', None)
        if not menus:
            menus = []
        elif not isinstance(menus, list) and not isinstance(menus, dict):
            menus = [menus]
        elif isinstance(menus, dict):
            new_menu = {}
            for menu_name, data in menus.items():
                data = data[0] if isinstance(data, list) else data
                new_menu[menu_name] = data
            menus = new_menu
        return menus

    @property
    def title(self):
        return self.frontmatter.get('title', self.name)

    def set_modification_date(self, date):
        if isinstance(date, int) or isinstance(date, float):
            date = datetime.fromtimestamp(int(date))
        self.modification_date = date
