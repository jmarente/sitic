# -*- condig: utf-8 -*-
import os
from datetime import datetime
from collections import defaultdict

from sitic.utils import boolean, get_valid_date
from sitic.config import config
from sitic.content.base_content import BaseContent

class BasePage(BaseContent):
    section = None
    frontmatter = {}
    draft = False
    publication_date = None
    expiration_date = None
    template_fields = ['template', 'type', 'section']

    def __init__(self, frontmatter, language = None, section = None):
        self.frontmatter = frontmatter or {}
        self.section = section

        self.language = language

        self.draft = boolean(self.frontmatter.pop('draft', None))
        self.taxonomies = defaultdict(list)

        date_fields = ['publication_date', 'expiration_date']
        self.modification_date = datetime.now()
        for field in date_fields:
            value = get_valid_date(self.frontmatter.pop(field, None), None)
            setattr(self, field, value)

        self.description = None

    def __getattr__(self, attribute):
        return self.frontmatter.get(attribute, None)

    def _get_url(self):
        raise NotImplementedError()

    def get_simple_context(self):
        if self.simple_context is None:
            self.simple_context = super(BasePage, self).get_simple_context()
            self.simple_context.update(dict(self.frontmatter))
            self.simple_context['modification_date'] = self.modification_date
            self.simple_context['publication_date'] = self.get_publication_date()
            self.simple_context['description'] = self.get_description()
            self.simple_context['taxonomies'] = self.format_taxonomies()
        return self.simple_context

    def get_context(self):
        if self.context is None:
            self.context = super(BasePage, self).get_context()
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
        plural_definition = taxonomy.definition.plural
        if taxonomy not in self.taxonomies[plural_definition]:
            self.taxonomies[plural_definition].append(taxonomy)
            if plural_definition in self.frontmatter:
                del self.frontmatter[taxonomy.definition.plural]

    def get_templates(self):
        raise NotImplementedError

    def get_publication_date(self):
        return self.publication_date if self.publication_date else datetime.now()

    @property
    def id(self):
        page_id = self.frontmatter.get('id', None)
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
        return self.frontmatter.get('title', None)

    def set_modification_date(self, date):
        if isinstance(date, int) or isinstance(date, float):
            date = datetime.fromtimestamp(int(date))
        self.modification_date = date

    def get_description(self):
        if not self.description:
            self.description = self.frontmatter.get('description', '')

        return self.description

    def format_taxonomies(self):
        formatted = {}
        for plural_definition in self.taxonomies:
            formatted[plural_definition] = [t.get_simple_context() for t in self.taxonomies[plural_definition]]

        return formatted
