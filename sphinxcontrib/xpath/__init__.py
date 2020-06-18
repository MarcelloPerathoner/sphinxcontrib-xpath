"""
    sphinxcontrib.xpath
    ~~~~~~~~~~~~~~~~~~~

    Do Xpath queries on XML files and put the result into your docs.

    Example:  use phpdoc with --template=xml and then parse the file docstrings
    out of the generated structure.xml file.  But the docstrings must be in
    RST format.

    :copyright: Copyright 2019 by Marcello Perathoner <marcello@perathoner.de>
    :license: BSD, see LICENSE for details.
"""

import docutils
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList

import sphinx
from sphinx.util.docutils import SphinxDirective, switch_source_input
from sphinx.errors import SphinxWarning, SphinxError, ExtensionError

from lxml import etree

import pbr.version

if False:
    # For type annotations
    from typing import Any, Dict  # noqa
    from sphinx.application import Sphinx  # noqa

__version__ = pbr.version.VersionInfo ('xpath').version_string ()


def setup (app):
    # type: (Sphinx) -> Dict[unicode, Any]

    app.add_directive ('xpath', XPathDirective)

    app.add_config_value ('xpath_file', '', False)

    return {
        'version'            : __version__,
        'parallel_read_safe' : True,
    }


class XPathError (SphinxError):
    category = 'XPath error'


class XPathDirective (SphinxDirective):
    """Directive to display XPath query results. """

    required_arguments = 1 # the xpath query
    optional_arguments = 0
    has_content = False

    option_spec = {
        'file': directives.unchanged,  # file to work on, overrides config
    }

    def run (self):
        filename = self.options.get ('file') or getattr (self.env.config, 'xpath_file')
        if not (filename):
            raise XPathError (':file: directive required (or set xpath_file in conf.py).')

        parent = nodes.container ()
        parent.document = self.state.document

        try:
            tree = etree.parse (filename)
            self.state.document.settings.record_dependencies.add (filename)

            for n in tree.xpath (self.arguments[0]):
                text = etree.tostring (n, encoding = 'unicode', method = 'text')
                sourceline = n.sourceline or 0
                content = StringList ()
                for lineno, line in enumerate (text.splitlines ()):
                    content.append (line, '%s:%d:<xpath>' % (filename, sourceline + lineno))
                with switch_source_input (self.state, content):
                    self.state.nested_parse (content, 0, parent)

        except etree.LxmlError as exc:
            logger.error ('Error in "%s" directive: %s.' % (self.name, str (exc)))

        return parent.children
