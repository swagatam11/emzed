# -*- coding: utf-8 -*-
"""
sphinxcontirb.pycon
~~~~~~~~~~~~~~~~~~~

derived from autorun

Run the code and insert stdout after the code block.


"""

import sys, cStringIO, traceback

from docutils import nodes
from sphinx.util.compat import Directive
from docutils.parsers.rst import directives
from sphinx.errors import SphinxError


class PyCon(SphinxError):
    category = 'pycon error'

class PyConConfig(object):
    config = dict()
    @classmethod
    def builder_init(cls,app):
        cls.config.update(app.builder.config.autorun_languages)


    
class PyCon(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'invisible': directives.flag,
        'suppress_output': directives.flag,
        'donotexec': directives.flag,
    }


    __globals = dict()


    def run(self):

        #config = PyConConfig.config
        #input_encoding = config.get('input_encoding','ascii')
        #output_encoding = config.get('output_encoding','ascii')


        suppress_output = "suppress_output" in self.options

        captured = cStringIO.StringIO()
        for line in self.content:
            fields = line.split("!noexec")
            donotexec = len(fields)>1
            if donotexec:
                del fields[1]
                line = "".join(fields)


            fields = line.split("!nooutput")
            donotoutput = len(fields)>1
            if donotoutput:
                del fields[1]
                line = "".join(fields)

            fields = line.split("!onlyoutput")
            onlyoutput = len(fields)>1
            if onlyoutput:
                del fields[1]
                line = "".join(fields)
            if not onlyoutput:
                print >> captured, ">>>", line

            if not suppress_output and not donotoutput:
                sys.stdout = captured
            if not donotexec:
                try:
                    exec(line, PyCon.__globals)
                except:
                    traceback.print_exc(file=captured)
            sys.stdout = sys.__stdout__

        out = captured.getvalue()# .decode(output_encoding)
        literal = nodes.literal_block(out,out)
        literal['language'] = "python"
        literal['linenos'] = 'linenos' in self.options
        if "invisible" in self.options:
            return []
        return [literal]


def setup(app):
    app.add_directive('pycon', PyCon)
    app.connect('builder-inited',PyConConfig.builder_init)
    app.add_config_value('autorun_languages', PyConConfig.config, 'env')

# vim: set expandtab shiftwidth=4 softtabstop=4 :
