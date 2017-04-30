# -*- condig: utf-8 -*-
import os
import inspect
import gettext

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from sitic.config import config
from sitic.template import filters
from sitic.utils import constants
from sitic.logging import logger

GETTEXT_DOMAIN = 'sitic'

class Render(object):
    environment = None
    loader = None
    def __init__(self, language):
        self.loader = FileSystemLoader(config.templates_path)
        self.environment = Environment(loader=self.loader,
                                       extensions=['jinja2.ext.i18n'])

        translations = self.get_translations(language)
        self.environment.install_gettext_translations(translations, True)

        for name, function in inspect.getmembers(filters, predicate=inspect.isfunction):
            self.environment.filters[name] = function

    def render(self, content, output_path, context):
        template = self.get_content_template(content)
        if template:
            template.stream(**context).dump(output_path)

    def get_content_template(self, content):
        template = None
        possible_templates = content.get_templates()

        for template_name in possible_templates:
            template = self.get_template(template_name)
            if template:
                break;

        return template

    def get_template(self, template_name):
        try:
            template = self.environment.get_template(template_name)
        except TemplateNotFound as e:
            template = None
        return template

    def get_translations(self, language):
        locale_dir = config.locales_path
        language = 'en'
        if language == constants.DEFAULT_LANG:
            translations = gettext.NullTranslations()
        else:
            langs = [language]
            try:
                translations = gettext.translation(GETTEXT_DOMAIN, locale_dir, langs)
            except (IOError, OSError):
                logger.error((
                    "Cannot find translations for language '{}' in '{}'."
                    " Installing NullTranslations.").format(
                        language, locale_dir, GETTEXT_DOMAIN))
                translations = gettext.NullTranslations()
        return translations
